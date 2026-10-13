"""Live numbers: `vars:` in deck.md front matter names a figure by how it is computed, text says `$name`.

A monthly deck then refreshes by swapping the data file and rebuilding: charts and the numbers in titles move
together, and `where: {month: latest}` follows the newest period. The model never types the figure itself.
"""
import json
import re
import shutil
from pathlib import Path


from . import data

REF = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*?)(\.abs)?(?![A-Za-z0-9_])(으로|로|을|를|이|가|은|는|과|와|이나|나)?")
DIGIT_FINAL = {"0": 21, "1": 8, "2": 0, "3": 16, "4": 0, "5": 0, "6": 1, "7": 8, "8": 8, "9": 0}  # 영 일 이 삼 ...
PAIRS = {"을": ("을", "를"), "를": ("을", "를"), "이": ("이", "가"), "가": ("이", "가"), "은": ("은", "는"),
         "는": ("은", "는"), "과": ("과", "와"), "와": ("과", "와"), "이나": ("이나", "나"), "나": ("이나", "나")}


def _final(text):
    """Final consonant index (0 = none, 8 = ㄹ) of how the value is read aloud: 억 원 -> ㄴ, 2.5% -> 퍼센트 (none)."""
    t = text.rstrip()
    if not t:
        return 0
    ch = t[-1]
    if "가" <= ch <= "힣":
        return (ord(ch) - 0xAC00) % 28
    if ch.isdigit():
        return DIGIT_FINAL[ch]
    return 0  # %, %p, letters: read without a final consonant (퍼센트, 포인트)


def josa(value, particle):
    if not particle:
        return ""
    f = _final(value)
    if particle in ("으로", "로"):
        return "로" if f in (0, 8) else "으로"
    with_, without = PAIRS[particle]
    return with_ if f else without


def _value(df, spec, where):
    d = data._filter(df, where)
    val, agg = spec["val"], spec.get("agg", "sum")
    if val not in d.columns:
        raise SystemExit(f"vars: unknown column '{val}'. columns: {', '.join(map(str, df.columns))}")
    if agg == "wmean":
        w = d[spec["weight"]]
        return float((d[val] * w).sum() / w.sum())
    return float(getattr(d[val], {"sum": "sum", "mean": "mean", "count": "count"}[agg])())


def compute(spec, base: Path, cache: dict):
    """One var. Kinds: plain value; per (ratio), minus, growth/diff between two periods, of (share %),
    or `col` + `at` for a period label itself (2026Q3)."""
    path = base / spec["data"]
    if path not in cache:
        cache[path] = data.load(path)
    df = cache[path]
    where = dict(spec.get("where") or {})
    if "col" in spec:  # the period label: `{data: x.csv, col: quarter, at: latest}` -> 2026Q3
        return str(data.period(df[spec["col"]], spec.get("at", "latest"))), "label"
    if "growth" in spec or "diff" in spec:
        (col, (a, b)), = (spec.get("growth") or spec.get("diff")).items()
        va, vb = (_value(df, spec, {**where, col: x}) for x in (a, b))
        return ((vb / va - 1) * 100, "pct") if "growth" in spec else (vb - va, "signed")
    v = _value(df, spec, where)
    if "per" in spec:
        v /= _value(df, {**spec, "val": spec["per"]}, where)
        return (v * 100, "pct") if spec.get("pct", True) else (v, "num")
    if "minus" in spec:
        return v - _value(df, {**spec, "val": spec["minus"]}, where), "signed"
    if "of" in spec:
        return v / _value(df, spec, spec["of"]) * 100, "pct"
    return v * (100 if spec.get("pct") else 1), "pct" if spec.get("pct") else "num"


def fmt(v, kind, spec):
    if kind == "label":
        return v
    if spec.get("fmt"):
        return format(v, spec["fmt"])
    sign = "+" if kind in ("signed",) or (kind == "pct" and ("growth" in spec or "diff" in spec)) else ""
    body = f"{v:{sign},.0f}" if kind != "pct" and float(round(v, 1)).is_integer() and abs(v) >= 100 \
        else f"{v:{sign},.1f}"  # rates always to one decimal (102.0%, 99.4%)
    return body + ("%" if kind == "pct" else "") + spec.get("unit", "")


