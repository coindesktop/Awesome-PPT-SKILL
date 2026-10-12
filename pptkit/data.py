"""Load tabular files, normalize KOSIS-style downloads, summarize, pivot. The model only sees summaries."""
import re
from pathlib import Path

import pandas as pd


def load(path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".zip":  # World Bank / OECD downloads: the data file, not the metadata files
        import tempfile
        import zipfile
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if n.lower().endswith((".csv", ".xlsx")) and "metadata" not in n.lower()]
            if not names:
                raise SystemExit(f"{path.name}: no data csv/xlsx inside")
            out = Path(tempfile.mkdtemp()) / Path(names[0]).name
            out.write_bytes(z.read(names[0]))
        return load(out)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return _tidy(pd.read_excel(path, header=None))
    for enc in ("utf-8-sig", "cp949"):  # Korean Windows exports are often cp949
        try:
            head = path.read_text(encoding=enc)[:200]
            skip = 4 if head.lstrip('"').startswith("Data Source") else 0  # World Bank web download: 4 meta lines
            raw = pd.read_csv(path, header=None, encoding=enc, dtype=str, skiprows=skip)
            return _tidy(raw.dropna(axis=1, how="all"))
        except UnicodeDecodeError:
            continue
    raise ValueError(f"cannot decode {path}")


def _tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Header rows -> columns. KOSIS repeats id headers on row 2 and puts years across columns."""
    head = raw.iloc[0].astype(str).tolist()
    second = raw.iloc[1].astype(str).tolist() if len(raw) > 1 else []
    years = [c for c in head if re.fullmatch(r"\d{4}(\.\d{1,2})?", c.strip())]
    kosis = second and second[0] == head[0] and len(years) >= 2
    df = raw.iloc[2 if kosis else 1:].reset_index(drop=True)
    df.columns = [c.strip() for c in head]
    if years:  # wide years -> long
        ids = [c for c in df.columns if c not in years]
        value_name = re.sub(r"\s*\(.*\)", "", second[len(ids)]).strip() if kosis else "value"
        df = df.melt(id_vars=ids, value_vars=years, var_name="year", value_name=value_name or "value")
    for c in df.columns:
        num = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
        if num.notna().all():
            df[c] = num
    return df


def summary(path) -> str:
    df = load(path)
    out = [f"{Path(path).name}: {len(df)} rows x {len(df.columns)} cols"]
    for c in df.columns:
        s = df[c]
        year_like = pd.api.types.is_numeric_dtype(s) and (s.dropna() % 1 == 0).all() and is_time(s.dropna().unique())
        if pd.api.types.is_numeric_dtype(s) and not year_like:
            out.append(f"  {c} num {s.min():g}..{s.max():g} sum={s.sum():g}")
        elif is_time(s.dropna().unique()):
            u = sorted(map(str, s.dropna().unique()))
            out.append(f"  {c} time {len(u)}: {u[0]}..{u[-1]}" + (f" (latest: {','.join(u[-3:])})" if len(u) > 3 else ""))
        else:
            top = s.value_counts().index[:6].tolist()
            out.append(f"  {c} cat {s.nunique()}: {','.join(map(str, top))}{' …' if s.nunique() > 6 else ''}")
    return "\n".join(out)


def coerce(col, v):
    """CLI values are strings; match the column's type (years are numbers)."""
    return pd.to_numeric(v) if pd.api.types.is_numeric_dtype(col) else v


def _filter(df, where):
    for k, v in (where or {}).items():
        df = df[df[k].isin(v if isinstance(v, list) else [v])]
    return df


def _wmean(df, keys, val, weight):
    """Weighted mean of val by weight within groups (e.g. revenue-weighted margin)."""
    g = df.assign(_vw=df[val] * df[weight]).groupby(keys)[["_vw", weight]].sum()
    return g["_vw"] / g[weight]


