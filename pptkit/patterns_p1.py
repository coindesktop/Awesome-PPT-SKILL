"""P1 slide patterns (docs/plan/02-slide-patterns.md). Registered into render.PATTERNS on import."""
import datetime as dt

import pandas as pd
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches

from . import data
from .render import (KEYS, PATTERNS, INFER, _callout, _s, box, card, content_slide, hline, mix, text, text_height)


def _items_h(ctx, items, w, pt):
    return text_height(list(map(_s, items)), w - 0.3, pt, gap_pt=pt * 0.7)


def _arrow(ctx, slide, x, y, w=0.55, h=0.5):
    box(slide, x, y, w, h, fill=mix(ctx.c["bg"], ctx.c["accent"], 0.55), shape=MSO_SHAPE.RIGHT_ARROW)


def _titled_list(ctx, slide, x, y, w, h, title, items, accent=False, filled=True):
    c, pt = ctx.c, ctx.tone["density"]["body_pt"]
    if filled:
        card(ctx, slide, x, y, w, h, fill="FFFFFF" if accent else None, line=c["accent"] if accent else None,
             line_pt=1.75 if accent else None)
    text(ctx, slide, x + 0.3, y + 0.22, w - 0.6, 0.5, [title], 17, c["accent"] if accent else c["ink"], bold=True, min_pt=12)
    hline(slide, x + 0.3, y + 0.82, w - 0.6, c["accent"] if accent else c["line"])
    text(ctx, slide, x + 0.3, y + 0.98, w - 0.6, h - 1.15, items, pt, c["ink"], bullets=True, gap=pt * 0.7)


