"""Report visuals: waterfall and donut charts, target-vs-actual progress, project status table. Registered on import."""
from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from . import data
from .render import (KEYS, PATTERNS, SPECIAL_CHARTS, _border, _callout, _no_fill, _s, box,
                     content_slide, mix, on_color, rgb, text, text_height, text_width)

WARN_C = "D08A00"  # amber for 주의; status always carries a word, never colour alone


def _num(v):
    return f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:,.1f}"


def _items(ctx, spec):
    """Ordered (label, value) pairs: inline `values`, or `data`/`x`/`y` deltas between `start` and `end`."""
    if "values" in spec:
        return [(str(k), v) for k, v in spec["values"].items()]
    df = data.load(ctx.base / spec["data"])
    wide = data.aggregate(df, spec["x"], spec["y"], None, spec.get("agg", "sum"), spec.get("where"), spec.get("weight"))
    out = [(str(i), float(v)) for i, v in wide.iloc[:, 0].items()]
    if spec.get("start"):
        out.insert(0, (str(spec["start"]["label"]), float(spec["start"]["value"])))
    if spec.get("end"):
        out.append((str(spec["end"]), "="))
    return out


def _unit(ctx, slide, x, y, w, spec):
    unit = spec.get("unit", ctx.tone.get("unit"))
    if unit:
        text(ctx, slide, x, y - 0.05, w, 0.3, [f"단위: {unit}"], 11, ctx.c["muted"], align=PP_ALIGN.RIGHT)


def waterfall(ctx, slide, x, y, w, h, spec):
    """First item is the starting total, then signed changes; "=" draws the running total (bridge chart)."""
    c = ctx.c
    items = _items(ctx, spec)
    base, total, up, down, labels = [], [], [], [], []
    run = 0.0
    for i, (k, v) in enumerate(items):
        if i == 0 or v == "=" or str(v).strip() in ("=", "합계", "total"):
            run = float(v) if i == 0 and v != "=" else run
            base.append(0), total.append(run), up.append(None), down.append(None)
            labels.append(_num(run))
            continue
        v = float(v)
        lo = run + min(v, 0)
        base.append(lo), total.append(None)
        up.append(v if v > 0 else None), down.append(-v if v < 0 else None)
        labels.append(("+" if v > 0 else "−") + _num(abs(v)))
        run += v
    _unit(ctx, slide, x, y, w, spec)
    tops = [b + (t or 0) + (u or 0) + (d or 0) for b, t, u, d in zip(base, total, up, down)]
    pad = (max(tops) - min(min(base[1:] or [0]), min(t for t in total if t is not None))) * 0.06 or 1
    cd = CategoryChartData()
    cd.categories = [k for k, _ in items]
    # "라벨" is an invisible slab on top of each bar: its centred label sits above the bar, never inside a thin one
    for name, vals in (("base", base), ("합계", total), ("증가", up), ("감소", down), ("라벨", [pad] * len(items))):
        cd.add_series(name, vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, Inches(x), Inches(y + 0.25), Inches(w), Inches(h - 0.25),
                                cd).chart
    ctx.charts += 1
    _no_fill(ch)
    ch.has_legend = ch.has_title = False
    ch.font.size, ch.font.color.rgb = Pt(12), rgb(c["muted"])
    va, ca = ch.value_axis, ch.category_axis
    va.visible, va.has_major_gridlines = False, False
    lows = [b + 0 for b, t in zip(base, total) if t is None] + [t for t in total if t is not None]
    floor = min(lows) if lows else 0
    top = max(tops)
    if floor > 0 and spec.get("zero") is not True:  # a bridge reads its changes, so the axis starts near the data
        import math
        span = max(top - floor, 1e-9)
        step = 10 ** math.floor(math.log10(span))
        va.minimum_scale = max(0, math.floor((floor - 0.8 * span) / step) * step)
    ca.format.line.color.rgb = rgb(c["line"])
    ca.tick_labels.font.color.rgb = rgb(c["body"])
    plot = ch.plots[0]
    plot.gap_width, plot.overlap = 45, 100
    colors = {"합계": c["accent"], "증가": c["positive"], "감소": c["negative"]}
    for s in plot.series:
        if s.name in ("base", "라벨"):
            s.format.fill.background()
            s.format.line.fill.background()
            continue
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(colors[s.name])
    lab_s = [s for s in plot.series if s.name == "라벨"][0]
    for j, lab in enumerate(labels):
        kind = "합계" if total[j] is not None else "증가" if up[j] is not None else "감소"
        dl = lab_s.points[j].data_label
        dl.position = XL_LABEL_POSITION.CENTER
        r = dl.text_frame.paragraphs[0].add_run()
        r.text = lab
        r.font.size, r.font.bold = Pt(12), True
        r.font.color.rgb = rgb(c["ink"] if kind == "합계" else colors[kind])
    return None


