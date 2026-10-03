"""Public statistics -> CSV + .meta.json (provenance). Keyless first; keys never printed or passed to the model."""
import datetime as dt
import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from . import persona

TTL = 7 * 24 * 3600  # cached responses are reused for a week: respects provider rate limits
KEY_ENV = {"kosis": "KOSIS_API_KEY"}
OFFLINE = ("network unreachable ({err}). No key is needed for the fallback: download the table as CSV from the "
           "provider's web page and run `pptkit data <file>`")


# ---------- keys ----------

def _keyring():
    try:
        import keyring  # optional; Windows Credential Manager / macOS Keychain
        return keyring
    except ImportError:
        return None


def get_key(source):
    v = os.environ.get(KEY_ENV[source])
    if not v and _keyring():
        v = _keyring().get_password("pptkit", source)
    return v


def key_cmd(action, source=None):
    if action == "status":
        return "\n".join(f"{s}: {'connected' if get_key(s) else 'not set'} (env {e})" for s, e in KEY_ENV.items())
    if source not in KEY_ENV:
        raise SystemExit(f"source must be one of {', '.join(KEY_ENV)}")
    kr = _keyring()
    if action == "set":
        if not kr:
            return (f"keyring is not installed. Either `pip install keyring` and rerun, or set the environment variable "
                    f"{KEY_ENV[source]} yourself (Windows: setx {KEY_ENV[source]} <key>). Do not paste keys into chat.")
        import getpass
        kr.set_password("pptkit", source, getpass.getpass(f"{source} API key (hidden): "))
        return f"{source}: saved to the OS credential store"
    if action == "rm":
        if kr and kr.get_password("pptkit", source):
            kr.delete_password("pptkit", source)
        return f"{source}: removed from the credential store (unset {KEY_ENV[source]} yourself if you used it)"
    raise SystemExit("action: set | status | rm")


# ---------- http + cache ----------

def _get_json(url, cache_key, refresh=False):
    cache = persona.home() / "cache" / (hashlib.sha1(cache_key.encode()).hexdigest()[:16] + ".json")
    if cache.exists() and not refresh and time.time() - cache.stat().st_mtime < TTL:
        return json.loads(cache.read_text(encoding="utf-8")), True
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "pptkit"}), timeout=20) as r:
            body = json.loads(r.read().decode("utf-8"))
    except OSError as e:  # URLError, timeouts, proxy refusals
        raise SystemExit(OFFLINE.format(err=getattr(e, "reason", e)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return body, False


def _years(spec):
    a, _, b = str(spec).partition("-")
    return a, b or a


# ---------- adapters: url builder + parser (parsers are pure, tested with recorded responses) ----------

def wb_url(indicator, countries, years):
    a, b = _years(years)
    return (f"https://api.worldbank.org/v2/country/{';'.join(countries)}/indicator/{indicator}"
            f"?format=json&per_page=2000&date={a}:{b}")


def wb_parse(body):
    if not isinstance(body, list) or len(body) < 2 or body[1] is None:
        msg = body[0].get("message") if isinstance(body, list) and body and isinstance(body[0], dict) else body
        raise SystemExit(f"World Bank returned no data: {msg}")
    rows = [{"country": r["country"]["value"], "iso3": r.get("countryiso3code"), "year": int(r["date"]),
             "value": r["value"]} for r in body[1]]
    df = pd.DataFrame(rows).dropna(subset=["value"]).sort_values(["iso3", "year"])
    name = body[1][0]["indicator"]["value"]
    return df, {"provider": "World Bank WDI", "indicator": name}


def kosis_url(key, org, tbl, years, prd="Y", obj1="ALL", itm="ALL"):
    a, b = _years(years)
    q = {"method": "getList", "apiKey": key, "itmId": itm, "objL1": obj1, "format": "json", "jsonVD": "Y",
         "prdSe": prd, "startPrdDe": a, "endPrdDe": b, "orgId": org, "tblId": tbl}
    return "https://kosis.kr/openapi/Param/statisticsParameterData.do?" + urllib.parse.urlencode(q)


def kosis_parse(body):
    if isinstance(body, dict):  # KOSIS reports errors as {"err": "...", "errMsg": "..."}
        raise SystemExit(f"KOSIS error {body.get('err')}: {body.get('errMsg')}")
    df = pd.DataFrame(body)
    keep = [c for c in ("C1_NM", "C2_NM", "C3_NM", "ITM_NM", "PRD_DE", "DT", "UNIT_NM") if c in df.columns]
    df = df[keep].rename(columns={"C1_NM": "c1", "C2_NM": "c2", "C3_NM": "c3", "ITM_NM": "item", "PRD_DE": "period",
                                  "DT": "value", "UNIT_NM": "unit"})
    df["value"] = pd.to_numeric(df["value"].astype(str).str.replace(",", ""), errors="coerce")
    first = body[0] if body else {}
    return df, {"provider": "통계청 KOSIS", "indicator": first.get("TBL_NM", ""), "org": first.get("ORG_ID", "")}


def fetch(source, out_dir=".", refresh=False, **kw):
    out_dir = Path(out_dir)
    if source == "wb":
        url = wb_url(kw["indicator"], kw["countries"], kw["years"])
        body, cached = _get_json(url, url, refresh)
        df, meta = wb_parse(body)
        stem = f"wb_{kw['indicator']}"
    elif source == "kosis":
        key = get_key("kosis")
        if not key:
            raise SystemExit("KOSIS needs your own API key (free at kosis.kr/openapi). Run `pptkit key set kosis` in a "
                             "terminal yourself, or use the keyless fallback: download the table as CSV and `pptkit data`.")
        url = kosis_url(key, kw["org"], kw["tbl"], kw["years"], kw.get("prd", "Y"))
        body, cached = _get_json(url, url.replace(key, "KEY"), refresh)
        df, meta = kosis_parse(body)
        url = url.replace(key, "***")  # the key never reaches files or output
        stem = f"kosis_{kw['org']}_{kw['tbl']}"
    else:
        raise SystemExit("sources: wb (keyless), kosis (your key)")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = out_dir / f"{stem}.csv"
    df.to_csv(csv, index=False, encoding="utf-8-sig")
    meta.update({"url": url, "retrieved": dt.date.today().isoformat(), "rows": len(df)})
    meta["source"] = f"{meta['provider']} {meta['indicator']} ({meta['retrieved']} 수집)".replace("  ", " ")
    csv.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return f"OK {source}{' (cache)' if cached else ''}: {len(df)} rows -> {csv} (+.meta.json)\nsource: {meta['source']}"


def sources_report():
    return "\n".join([
        "wb     keyless  World Bank WDI (GDP, prices, jobs, trade...)  pptkit fetch wb <indicator> --country KOR,JPN --years 2021-2025",
        f"kosis  {'key ok ' if get_key('kosis') else 'no key '}  통계청 KOSIS 통계표               pptkit fetch kosis --org 101 --tbl <ID> --years 2020-2025",
        "file   keyless  any CSV/XLSX you downloaded (KOSIS, e-나라지표, 한국은행)  pptkit data <file>",
    ])