def p_two_column(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    cols = spec.get("columns", [])[:2]
    pt = ctx.tone["density"]["body_pt"]
    ch = min(h, max(2.2, max((_items_h(ctx, col.get("items", []), w / 2 - 0.6, pt) for col in cols), default=0) + 1.3))
    for i, col in enumerate(cols):
        _titled_list(ctx, slide, x + i * (w / 2 + 0.15), y, w / 2 - 0.15, ch, col["title"], col.get("items", []),
                     filled=False)


def p_before_after(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    b, a = spec.get("before", {}), spec.get("after", {})
    pt = ctx.tone["density"]["body_pt"]
    cw = (w - 1.0) / 2
    ch = min(h, max(2.4, max(_items_h(ctx, b.get("items", []), cw - 0.6, pt), _items_h(ctx, a.get("items", []), cw - 0.6, pt)) + 1.3))
    _titled_list(ctx, slide, x, y, cw, ch, b.get("title", "현재"), b.get("items", []))
    _arrow(ctx, slide, x + cw + 0.22, y + ch / 2 - 0.25)
    _titled_list(ctx, slide, x + cw + 1.0, y, cw, ch, a.get("title", "개선 후"), a.get("items", []), accent=True)


def p_problem_solution(ctx, spec):
    p_before_after(ctx, {**spec, "before": {"title": spec.get("problem_title", "문제"), "items": spec.get("problems", [])},
                         "after": {"title": spec.get("solution_title", "해결"), "items": spec.get("solutions", [])}})


def p_swot(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"] - 1
    sw = spec.get("swot", {})
    names = {"S": "강점 Strengths", "W": "약점 Weaknesses", "O": "기회 Opportunities", "T": "위협 Threats"}
    gw, gh = (w - 0.25) / 2, (h - 0.25) / 2
    for i, k in enumerate("SWOT"):
        cx, cy = x + (i % 2) * (gw + 0.25), y + (i // 2) * (gh + 0.25)
        card(ctx, slide, cx, cy, gw, gh, fill=c["card"] if k in "SO" else "FFFFFF", line=c["line"])
        text(ctx, slide, cx + 0.25, cy + 0.15, 0.7, 0.75, [k], 34, c["accent"], bold=True)
        text(ctx, slide, cx + 0.95, cy + 0.32, gw - 1.2, 0.45, [names[k]], 14, c["muted"], bold=True)
        text(ctx, slide, cx + 0.95, cy + 0.85, gw - 1.2, gh - 1.0, sw.get(k, []), pt, c["ink"], bullets=True, gap=pt * 0.5)


def p_compare_table(ctx, spec):
    """criteria x options grid. Values: ●/◐/○ marks or short text. recommend: 1-based option index."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    opts, crit, rec = spec.get("options", []), spec.get("criteria", []), spec.get("recommend")
    nr, nc = len(crit) + 1, len(opts) + 1
    rh = min(0.62, h / nr)
    gt = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rh * nr))
    ctx.tables += 1
    tb = gt.table
    tb.horz_banding = tb.first_row = False
    first = min(3.2, w * 0.3)
    tb.columns[0].width = Inches(first)
    for j in range(1, nc):
        tb.columns[j].width = Inches((w - first) / (nc - 1))
    from .render import _border, rgb
    from pptx.util import Pt

    def cell(i, j, val, fill, color, bold=False, align=PP_ALIGN.CENTER, size=13):
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

    cell(0, 0, spec.get("corner", "기준"), c["card"], c["muted"], True, PP_ALIGN.LEFT)
    for j, o in enumerate(opts, start=1):
        is_rec = rec == j
        cell(0, j, o + ("  ★" if is_rec else ""), c["accent"] if is_rec else c["card"], "FFFFFF" if is_rec else c["ink"], True)
    for i, row in enumerate(crit, start=1):
        cell(i, 0, row["label"], "FFFFFF", c["ink"], True, PP_ALIGN.LEFT)
        for j, v in enumerate(row.get("values", []), start=1):
            mark = str(v) in ("●", "◐", "○")
            cell(i, j, v, mix("FFFFFF", c["card"], 0.6) if rec == j else "FFFFFF",
                 c["accent"] if mark else c["ink"], False, size=18 if mark else 13)


def p_logic_tree(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    branches = spec.get("branches", [])
    leaves_n = sum(max(1, len(b.get("leaves", []))) for b in branches) or 1
    lh = min(0.75, h / leaves_n)
    total_h = lh * leaves_n
    y0 = y + (h - total_h) / 2
    rw, bw, lw = w * 0.22, w * 0.26, w * 0.4
    rx, bx, lx = x, x + rw + 0.5, x + rw + bw + 1.0
    root = box(slide, rx, y0 + total_h / 2 - 0.6, rw, 1.2, fill=c["accent"], radius=ctx.tone["shape"]["radius"] or None)
    text(ctx, slide, 0, 0, rw, 1.2, [spec.get("root", spec["title"])], 16, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.MIDDLE, shape=root, min_pt=11)
    mids, cy = [], y0
    for b in branches:
        mids.append(cy + lh * len(b.get("leaves", []) or [""]) / 2)
        cy += lh * len(b.get("leaves", []) or [""])
    spine = rx + rw + 0.25  # elbow connector: root -> spine -> each branch
    hline(slide, rx + rw, y0 + total_h / 2, 0.25, c["line"], 1.25)
    if len(mids) > 1:
        box(slide, spine - 0.008, mids[0], 0.016, mids[-1] - mids[0], fill=c["line"])
    cy = y0
    for b in branches:
        leaves = b.get("leaves", []) or [""]
        bh = lh * len(leaves)
        mid = cy + bh / 2
        hline(slide, spine, mid, bx - spine, c["line"], 1.25)
        bb = card(ctx, slide, bx, mid - min(0.6, bh / 2 - 0.05), bw, min(1.2, bh - 0.1))
        text(ctx, slide, 0, 0, bw, min(1.2, bh - 0.1), [b["label"]], 14, c["ink"], bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, shape=bb, min_pt=10)
        for k, leaf in enumerate(leaves):
            ly = cy + k * lh + lh / 2
            if leaf:
                hline(slide, bx + bw, ly, lx - bx - bw, c["line"], 1)
                text(ctx, slide, lx, ly - lh / 2 + 0.05, lw, lh - 0.1, [leaf], ctx.tone["density"]["body_pt"] - 1, c["ink"],
                     anchor=MSO_ANCHOR.MIDDLE, min_pt=10)
        cy += bh


def p_roadmap(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    phases, lanes = spec.get("phases", []), spec.get("lanes", [])
    lw = min(2.2, w * 0.2)
    pw = (w - lw) / max(len(phases), 1)
    for j, ph in enumerate(phases):
        hd = box(slide, x + lw + j * pw + 0.05, y, pw - 0.1, 0.5, fill=c["dark"] if j == spec.get("now", 0) - 1 else c["card"],
                 radius=0.06)
        text(ctx, slide, 0, 0, pw - 0.1, 0.5, [ph], 14, "FFFFFF" if j == spec.get("now", 0) - 1 else c["ink"], bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=hd)
    rh = min(1.3, (h - 0.65) / max(len(lanes), 1))
    for i, ln in enumerate(lanes):
        ry = y + 0.65 + i * rh
        hline(slide, x, ry, w, c["line"])
        text(ctx, slide, x, ry + 0.08, lw - 0.15, rh - 0.16, [ln["name"]], 14, c["ink"], bold=True, anchor=MSO_ANCHOR.MIDDLE)
        for j, cell in enumerate(ln.get("cells", [])[:len(phases)]):
            if not cell:
                continue
            cb = box(slide, x + lw + j * pw + 0.08, ry + 0.12, pw - 0.16, rh - 0.24, fill=c["card"],
                     radius=ctx.tone["shape"]["radius"] or None)
            text(ctx, slide, 0, 0, pw - 0.16, rh - 0.24, [cell], ctx.tone["density"]["body_pt"] - 2, c["ink"],
                 anchor=MSO_ANCHOR.MIDDLE, shape=cb, min_pt=10)
            cb.text_frame.margin_left = Inches(0.12)


def _date(v):
    return pd.Timestamp(str(v)).date()


def p_gantt(ctx, spec):
    """tasks: [{name, start, end, owner}] or data: file with name/start/end columns. Month grid."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    tasks = spec.get("tasks")
    if tasks is None:
        df = data.load(ctx.base / spec["data"])
        tasks = df.rename(columns=str.lower).to_dict("records")
    t = [{**r, "s": _date(r["start"]), "e": _date(r["end"])} for r in tasks]
    lo = min(r["s"] for r in t).replace(day=1)
    hi = max(r["e"] for r in t)
    months = []
    m = lo
    while m <= hi:
        months.append(m)
        m = (m.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
    end = months[-1].replace(day=28) + dt.timedelta(days=4)
    span = (end.replace(day=1) - lo).days or 1
    nw = min(2.8, w * 0.25)
    gx, gw = x + nw, w - nw
    for i, mo in enumerate(months):
        mx = gx + (mo - lo).days / span * gw
        nxt = gx + ((months[i + 1] if i + 1 < len(months) else end.replace(day=1)) - lo).days / span * gw
        text(ctx, slide, mx, y, nxt - mx - 0.02, 0.35, [f"{mo.year % 100:02d}.{mo.month:02d}"], 11, c["muted"], bold=True)
        if i:
            box(slide, mx, y + 0.4, 0.01, h - 0.4, fill=c["line"])
    rh = min(0.55, (h - 0.45) / max(len(t), 1))
    today = dt.date.today()
    for i, r in enumerate(t):
        ry = y + 0.45 + i * rh
        text(ctx, slide, x, ry, nw - 0.15, rh, [r["name"]], 13, c["ink"], anchor=MSO_ANCHOR.MIDDLE, min_pt=10)
        bx = gx + (r["s"] - lo).days / span * gw
        bw = max(0.12, ((r["e"] - r["s"]).days + 1) / span * gw)
        live = r["s"] <= today <= r["e"]
        box(slide, bx, ry + rh * 0.22, bw, rh * 0.56, fill=c["accent"] if live else mix(c["bg"], c["accent"], 0.45),
            radius=min(0.08, rh * 0.25))
        if r.get("owner"):
            right = bx + bw + 1.5 <= x + w  # room after the bar, else put the label before it
            lx = bx + bw + 0.08 if right else max(gx, bx - 1.5)
            text(ctx, slide, lx, ry, 1.4, rh, [str(r["owner"])], 11, c["muted"], anchor=MSO_ANCHOR.MIDDLE,
                 align=PP_ALIGN.LEFT if right else PP_ALIGN.RIGHT)


def p_funnel(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    st = spec.get("stages", [])
    fw = w * 0.62
    sh = min(0.95, h / max(len(st), 1))
    top = float(st[0]["value"]) if st else 1
    for i, s in enumerate(st):
        frac = 0.35 + 0.65 * (float(s["value"]) / top)
        bw = fw * frac
        bx = x + (fw - bw) / 2
        b = box(slide, bx, y + i * sh + 0.05, bw, sh - 0.1, fill=mix(c["accent"], c["bg"], 0.12 * i),
                radius=ctx.tone["shape"]["radius"] or None)
        text(ctx, slide, 0, 0, bw, sh - 0.1, [f"{s['label']}  {float(s['value']):,.0f}"], 15, "FFFFFF", bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b, min_pt=10)
        if i:
            conv = float(s["value"]) / float(st[i - 1]["value"]) * 100
            text(ctx, slide, x + fw + 0.3, y + i * sh + 0.05, 2.2, sh - 0.1, [f"→ {conv:.1f}%"], 15, c["accent"], bold=True,
                 anchor=MSO_ANCHOR.MIDDLE)
    if spec.get("callout"):
        _callout(ctx, slide, x + fw + 2.6, y, w - fw - 2.6, h, spec.get("callout_title", "시사점"), spec["callout"])


def p_big_number(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    text(ctx, slide, x, y + 0.4, w * 0.75, 2.2, [str(spec["figure"])], 110, c["accent"], bold=True, min_pt=60)
    if spec.get("label"):
        text(ctx, slide, x, y + 2.7, w * 0.75, 0.6, [spec["label"]], 22, c["ink"], bold=True)
    if spec.get("support"):
        text(ctx, slide, x, y + 3.35, w * 0.7, 1.2, [spec["support"]], 16, c["body"])


def p_market_size(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    levels = [("TAM", spec.get("tam")), ("SAM", spec.get("sam")), ("SOM", spec.get("som"))]
    d = min(h - 0.1, w * 0.42)
    cx, cy = x + d / 2, y + h / 2
    for i, (k, v) in enumerate(levels):
        r = d / 2 * (1 - i * 0.3)
        box(slide, cx - r, cy + d / 2 - 2 * r, 2 * r, 2 * r, fill=mix(c["bg"], c["accent"], 0.18 + 0.3 * i), shape=MSO_SHAPE.OVAL)
    for i, (k, v) in enumerate(levels):
        if not v:
            continue
        ly = y + 0.3 + i * (h - 0.6) / 3
        text(ctx, slide, x + d + 0.6, ly, 1.2, 0.5, [k], 16, c["accent"], bold=True)
        text(ctx, slide, x + d + 1.8, ly - 0.05, w - d - 1.8, 0.6, [str(v.get("value", ""))], 26, c["ink"], bold=True)
        text(ctx, slide, x + d + 1.8, ly + 0.55, w - d - 1.8, 0.6, [str(v.get("label", ""))], 13, c["muted"])


NEW = {
    "two-column": (p_two_column, {"columns"}), "before-after": (p_before_after, {"before", "after"}),
    "problem-solution": (p_problem_solution, {"problems", "solutions", "problem_title", "solution_title"}),
    "swot": (p_swot, {"swot"}), "compare-table": (p_compare_table, {"options", "criteria", "recommend", "corner"}),
    "logic-tree": (p_logic_tree, {"root", "branches"}), "roadmap": (p_roadmap, {"phases", "lanes", "now"}),
    "gantt": (p_gantt, {"tasks", "data"}), "funnel": (p_funnel, {"stages", "callout", "callout_title"}),
    "big-number": (p_big_number, {"figure", "label", "support"}), "market-size": (p_market_size, {"tam", "sam", "som"}),
}
for name, (fn, keys) in NEW.items():
    PATTERNS[name], KEYS[name] = fn, keys
# inference for the new keys goes before the generic ones (e.g. `columns` stays compare)
INFER[:0] = [("criteria", "compare-table"), ("before", "before-after"), ("problems", "problem-solution"),
             ("swot", "swot"), ("branches", "logic-tree"), ("lanes", "roadmap"), ("tasks", "gantt"),
             ("stages", "funnel"), ("figure", "big-number"), ("tam", "market-size")]
