"""Everyday office slides: a free-form table (markdown or a data file, merged cells) and an image with text.
Registered on import."""
import math
import re
from pathlib import Path

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from . import data
from .render import (INFER, KEYS, PATTERNS, _border, _callout, _label, _s, box, content_slide, mix, picture,
                     plain_table, rgb, text, text_width)

SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
NUM = re.compile(r"^[+\-−▲▼△▽]?\s*[\d,]+(\.\d+)?\s*(%p|%|억 원|만 원|억|만|원|건|명|배|개|곳|천|조|점|시간|일|개월|년)?$")
UP, DOWN = re.compile(r"^[+▲△]\s*\d"), re.compile(r"^[-−▼▽]\s*\d")


def _cells(line):
    line = line.strip()
    line = line[1:] if line.startswith("|") else line
    line = line[:-1] if line.endswith("|") else line
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line)]


def _read(ctx, spec):
    """-> (header rows, body rows, per-column alignment or None). Sources: a markdown table, {columns, rows},
    or a data file (`data:` + optional `columns`, `where`, `max_rows`)."""
    t = spec.get("table")
    align = None
    if isinstance(t, str):
        lines = [ln for ln in t.splitlines() if "|" in ln]
        sep = next((i for i, ln in enumerate(lines) if SEP.match(ln)), None)
        head = [_cells(ln) for ln in (lines[:sep] if sep else lines[:1])]
        body = [_cells(ln) for ln in lines[(sep + 1 if sep else 1):]]
        if sep:
            marks = _cells(lines[sep])
            align = ["center" if m.startswith(":") and m.endswith(":") else "right" if m.endswith(":")
                     else "left" if m.startswith(":") else None for m in marks]
    elif isinstance(t, dict):
        head = [[_s(c) for c in t.get("columns", [])]]
        body = [[_s(c) for c in r] for r in t.get("rows", [])]
    elif spec.get("data"):
        df = data._filter(data.load(ctx.base / spec["data"]), spec.get("where"))
        cols = spec.get("columns") or list(df.columns)
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise SystemExit(f"table: unknown column(s) {missing}. columns: {', '.join(map(str, df.columns))}")
        df = df[cols].head(int(spec.get("max_rows", 12)))
        head = [[_label(ctx, spec, c) for c in cols]]
        dec = {c: df[c].dtype.kind == "f" and not (df[c].dropna() % 1 == 0).all() for c in cols}  # 105.0 beside 107.9
        body = [[(f"{v:,.1f}" if dec[c] and isinstance(v, float) and not math.isnan(v) else _num(v))
                 for c, v in zip(cols, r)] for r in df.itertuples(index=False)]
    else:
        raise SystemExit(f"table on '{spec['title']}': give `table:` (markdown or columns/rows) or `data:`")
    n = max(len(r) for r in head + body) if head + body else 0
    pad = lambda r: r + [""] * (n - len(r))
    return [pad(r) for r in head], [pad(r) for r in body], align


def _num(v):
    if isinstance(v, bool) or v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    if isinstance(v, (int, float)):
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    return str(v)


def _spans(grid):
    """`<` joins a cell to the one on its left, `^` to the one above. -> {(r, c): (rowspan, colspan)}, skipped set."""
    spans, skip = {}, set()
    nr, nc = len(grid), len(grid[0]) if grid else 0
    for r in range(nr):
        for c in range(nc):
            if grid[r][c] in ("<", "^") or (r, c) in skip:
                continue
            cs = 1
            while c + cs < nc and grid[r][c + cs] == "<":
                cs += 1
            rs = 1
            while r + rs < nr and all(grid[r + rs][c + k] == "^" or (k and grid[r + rs][c + k] == "<") for k in range(cs)):
                rs += 1
            if rs > 1 or cs > 1:
                spans[(r, c)] = (rs, cs)
                skip |= {(r + i, c + j) for i in range(rs) for j in range(cs)} - {(r, c)}
    return spans, skip


