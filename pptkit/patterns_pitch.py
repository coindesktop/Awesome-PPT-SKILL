"""Pitch patterns: pillars, team, traction, pricing, product-shot, funding-ask. Registered on import."""
from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from .render import (INFER, KEYS, PATTERNS, CHART_KEYS, _chart, _no_fill, _s, box, card, content_slide, dark_color,
                     hline, mix, rgb, text, text_height, text_width)


def _lines(v):
    return [_s(x) for x in v] if isinstance(v, list) else ([_s(v)] if v else [])


def _fit(s, w, pt, floor=20):
    """Largest size <= pt at which s stays on one line in w inches."""
    while pt > floor and text_width(str(s), pt) > w * 0.8:  # bold display type runs ~15% wider than the estimate
        pt -= 2
    return pt


def p_pillars(ctx, spec):
    """3-4 strong points side by side: number (or figure), title, one or two lines."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"]
    items = [i if isinstance(i, dict) else {"title": _s(i)} for i in spec.get("pillars", [])][:4]
    n = max(len(items), 1)
    gap = 0.35
    cw = (w - gap * (n - 1)) / n
    need = max(text_height(_lines(i.get("desc")), cw - 0.6, pt, gap_pt=6) for i in items) if items else 0
    ch = min(h, max(3.2, need + 2.5, h * 0.8))  # cards use most of the body
    for k, it in enumerate(items):
        cx = x + k * (cw + gap)
        card(ctx, slide, cx, y, cw, ch)
        box(slide, cx, y, cw, 0.07, fill=c["accent"])
        head = str(it.get("figure") or f"{k + 1:02d}")
        hp = _fit(head, cw - 0.6, 40 if it.get("figure") else 30)
        text(ctx, slide, cx + 0.3, y + 0.35, cw - 0.6, 0.8, [head], hp, c["accent"], bold=True, min_pt=hp)
        text(ctx, slide, cx + 0.3, y + 1.2, cw - 0.6, 0.85, [it.get("title", "")], 20, c["ink"], bold=True, min_pt=15)
        if it.get("desc"):
            text(ctx, slide, cx + 0.3, y + 2.1, cw - 0.6, ch - 2.3 - (0.6 if it.get("note") else 0), _lines(it["desc"]),
                 pt, c["body"], gap=6)
        if it.get("note"):  # a proof point pinned to the card bottom (e.g. "도입 기관 평균 63% 감소")
            hline(slide, cx + 0.3, y + ch - 0.7, cw - 0.6, c["line"])
            text(ctx, slide, cx + 0.3, y + ch - 0.6, cw - 0.6, 0.45, [_s(it["note"])], 13, c["accent"], bold=True, min_pt=10)


def _initials(name):
    name = str(name).strip()
    parts = name.split()
    if name and ord(name[0]) > 0x3000:  # Korean/CJK: family name
        return name[0]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


def p_team(ctx, spec):
    """People cards: initials badge (no photos), name, role, one to three lines of relevant history."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"] - 1
    people = spec.get("members", [])[:8]
    cols = min(len(people), 4) or 1
    rows = (len(people) + cols - 1) // cols
    gap = 0.3
    cw = (w - gap * (cols - 1)) / cols
    adv = spec.get("advisors")
    avail = h - (0.6 if adv else 0)
    d = 0.9
    need = max((text_height(_lines(m.get("bio")), cw - 0.6, pt, gap_pt=4) for m in people), default=0)
    rh = min(avail / max(rows, 1) - (gap if rows > 1 else 0),
             max(0.3 + d + 0.3 + need + 0.3 + (0.6 if any(m.get("note") for m in people) else 0), avail * 0.7 / max(rows, 1)))
    for k, m in enumerate(people):
        cx, cy = x + (k % cols) * (cw + gap), y + (k // cols) * (rh + gap)
        card(ctx, slide, cx, cy, cw, rh)
        dot = box(slide, cx + 0.3, cy + 0.3, d, d, fill=c["accent"], shape=MSO_SHAPE.OVAL)
        text(ctx, slide, 0, 0, d, d, [_initials(m.get("name", ""))], int(d * 30), "FFFFFF", bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=dot, min_pt=12)
        tx = cx + 0.3 + d + 0.2
        text(ctx, slide, tx, cy + 0.3, cx + cw - tx - 0.2, 0.45, [m.get("name", "")], 20, c["ink"], bold=True, min_pt=14)
        text(ctx, slide, tx, cy + 0.78, cx + cw - tx - 0.2, 0.38, [m.get("role", "")], 14, c["accent"], bold=True,
             min_pt=11)
        bio = _lines(m.get("bio"))
        if bio:
            by = cy + 0.3 + d + 0.25
            hline(slide, cx + 0.3, by - 0.1, cw - 0.6, c["line"])
            text(ctx, slide, cx + 0.3, by, cw - 0.6, cy + rh - by - 0.15 - (0.6 if m.get("note") else 0), bio, pt,
                 c["body"], gap=4)
        if m.get("note"):  # why this person, in one line, at the card bottom
            text(ctx, slide, cx + 0.3, cy + rh - 0.6, cw - 0.6, 0.45, [_s(m["note"])], 13, c["accent"], bold=True, min_pt=10)
    if adv:  # right under the cards, so a short team does not leave the advisors stranded at the bottom
        ay = y + rows * rh + (rows - 1) * gap + 0.3
        text(ctx, slide, x, ay, w, 0.4, ["자문  " + " · ".join(_lines(adv))], 13, c["muted"])


def p_traction(ctx, spec):
    """Headline metrics strip on top, growth chart below (data file or inline `values`)."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    ms = [m if isinstance(m, dict) else {"value": _s(m)} for m in spec.get("metrics", [])][:4]
    top = 0
    if ms:
        mw = w / len(ms)
        vp = min(_fit(m["value"], mw - 0.5, ctx.ty["metric"] + 8, 22) for m in ms)  # one size for the whole strip
        for k, m in enumerate(ms):
            mx = x + k * mw
            if k:
                box(slide, mx, y + 0.1, 0.02, 1.25, fill=c["line"])
            text(ctx, slide, mx + (0.3 if k else 0), y, mw - 0.4, 1.15, [str(m["value"])], vp, c["accent"], bold=True,
                 min_pt=vp, anchor=MSO_ANCHOR.BOTTOM)
            text(ctx, slide, mx + (0.3 if k else 0), y + 1.15, mw - 0.4, 0.4, [m.get("label", "")], 14, c["muted"])
        top = 1.8
    if "data" in spec or "values" in spec:
        cs = {k: v for k, v in spec.items() if k in CHART_KEYS}
        cs.setdefault("chart", "line-trend")
        _chart(ctx, slide, x, y + top, w, h - top, cs)


def p_pricing(ctx, spec):
    """Plans side by side; the highlighted one gets the accent border and a badge."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"]
    tiers = spec.get("tiers", [])[:4]
    n = max(len(tiers), 1)
    gap = 0.35
    cw = min((w - gap * (n - 1)) / n, 3.9)
    x0 = x + (w - (cw * n + gap * (n - 1))) / 2
    need = max(text_height(["✓ " + f for f in _lines(t.get("features"))], cw - 0.6, pt, gap_pt=6) for t in tiers) if tiers else 0
    ch = min(h, max(need + 2.6, h * 0.8))
    for k, t in enumerate(tiers):
        cx = x0 + k * (cw + gap)
        hl = t.get("highlight")
        card(ctx, slide, cx, y, cw, ch, fill=c["surface"] if hl else None, line=c["accent"] if hl else None,
             line_pt=2 if hl else None)
        if hl:
            b = box(slide, cx + cw - 1.05, y + 0.25, 0.8, 0.34, fill=c["accent"], radius=0.17)
            text(ctx, slide, 0, 0, 0.8, 0.34, [t.get("badge", "추천")], 11, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE, shape=b)
        text(ctx, slide, cx + 0.3, y + 0.25, cw - 1.4, 0.45, [t.get("name", "")], 17, c["ink"], bold=True)
        price = str(t.get("price", ""))
        pp = _fit(price, cw - 0.6, 40, 22)
        text(ctx, slide, cx + 0.3, y + 0.75, cw - 0.6, 0.8, [price], pp, c["accent"] if hl else c["ink"], bold=True,
             min_pt=pp, anchor=MSO_ANCHOR.BOTTOM)
        sub = " · ".join(str(t[k]) for k in ("unit", "for") if t.get(k))  # "/월 · 기획·재무 1개 팀" under the price
        if sub:
            text(ctx, slide, cx + 0.3, y + 1.58, cw - 0.6, 0.4, [sub], 13, c["muted"], min_pt=10)
        hline(slide, cx + 0.3, y + 2.05, cw - 0.6, c["line"])
        text(ctx, slide, cx + 0.3, y + 2.2, cw - 0.6, ch - 2.35, ["✓  " + f for f in _lines(t.get("features"))], pt,
             c["ink"], gap=6)