def resolve(meta, base: Path):
    """{name: text} for every var in the front matter."""
    out, cache = {}, {}
    for name, spec in (meta.get("vars") or {}).items():
        v, kind = compute(spec, base, cache)
        out[name] = fmt(v, kind, spec)
    return out


def substitute(obj, values, missing):
    """$name -> value in every string of a slide spec (titles included). Unknown $names are collected."""
    if isinstance(obj, str):
        def rep(m):
            if m[1] not in values:
                missing.add(m[1])
                return m[0]
            v = values[m[1]].lstrip("+-") if m[2] else values[m[1]]  # $mom.abs: 감소 2.5% instead of 감소 -2.5%
            return v + josa(v, m[3])  # 166.3억 원을, 2.5%를: the particle follows the value
        return REF.sub(rep, obj)
    if isinstance(obj, list):
        return [substitute(x, values, missing) for x in obj]
    if isinstance(obj, dict):
        return {k: substitute(x, values, missing) for k, x in obj.items()}
    return obj


def changes(md_path: Path, values, slides, save=True):
    """Lines naming vars whose value moved since the last build, and the slides that quote them."""
    store = md_path.with_name(f".{md_path.stem}.vars.json")
    old = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    lines = []
    for k, v in values.items():
        if k in old and old[k] != v:
            used = [str(i) for i, s in enumerate(slides, 1) if re.search(rf"\${k}(?![A-Za-z0-9_])",
                                                                          json.dumps(s, ensure_ascii=False))]
            flip = old[k][:1] in "+-" and v[:1] in "+-" and old[k][:1] != v[:1]
            lines.append(f"VARS ${k} {old[k]} -> {v} (S{','.join(used) or '-'})"
                         + (" SIGN FLIPPED: 증가/감소 wording is now wrong" if flip else ""))
    if lines:
        lines.insert(0, "VARS changed since the last build: re-read the sentences on the slides listed")
    if lines:  # sentences without a $var did not move with the data: they are the likeliest to be wrong now
        static = [str(i) for i, s in enumerate(slides, 1) if s.get("pattern") not in ("cover", "section") and any(
            "$" not in json.dumps(s.get(k, ""), ensure_ascii=False) and s.get(k)
            for k in ("title", "takeaways", "callout", "bullets", "statement", "ask"))]
        if static:
            lines.append(f"VARS text without $vars on slides {','.join(static)} did not change with the data: "
                         "check each claim against `pptkit pivot`")
    if save and values:
        store.write_text(json.dumps(values, ensure_ascii=False, indent=0), encoding="utf-8")
    return lines


def backup(md_path: Path, meta, values, out: Path):
    """Before a rebuild moves the period label (2026-09 -> 2026-10), keep the old deck as deck.2026-09.pptx."""
    store = md_path.with_name(f".{md_path.stem}.vars.json")
    old = json.loads(store.read_text(encoding="utf-8")) if store.exists() else {}
    label = next((k for k, sp in (meta.get("vars") or {}).items() if "col" in sp), None)
    if not (label and out.exists() and old.get(label) and old[label] != values.get(label)):
        return None
    keep = out.with_name(f"{out.stem}.{re.sub(r'[^0-9A-Za-z가-힣_-]', '_', old[label])}.pptx")
    if not keep.exists():
        shutil.copy2(out, keep)
    return f"SAVED last period's deck -> {keep.name}"


def report(md_path):
    from .render import parse
    md_path = Path(md_path)
    meta, _ = parse(md_path.read_text(encoding="utf-8"))
    if not meta.get("vars"):
        return "no `vars:` in the front matter"
    return "\n".join(f"${k} = {v}" for k, v in resolve(meta, md_path.parent).items())

