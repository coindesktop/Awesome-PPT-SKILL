"""Live numbers: `vars:` in deck.md front matter names a figure by how it is computed, text says `$name`.

A monthly deck then refreshes by swapping the data file and rebuilding: charts and the numbers in titles move
together, and `where: {month: latest}` follows the newest period. The model never types the figure itself.
"""
import json
import re
from pathlib import Path


from . import data

REF = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


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
    body = f"{v:{sign},.0f}" if float(round(v, 1)).is_integer() and abs(v) >= 100 else f"{v:{sign},.1f}"
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
            if m[1] in values:
                return values[m[1]]
            missing.add(m[1])
            return m[0]
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
            used = [str(i) for i, s in enumerate(slides, 1) if f"${k}" in json.dumps(s, ensure_ascii=False)]
            flip = old[k][:1] in "+-" and v[:1] in "+-" and old[k][:1] != v[:1]
            lines.append(f"VARS ${k} {old[k]} -> {v} (slides {','.join(used) or '-'}): re-read those titles"
                         + ("; SIGN FLIPPED: 증가/감소 wording is now wrong" if flip else ""))
    if save and values:
        store.write_text(json.dumps(values, ensure_ascii=False, indent=0), encoding="utf-8")
    return lines


def report(md_path):
    from .render import parse
    md_path = Path(md_path)
    meta, _ = parse(md_path.read_text(encoding="utf-8"))
    if not meta.get("vars"):
        return "no `vars:` in the front matter"
    return "\n".join(f"${k} = {v}" for k, v in resolve(meta, md_path.parent).items())

