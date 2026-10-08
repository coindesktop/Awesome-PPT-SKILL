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


TIME = re.compile(r"^(19|20)\d{2}([-./]?(Q[1-4]|H[12]|\d{1,2}))?$|^(19|20)\d{2}년")


def is_time(values) -> bool:
    """Years, quarters (2026Q3), months (2026-01): keep chronological order instead of sorting by size."""
    vals = [str(v).strip() for v in values]
    return bool(vals) and all(TIME.match(v) for v in vals)


def pivot(df, rows, cols=None, val=None, agg="sum", top=None, where=None, total="합계", other="기타", weight=None,
          pct=None):
    """rows x cols table (cols optional). Time-like rows stay chronological; others sort by size.
    Totals are sums, or weighted means for wmean. pct: row | col (shares) | growth (vs previous period)."""
    df = _filter(df, where)
    keys = [rows, cols] if cols else [rows]
    if agg == "wmean":
        p = _wmean(df, keys, val, weight)
        p = p.unstack(cols) if cols else p.to_frame(val)
    elif cols:
        p = df.pivot_table(index=rows, columns=cols, values=val, aggfunc=agg)
    else:
        p = df.groupby(rows)[[val]].agg(agg)
    if cols and is_time(p.columns):
        p = p[sorted(p.columns, key=str)]
    timed = is_time(p.index)
    p = p.sort_index() if timed else p.loc[p.sum(axis=1).sort_values(ascending=False).index]
    if top and len(p) > top and agg == "sum":
        rest = p.iloc[top:].sum().rename(other)
        p = pd.concat([p.iloc[:top], rest.to_frame().T])
    elif top:
        p = p.iloc[:top]
    if pct in ("row", "col") and agg == "sum":
        p = p.div(p.sum(axis=1), axis=0) * 100 if pct == "row" else p.div(p.sum(axis=0), axis=1) * 100
    elif pct == "growth":
        p = (p.pct_change(axis=0 if timed or not cols or not is_time(p.columns) else 1) * 100)
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


def period_name(values):
    """CAGR is per year only for yearly data: months -> CMGR, quarters -> CQGR."""
    v = [str(x) for x in values if is_time([x])]
    if v and all(re.search(r"[-./]\d{1,2}$", x) for x in v):
        return "CMGR (월 복리)"
    if v and all("Q" in x for x in v):
        return "CQGR (분기 복리)"
    return "CAGR (연 복리)"


def cagr(p):
    """Compound annual growth of each column from the first to the last time-like row (None if not time-like)."""
    idx = [i for i in p.index if is_time([i])]
    if len(idx) < 2:
        cols = [c for c in p.columns if is_time([c])]
        return cagr(p[cols].T) if len(cols) >= 2 else None  # time across columns: one rate per row
    a, b = p.loc[idx[0]], p.loc[idx[-1]]
    return ((b / a) ** (1 / (len(idx) - 1)) - 1) * 100