def aggregate(df, x, y, series=None, agg="sum", where=None, weight=None):
    """Long data -> wide frame indexed by x, one column per series (or per y). agg=wmean needs weight."""
    df = _filter(df, where)
    ys = y if isinstance(y, list) else [y]
    if agg == "wmean":
        if series:
            return _wmean(df, [x, series], ys[0], weight).unstack(series).sort_index()
        return pd.concat({c: _wmean(df, x, c, weight) for c in ys}, axis=1).sort_index()
    if series:
        return df.pivot_table(index=x, columns=series, values=ys[0], aggfunc=agg).sort_index()
    return df.groupby(x)[ys].agg(agg).sort_index()


TIME = re.compile(r"^(19|20)\d{2}([-./]?(Q[1-4]|H[12]|\d{1,2}))?$|^(19|20)\d{2}년|^Q[1-4]$|^H[12]$|^[1-4]분기$"
                  r"|^[상하]반기$|^\d{1,2}월$|^(\d{4}-)?\d{1,2}-\d주(차)?$|^W\d{1,2}$")


def is_time(values) -> bool:
    """Years, quarters (2026Q3, Q3, 3분기), halves, months (2026-01, 3월): chronological, never sorted by size."""
    vals = [str(v).strip() for v in values]
    return bool(vals) and all(TIME.match(v) for v in vals)


def time_pos(v):
    """(unit, position) so steps can be counted: M = months, Q = quarters, H = halves, Y = years."""
    v = str(v).strip()
    y = re.match(r"(19|20)\d{2}", v)
    year = int(y.group()) if y else 0
    w = re.search(r"(\d{1,2})-(\d)주|^W(\d{1,2})$", v)
    if w:  # 09-1주 = September week 1; W37 = ISO-like week number
        return "W", (year * 60 + int(w.group(1)) * 5 + int(w.group(2))) if w.group(1) else int(w.group(3))
    for pat, unit, mult in ((r"Q([1-4])|([1-4])분기", "Q", 4), (r"H([12])", "H", 2), (r"[-./](\d{1,2})$|^(\d{1,2})월$", "M", 12)):
        m = re.search(pat, v)
        if m:
            return unit, year * mult + int(next(g for g in m.groups() if g))
    if v in ("상반기", "하반기"):
        return "H", year * 2 + (1 if v == "상반기" else 2)
    return "Y", year


def _order(p, timed, keep_file_order, first_seen):
    if timed:
        return p.loc[sorted(p.index, key=lambda i: time_pos(i))]
    if keep_file_order:  # growth/diff on categories (도입 전 → 도입 후) follow the file, not the size
        return p.loc[[i for i in first_seen if i in p.index]]
    return p.loc[p.sum(axis=1).sort_values(ascending=False).index]


def apply_pct(p, pct, timed, cols_timed=False):
    """row | col shares, growth (% vs previous), diff (change vs previous). Along time columns when rows are not time."""
    axis = 1 if (cols_timed and not timed) else 0
    if pct == "row":
        return p.div(p.sum(axis=1), axis=0) * 100
    if pct == "col":
        return p.div(p.sum(axis=0), axis=1) * 100
    if pct == "diff":
        return p.diff(axis=axis)
    if pct == "growth":
        return p.pct_change(axis=axis) * 100
    return p