def donut(ctx, slide, x, y, w, h, spec):
    """Composition as a ring with its own legend (label, value, share); one category may be highlighted."""
    c = ctx.c
    items = [(k, float(v)) for k, v in _items(ctx, spec) if v not in ("=", None)]
    tot = sum(v for _, v in items) or 1
    hl = spec.get("highlight")
    cols = [ctx.series[i % len(ctx.series)] for i in range(len(items))]
    if hl is not None:
        cols = [c["accent"] if k == str(hl) else mix(c["bg"], c["muted"], 0.35 + 0.08 * (i % 3))
                for i, (k, _) in enumerate(items)]
    d = min(h - 0.2, w * 0.45)
    cd = CategoryChartData()
    cd.categories = [k for k, _ in items]
    cd.add_series("구성", [v for _, v in items])
    ch = slide.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(x), Inches(y + (h - d) / 2), Inches(d), Inches(d), cd).chart
    ctx.charts += 1
    _no_fill(ch)
    ch.has_legend = ch.has_title = False
    for k, pt in enumerate(ch.plots[0].series[0].points):
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = rgb(cols[k])
        pt.format.line.color.rgb, pt.format.line.width = rgb(c["bg"]), Pt(2)
    dn = ch.plots[0]._element
    hole = dn.find(qn("c:holeSize"))
    if hole is None:
        hole = etree.SubElement(dn, qn("c:holeSize"))
    hole.set("val", "60")
    centre = spec.get("center") or _num(tot)
    hx, hw = x + d * 0.22, d * 0.56  # inside the hole
    text(ctx, slide, hx, y + h / 2 - 0.42, hw, 0.5, [str(centre)], 22, c["ink"], bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.BOTTOM, min_pt=14)
    if spec.get("center_label", "합계"):
        text(ctx, slide, hx, y + h / 2 + 0.1, hw, 0.32, [spec.get("center_label", "합계")], 11, c["muted"],
             align=PP_ALIGN.CENTER, min_pt=8)
    gx, gw = x + d + 0.4, w - d - 0.4
    rh = min(0.6, h / max(len(items), 1))
    gy = y + (h - rh * len(items)) / 2
    for k, (lab, v) in enumerate(items):
        ly = gy + k * rh
        box(slide, gx, ly + rh / 2 - 0.1, 0.2, 0.2, fill=cols[k], radius=0.04)
        text(ctx, slide, gx + 0.35, ly, gw - 2.6, rh, [lab], 15, c["ink"], anchor=MSO_ANCHOR.MIDDLE, min_pt=11)
        text(ctx, slide, gx + gw - 2.2, ly, 1.2, rh, [_num(v)], 15, c["body"], anchor=MSO_ANCHOR.MIDDLE,
             align=PP_ALIGN.RIGHT)
        text(ctx, slide, gx + gw - 0.95, ly, 0.95, rh, [f"{v / tot:.0%}"], 16, c["ink"], bold=True,
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT)
    return None


