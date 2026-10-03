"""Load tabular files, normalize KOSIS-style downloads, summarize, pivot. The model only sees summaries."""
import re
from pathlib import Path

import pandas as pd


def load(path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xls"):
        return _tidy(pd.read_excel(path, header=None))
    for enc in ("utf-8-sig", "cp949"):  # Korean Windows exports are often cp949
        try:
            return _tidy(pd.read_csv(path, header=None, encoding=enc, dtype=str))
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
        if pd.api.types.is_numeric_dtype(s):
            out.append(f"  {c} num {s.min():g}..{s.max():g} sum={s.sum():g}")
        else:
            top = s.value_counts().index[:6].tolist()
            out.append(f"  {c} cat {s.nunique()}: {','.join(map(str, top))}{' …' if s.nunique() > 6 else ''}")
    return "\n".join(out)


def aggregate(df, x, y, series=None, agg="sum", where=None):
    """Long data -> wide frame indexed by x, one column per series (or per y)."""
    for k, v in (where or {}).items():
        df = df[df[k].isin(v if isinstance(v, list) else [v])]
    ys = y if isinstance(y, list) else [y]
    if series:
        return df.pivot_table(index=x, columns=series, values=ys[0], aggfunc=agg).sort_index()
    return df.groupby(x)[ys].agg(agg).sort_index()


def pivot(df, rows, cols, val, agg="sum", top=None, where=None, total="합계", other="기타"):
    for k, v in (where or {}).items():
        df = df[df[k].isin(v if isinstance(v, list) else [v])]
    p = df.pivot_table(index=rows, columns=cols, values=val, aggfunc=agg)
    p = p.loc[p.sum(axis=1).sort_values(ascending=False).index]
    if agg != "sum":  # totals and an "other" row are only meaningful for sums
        return p.iloc[:top] if top else p
    if top and len(p) > top:
        rest = p.iloc[top:].sum().rename(other)
        p = pd.concat([p.iloc[:top], rest.to_frame().T])
    p[total] = p.sum(axis=1)
    p.loc[total] = p.sum()
    p.index.name, p.columns.name = rows, None
    return p