def pivot(df, rows, cols=None, val=None, agg="sum", top=None, where=None, total="합계", other="기타", weight=None,
          pct=None):
    """rows x cols table (cols optional). Time-like rows stay chronological; others sort by size (file order for
    growth/diff). Totals are sums, or weighted means for wmean. pct: row | col | growth | diff."""
    df = _filter(df, where)
    first_seen = list(dict.fromkeys(df[rows]))
    keys = [rows, cols] if cols else [rows]
    if agg == "wmean":
        p = _wmean(df, keys, val, weight)
        p = p.unstack(cols) if cols else p.to_frame(val)
    elif cols:
        p = df.pivot_table(index=rows, columns=cols, values=val, aggfunc=agg)
    else:
        p = df.groupby(rows)[[val]].agg(agg)
    cols_timed = bool(cols) and is_time(p.columns)
    if cols_timed:
        p = p[sorted(p.columns, key=time_pos)]
    elif cols:  # category columns (근속 1년 미만, 1~3년 ...) keep the file's order, not alphabetical
        p = p[[c for c in dict.fromkeys(df[cols]) if c in p.columns]]
    timed = is_time(p.index)
    p = _order(p, timed, pct in ("growth", "diff"), first_seen)
    if top and len(p) > top and agg == "sum":
        rest = p.iloc[top:].sum().rename(other)
        p = pd.concat([p.iloc[:top], rest.to_frame().T])
    elif top:
        p = p.iloc[:top]
    if pct in ("row", "col") and agg != "sum":
        pct = None  # shares of averages mean nothing
    if pct:
        p = apply_pct(p, pct, timed, cols_timed)
    elif agg == "sum" and cols:
        p[total] = p.sum(axis=1)
        p.loc[total] = p.sum()
    elif agg == "wmean":
        if cols:
            p[total] = _wmean(df, [rows], val, weight)
            p.loc[total] = list(_wmean(df, [cols], val, weight).reindex(p.columns[:-1])) + \
                [(df[val] * df[weight]).sum() / df[weight].sum()]
        else:
            p.loc[total] = (df[val] * df[weight]).sum() / df[weight].sum()
    elif agg == "sum":
        p.loc[total] = p.sum()
    p.index.name, p.columns.name = rows, None
    return p


def bridge(p, start, end, top=6, other="기타"):
    """Waterfall input from a rows x periods pivot: start total, the per-row changes (largest first, the tail
    summed into one "기타 n개" bar), end total. Returns ([(label, value)], total change)."""
    cols = {str(c): c for c in p.columns if c != "합계"}
    if str(start) not in cols or str(end) not in cols:
        raise KeyError(f"--bridge takes two of: {', '.join(cols)}")
    a, b = cols[str(start)], cols[str(end)]
    d = (p[b].fillna(0) - p[a].fillna(0)).drop(index="합계", errors="ignore")
    d = d.reindex(d.abs().sort_values(ascending=False).index)
    items = [(str(k), float(v)) for k, v in d.iloc[:top].items()]
    if len(d) > top:
        items.append((f"{other} {len(d) - top}개", float(d.iloc[top:].sum())))
    tot_a = float(p[a].drop(index="합계", errors="ignore").sum())
    return [(f"{a}", tot_a)] + items + [(f"{b}", "=")], float(d.sum())


RATE = {"W": "주 복리 성장률", "M": "CMGR (월 복리)", "Q": "CQGR (분기 복리)", "H": "반기 복리 성장률", "Y": "CAGR (연 복리)"}


def growth_summary(p):
    """(label, compound rate per period unit, first→last multiple) between the first and last time points.
    Steps are counted from the labels, so 2024-12 → 2025-06 is 6 months, not one step. None if not time-like."""
    idx = [i for i in p.index if is_time([i])]
    if len(idx) < 2:
        cols = [c for c in p.columns if is_time([c])]
        return growth_summary(p[cols].T) if len(cols) >= 2 else None  # time across columns: one rate per row
    (ua, a_pos), (ub, b_pos) = time_pos(idx[0]), time_pos(idx[-1])
    steps = b_pos - a_pos if ua == ub and b_pos > a_pos else len(idx) - 1
    a, b = p.loc[idx[0]].astype(float), p.loc[idx[-1]].astype(float)
    ok = (a > 0) & (b >= 0)
    mult = (b / a).where(ok)
    rate = ((mult ** (1 / steps)) - 1) * 100
    return RATE[ua], rate, mult


def cagr(p):
    """Compound growth per period from the first to the last time point (kept for callers that need only the rate)."""
    g = growth_summary(p)
    return None if g is None else g[1]


def period_name(values):
    v = [x for x in values if is_time([x])]
    return RATE[time_pos(v[0])[0]] if v else RATE["Y"]


def smart_round(p, pct=False):
    """Keep significant digits: shares and growth at 0.1, small ratios (0.02) at 4 places."""
    if pct:
        return p.round(1)
    m = p.abs().max().max() if p.size else 0
    if pd.isna(m) or m >= 100:
        return p.round(1)
    return p.round(2 if m >= 1 else 4)