def p_product_shot(ctx, spec):
    """Numbered features on the left, an empty product frame on the right for the user's screenshot."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"]
    feats = [f if isinstance(f, dict) else {"title": _s(f)} for f in spec.get("features", [])][:4]
    phone = spec.get("frame") == "phone"
    fw = min(h * 0.55, w * 0.3) if phone else w * 0.56
    lw = w - fw - 0.6
    rh = min(1.35, h / max(len(feats), 1))
    for k, f in enumerate(feats):
        fy = y + k * rh
        text(ctx, slide, x, fy, 0.7, 0.5, [f"{k + 1:02d}"], 18, c["accent"], bold=True)
        text(ctx, slide, x + 0.7, fy, lw - 0.7, 0.45, [f.get("title", "")], 18, c["ink"], bold=True, min_pt=14)
        if f.get("desc"):
            text(ctx, slide, x + 0.7, fy + 0.45, lw - 0.7, rh - 0.55, _lines(f["desc"]), pt - 1, c["body"])
    fx = x + w - fw
    fh = h if phone else min(h, fw * 0.62)
    fy = y + (h - fh) / 2
    frame = mix(c["bg"], c["ink"], 0.12)
    box(slide, fx, fy, fw, fh, fill=frame, radius=0.35 if phone else 0.12)
    inner = mix(c["bg"], c["ink"], 0.04)
    if phone:
        box(slide, fx + 0.12, fy + 0.35, fw - 0.24, fh - 0.7, fill=inner, radius=0.12)
        sx, sy, sw, sh = fx + 0.12, fy + 0.35, fw - 0.24, fh - 0.7
    else:
        for k in range(3):
            box(slide, fx + 0.22 + k * 0.22, fy + 0.15, 0.12, 0.12, fill=mix(frame, c["ink"], 0.35), shape=MSO_SHAPE.OVAL)
        box(slide, fx + 0.12, fy + 0.42, fw - 0.24, fh - 0.54, fill=inner, radius=0.06)
        sx, sy, sw, sh = fx + 0.12, fy + 0.42, fw - 0.24, fh - 0.54
    text(ctx, slide, sx, sy + sh / 2 - 0.3, sw, 0.6, [spec.get("screen", "제품 화면 (스크린샷을 붙여 넣으세요)")], 13,
         c["muted"], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def p_funding_ask(ctx, spec):
    """Amount and round, what it buys (milestones), and use of funds as a doughnut with its own legend."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, pt = ctx.c, ctx.tone["density"]["body_pt"]
    lw = w * 0.42
    if spec.get("round"):
        text(ctx, slide, x, y, lw, 0.45, [str(spec["round"])], 16, c["accent"], bold=True)
    ap = _fit(spec.get("amount", ""), lw, 66, 36)
    text(ctx, slide, x, y + 0.45, lw, 1.3, [str(spec.get("amount", ""))], ap, c["ink"], bold=True, min_pt=ap,
         anchor=MSO_ANCHOR.MIDDLE)
    ms = _lines(spec.get("milestones"))
    if ms:
        hline(slide, x, y + 1.95, lw - 0.4, c["line"])
        text(ctx, slide, x, y + 2.1, lw - 0.4, 0.4, [spec.get("milestones_title", "이 투자로 달성할 것")], 14, c["muted"],
             bold=True)
        text(ctx, slide, x, y + 2.6, lw - 0.4, h - 2.7, ms, pt + 1, c["ink"], bullets=True, gap=8)
    use = [u for u in spec.get("use", []) if isinstance(u, dict)]
    if not use:
        return
    cd = CategoryChartData()
    cd.categories = [str(u["label"]) for u in use]
    cd.add_series("사용처", [float(u.get("pct", 0)) for u in use])
    d = min(h, w * 0.24)
    cx = x + lw + 0.1
    ch = slide.shapes.add_chart(XL_CHART_TYPE.DOUGHNUT, Inches(cx), Inches(y + (h - d) / 2), Inches(d), Inches(d), cd).chart
    ctx.charts += 1
    _no_fill(ch)
    ch.has_legend, ch.has_title = False, False
    cols = [c["accent"]] + [s for s in ctx.tone["series"] if s.upper() != c["accent"].upper()]
    for k, point in enumerate(ch.plots[0].series[0].points):
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(cols[k % len(cols)])
        point.format.line.color.rgb = rgb(c["bg"])
        point.format.line.width = Pt(2)
    dn = ch.plots[0]._element
    hole = dn.find(qn("c:holeSize"))
    if hole is None:
        hole = etree.SubElement(dn, qn("c:holeSize"))
    hole.set("val", "62")
    text(ctx, slide, cx, y + h / 2 - 0.3, d, 0.6, [spec.get("use_title", "자금 사용처")], 13, c["muted"], bold=True,
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    gx = cx + d + 0.3
    gw = x + w - gx
    rh = min(0.75, h / len(use))
    gy = y + (h - rh * len(use)) / 2
    for k, u in enumerate(use):
        ly = gy + k * rh
        box(slide, gx, ly + 0.12, 0.2, 0.2, fill=cols[k % len(cols)], radius=0.04)
        text(ctx, slide, gx + 0.35, ly, gw - 1.25, rh, [str(u["label"])], 15, c["ink"], min_pt=11)
        text(ctx, slide, x + w - 0.85, ly, 0.85, rh, [f"{float(u.get('pct', 0)):g}%"], 17, c["ink"], bold=True,
             align=PP_ALIGN.RIGHT)


NEW = {
    "pillars": (p_pillars, {"pillars"}),
    "team": (p_team, {"members", "advisors"}),
    "traction": (p_traction, CHART_KEYS | {"metrics"}),
    "pricing": (p_pricing, {"tiers"}),
    "product-shot": (p_product_shot, {"features", "frame", "screen"}),
    "funding-ask": (p_funding_ask, {"amount", "round", "use", "milestones", "milestones_title", "use_title"}),
}
for name, (fn, keys) in NEW.items():
    PATTERNS[name], KEYS[name] = fn, keys
INFER[:0] = [("metrics", "traction"), ("members", "team"), ("tiers", "pricing"), ("amount", "funding-ask"),
             ("pillars", "pillars"), ("features", "product-shot")]