def p_table(ctx, spec):
    """A table as typed: header row(s), body rows, merged cells, a bold total row, signed figures coloured."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    head, body, align = _read(ctx, spec)
    grid = head + body
    nr, nc, nh = len(grid), len(grid[0]), len(head)
    side = spec.get("takeaways") or spec.get("callout")
    tw = w * 0.64 if side else w
    note_h = 0.35 if spec.get("note") else 0
    plain = [[re.sub(r"^\*\*(.*)\*\*$", r"\1", v) for v in r] for r in grid]
    numeric = [sum(bool(NUM.match(v)) for v in col[nh:] if v not in ("", "<", "^", "-")) >=
               0.7 * max(1, sum(v not in ("", "<", "^", "-") for v in col[nh:])) for col in zip(*plain)]
    al = spec.get("align") or align or [None] * nc
    al = [{"l": "left", "r": "right", "c": "center"}.get(str(a)[:1].lower()) if a else None for a in (
        list(al) if not isinstance(al, str) else list(al))] + [None] * nc
    al = [al[j] or ("right" if numeric[j] and j else "left") for j in range(nc)]
    if not spec.get("widths") and not side:  # a few short columns: a narrower table reads better than a stretched one
        need = sum(max(text_width(r[j], 14) for r in plain if r[j] not in ("<", "^")) + 0.26 for j in range(nc))
        tw = min(tw, max(need * 1.7, w * 0.5))
    pt = 14
    while True:  # largest type at which every row fits the body height
        pad = 0.26
        nat = [max(text_width(r[j], pt) for r in plain if r[j] not in ("<", "^")) + pad for j in range(nc)]
        rel = spec.get("widths")
        widths = [tw * float(v) / sum(map(float, rel)) for v in rel] if rel and len(rel) == nc else None
        if not widths:
            extra = tw - sum(nat)
            widths = [n_ + extra / nc for n_ in nat] if extra >= 0 else [tw * n_ / sum(nat) for n_ in nat]
        line_h = pt / 72 * 1.3
        row_h = [max(0.3, 0.14 + line_h * max(math.ceil(text_width(v, pt) / max(widths[j] - pad + 0.02, 0.3))
                                               for j, v in enumerate(r) if v not in ("<", "^"))) for r in plain]
        base = min(0.56, (h - note_h) / nr)
        row_h = [max(rh, base if pt >= 12 else rh) for rh in row_h]
        if sum(row_h) <= h - note_h + 0.02 or pt <= 9:
            break
        pt -= 1
    if sum(row_h) > h - note_h + 0.05:
        ctx.warn(f"table: {nr} rows x {nc} cols do not fit even at 9pt; split it over two slides or shorten cells")
    gf = plain_table(slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(tw), Inches(sum(row_h))))
    tb = gf.table
    ctx.tables += 1
    for j, cw in enumerate(widths):
        tb.columns[j].width = Inches(cw)
    for i, rh in enumerate(row_h):
        tb.rows[i].height = Inches(rh)
    style = "dark" if ctx.tone["name"] == "public" else ctx.st["table_head"]
    head_fill, head_fg = {"dark": (c["dark"], "FFFFFF"), "accent": (c["accent"], "FFFFFF"),
                          "plain": (c["surface"], c["ink"])}.get(style, (c["card"], c["ink"]))
    total = spec.get("total")
    total_rows = {nr - 1} if total in (True, "last") else {nh + int(t) - 1 for t in (total if isinstance(total, list) else [])}
    hl = {str(v) for v in (spec.get("highlight") if isinstance(spec.get("highlight"), list) else [spec.get("highlight")])
          if v is not None}
    spans, skip = _spans(grid)
    for i, row in enumerate(grid):
        is_head, is_total = i < nh, i in total_rows
        zebra = style != "card" and not is_head and (i - nh) % 2 == 1
        fill = head_fill if is_head else c["card"] if is_total else mix(c["surface"], c["card"], 0.55) if zebra else c["surface"]
        if not is_head and plain[i][0] in hl:
            fill = mix(c["surface"], c["accent"], 0.1)
        for j, raw in enumerate(row):
            ce = tb.cell(i, j)
            ce.fill.solid()
            ce.fill.fore_color.rgb = rgb(fill)
            ce.vertical_anchor = MSO_ANCHOR.MIDDLE
            ce.margin_left = ce.margin_right = Inches(0.11)
            ce.margin_top = ce.margin_bottom = Inches(0.03)
            _border(ce, "B", (head_fill if style in ("dark", "accent") else c["ink"]) if i == nh - 1 else c["line"],
                    1.25 if i == nh - 1 else 0.75)
            if is_total:
                _border(ce, "T", c["ink"], 1)
            if (i, j) in skip or raw in ("<", "^"):
                continue
            v = plain[i][j]
            bold = is_head or is_total or raw.startswith("**") or (j == 0 and nc > 2)
            color = head_fg if is_head else c["ink"] if bold else c["body"]
            if not is_head and spec.get("signed", True) and numeric[j]:
                color = c["positive"] if UP.match(v) else c["negative"] if DOWN.match(v) else color
            para = ce.text_frame.paragraphs[0]
            merged = (i, j) in spans
            para.alignment = {"left": PP_ALIGN.LEFT, "right": PP_ALIGN.RIGHT, "center": PP_ALIGN.CENTER}[
                "center" if merged and spans[(i, j)][1] > 1 else al[j]]
            run = para.add_run()
            run.text = v
            run.font.size, run.font.bold, run.font.color.rgb = Pt(pt), bold, rgb(color)
    for (i, j), (rs, cs) in spans.items():
        tb.cell(i, j).merge(tb.cell(i + rs - 1, j + cs - 1))
    if spec.get("note"):
        text(ctx, slide, x, y + sum(row_h) + 0.08, tw, 0.3, [_s(spec["note"])], 11, c["muted"], min_pt=9)
    if side:
        _callout(ctx, slide, x + w * 0.68, y, w * 0.32, h, spec.get("callout_title", ctx.tone.get("callout_title", "시사점")),
                 side)


def p_image(ctx, spec):
    """A picture (screenshot, diagram, photo) with a caption, optionally with bullets beside it."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    items = spec.get("bullets") or spec.get("takeaways")
    iw = w * 0.58 if items else w
    ix = x if not items or spec.get("side", "right") == "right" else x + w - iw  # side = where the text goes
    cap_h = 0.4 if spec.get("caption") else 0
    path = ctx.base / str(spec.get("image", ""))
    if spec.get("image") and path.is_file():
        pic = picture(slide, path, ix, y, iw, h - cap_h)
        if spec.get("frame", True):
            pic.line.color.rgb, pic.line.width = rgb(c["line"]), Pt(0.75)
        bottom = (pic.top + pic.height) / 914400
    else:
        b = box(slide, ix, y, iw, h - cap_h, fill=c["surface"], line=c["muted"], radius=0.08)
        from pptx.enum.dml import MSO_LINE
        b.line.dash_style = MSO_LINE.DASH
        name = Path(str(spec.get("image") or "?")).name
        text(ctx, slide, ix, y + (h - cap_h) / 2 - 0.3, iw, 0.5, [f"이미지 대기: {name}"], 18, c["ink"], True,
             align=PP_ALIGN.CENTER)
        ctx.warn(f"image '{name}' not found next to deck.md: placeholder drawn")
        bottom = y + h - cap_h
    if spec.get("caption"):
        text(ctx, slide, ix, bottom + 0.06, iw, 0.32, [_s(spec["caption"])], 11, c["muted"], align=PP_ALIGN.CENTER,
             min_pt=9)
    if items:
        tx = x + iw + 0.45 if ix == x else x
        text(ctx, slide, tx, y, w - iw - 0.45, h, items, ctx.tone["density"]["body_pt"] + 1, c["ink"], bullets=True,
             anchor=MSO_ANCHOR.MIDDLE, gap=10)


NEW = {"table": (p_table, {"table", "data", "columns", "where", "max_rows", "align", "widths", "total", "highlight",
                           "signed", "note", "takeaways", "callout", "callout_title"}),
       "image": (p_image, {"image", "caption", "bullets", "takeaways", "side", "frame"})}
for name, (fn, keys) in NEW.items():
    PATTERNS[name], KEYS[name] = fn, keys
INFER[:0] = [("table", "table"), ("image", "image")]