SPECIAL_CHARTS.update({"waterfall": waterfall, "donut": donut})


def _status_of(r):
    return (r >= 1.0 and ("달성", "positive")) or (r >= 0.9 and ("근접", "accent")) or ("미달", "negative")


def p_progress(ctx, spec):
    """Target vs actual per item: track, filled bar, 100% marker, actual/target and the rate with a status word."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    rows = spec.get("items") or []
    if not rows and spec.get("data"):
        df = data.load(ctx.base / spec["data"])
        rows = [{"label": r[spec["x"]], "actual": r[spec["actual"]], "target": r[spec["target"]]}
                for r in df.to_dict("records")]
    n = max(len(rows), 1)
    co = spec.get("callout")
    co = co if isinstance(co, list) else [co] if co else []
    room = text_height([_s(t) for t in co], w - 0.74, ctx.tone["density"]["body_pt"]) + 1.15 if co else 0
    y, h = y + 0.28, h - 0.28  # the 목표 marker label sits above the first row
    rh = min(1.0, (h - room) / n)  # the callout keeps its height; rows get tighter instead
    dec = any(not float(v).is_integer() for r in rows for v in (r["actual"], r["target"]))
    fnum = (lambda v: f"{float(v):,.1f}") if dec and max(abs(float(r["actual"])) for r in rows) < 1000 else _num
    lw, rw = min(2.8, w * 0.24), 3.3
    tx, tw = x + lw, w - lw - rw
    cap = float(spec.get("cap", 1.2))  # the bar track ends at 120% so overachievement stays visible
    unit = spec.get("unit", "")
    for i, r in enumerate(rows):
        ry = y + i * rh
        act, tgt = float(r["actual"]), float(r["target"])
        rate = act / tgt if tgt else 0
        word, tone = _status_of(rate)
        col = {"positive": c["positive"], "accent": c["accent"], "negative": c["negative"]}[tone]
        text(ctx, slide, x, ry, lw - 0.2, rh, [str(r["label"])], 15 if rh >= 0.5 else 13, c["ink"], bold=True,
             anchor=MSO_ANCHOR.MIDDLE,
             min_pt=11)
        bh = min(0.32, rh * 0.42)
        by = ry + (rh - bh) / 2
        box(slide, tx, by, tw, bh, fill=c["card"], radius=bh / 2)
        box(slide, tx, by, max(0.06, tw * min(rate, cap) / cap), bh, fill=col, radius=bh / 2)
        mx = tx + tw / cap
        box(slide, mx - 0.01, by - 0.08, 0.02, bh + 0.16, fill=c["ink"])
        if i == 0:
            text(ctx, slide, mx - 0.5, ry - 0.3, 1.0, 0.26, ["목표"], 10, c["muted"], align=PP_ALIGN.CENTER)
        text(ctx, slide, tx + tw + 0.15, ry, 1.65, rh, [f"{fnum(act)} / {fnum(tgt)}{unit}"], 12, c["body"],
             anchor=MSO_ANCHOR.MIDDLE, min_pt=9)
        shown = f"{rate:.0%}" if _status_of(round(rate, 2))[0] == word else f"{rate:.1%}"  # 99.5% is not "100% 근접"
        text(ctx, slide, tx + tw + 1.85, ry, 1.45, rh, [f"{shown} {word}"], 15 if rh >= 0.5 else 13, col, bold=True,
             anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.RIGHT, min_pt=11)
    if spec.get("callout"):
        _callout(ctx, slide, x, y + n * rh + 0.2, w, h - n * rh - 0.2,
                 spec.get("callout_title", ctx.tone.get("callout_title", "시사점")), spec["callout"])


STATUS = {"green": ("정상", "positive"), "정상": ("정상", "positive"), "amber": ("주의", "warn"), "주의": ("주의", "warn"),
          "red": ("지연", "negative"), "지연": ("지연", "negative"), "done": ("완료", "muted"), "완료": ("완료", "muted")}


def p_status_table(ctx, spec):
    """Project/task status: item, owner, due, status (dot + word), note. Rows from `rows` or a data file."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    rows = spec.get("rows") or (data.load(ctx.base / spec["data"]).to_dict("records") if spec.get("data") else [])
    cols = spec.get("columns", ["item", "owner", "due", "status", "note"])
    heads = spec.get("headers", {"item": "과제", "owner": "담당", "due": "일정", "status": "상태", "note": "비고"})
    widths = {"item": 3.2, "owner": 1.5, "due": 1.4, "status": 1.3}
    fixed = sum(widths.get(k, 0) for k in cols)
    nr, nc = len(rows) + 1, len(cols)
    rh = min(0.6, (h - 0.45) / nr)  # the status counts sit under the table
    tb = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rh * nr)).table
    ctx.tables += 1
    tb.horz_banding = tb.first_row = False
    for j, k in enumerate(cols):
        tb.columns[j].width = Inches(widths.get(k, max(1.5, (w - fixed) / max(1, sum(1 for q in cols if q not in widths)))))
    head_fill, head_fg = {"dark": (c["dark"], "FFFFFF"), "accent": (c["accent"], "FFFFFF")}.get(
        ctx.st["table_head"], (c["card"], c["ink"]))
    tone_c = {"positive": c["positive"], "warn": WARN_C, "negative": c["negative"], "muted": c["muted"]}

    def put(i, j, val, fill, color, bold=False, align=PP_ALIGN.LEFT, size=13):
        ce = tb.cell(i, j)
        ce.fill.solid()
        ce.fill.fore_color.rgb = rgb(fill)
        ce.vertical_anchor = MSO_ANCHOR.MIDDLE
        ce.margin_left = ce.margin_right = Inches(0.12)
        p = ce.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = str(val)
        r.font.size, r.font.bold, r.font.color.rgb = Pt(size), bold, rgb(color)
        _border(ce, "B", c["line"], 0.75)
        return p

    for j, k in enumerate(cols):
        put(0, j, heads.get(k, k), head_fill, head_fg, True, PP_ALIGN.CENTER if k in ("status", "due") else PP_ALIGN.LEFT)
    for i, r in enumerate(rows, start=1):
        fill = mix(c["surface"], c["card"], 0.55) if i % 2 == 0 else c["surface"]
        for j, k in enumerate(cols):
            v = r.get(k, "")
            v = "" if str(v) == "nan" else v
            if k == "status":
                word, tone = STATUS.get(str(v).strip().lower(), STATUS.get(str(v).strip(), (str(v), "muted")))
                put(i, j, f"● {word}" if tone != "muted" else f"✓ {word}", fill, tone_c[tone], True, PP_ALIGN.CENTER)
            else:
                put(i, j, _s(v), fill, c["ink"] if k == "item" else c["body"], k == "item",
                    PP_ALIGN.CENTER if k == "due" else PP_ALIGN.LEFT)
    counts = {}
    for r in rows:
        word = STATUS.get(str(r.get("status", "")).strip().lower(), STATUS.get(str(r.get("status", "")).strip(), ("", "")))[0]
        counts[word] = counts.get(word, 0) + 1
    summary = "   ".join(f"{k} {v}건" for k, v in counts.items() if k)
    if summary:
        text(ctx, slide, x, y + rh * nr + 0.1, w, 0.3, [summary], 12, c["muted"], align=PP_ALIGN.RIGHT)


NEW = {"progress": (p_progress, {"items", "data", "x", "actual", "target", "unit", "cap", "callout", "callout_title"}),
       "status-table": (p_status_table, {"rows", "data", "columns", "headers"})}
for name, (fn, keys) in NEW.items():
    PATTERNS[name], KEYS[name] = fn, keys
for k in ("chart-takeaway", "traction"):  # waterfall/donut extras ride on the chart patterns
    KEYS[k] = KEYS[k] | {"start", "end", "center", "center_label"}
