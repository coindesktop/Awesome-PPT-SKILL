"""deck.md -> .pptx. Every shape is native (text, autoshape, chart, table) so it stays editable."""
import math
import re
from pathlib import Path

import pandas as pd
import yaml
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from . import data, persona

W, H = 13.333, 7.5
MX = 0.6  # side margin
GOOD, BAD = "1F8F4E", "D64545"


# ---------- text measurement (shared with qa) ----------

def _cw(ch):
    o = ord(ch)
    if o >= 0x1100:
        return 0.95  # Hangul / CJK are near full-width
    if ch == " ":
        return 0.3
    return 0.62 if ch.isupper() or ch.isdigit() else 0.52


def text_height(paras, width_in, pt, spacing=1.2, gap_pt=4, pad=0.1):
    """Estimated height (in) of paragraphs at pt inside width_in. Char-width heuristic, no font files needed.
    pad = left+right (and top+bottom) insets in inches."""
    usable = max(width_in - pad, 0.1) * 0.92  # insets + word-wrap slack
    lines = 0
    for p in paras:
        lines += max(1, math.ceil(sum(_cw(c) for c in p) * pt / 72 / usable))
    return lines * pt * spacing / 72 + max(len(paras) - 1, 0) * gap_pt / 72 + pad


# ---------- primitives ----------

def rgb(h):
    return RGBColor.from_string(h)


class Ctx:
    def __init__(self, prs, tone, meta, base: Path):
        self.prs, self.tone, self.meta, self.base = prs, tone, meta, base
        self.warnings, self.page, self.charts, self.tables = [], 0, 0, 0

    def warn(self, msg):
        self.warnings.append(f"S{self.page} {msg}")


def box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    st = s._element.find(qn("p:style"))  # theme style refs add shadows; fill/line are always explicit here
    s._element.remove(st)
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(0.75)
    else:
        s.line.fill.background()
    if radius is not None:
        s.adjustments[0] = radius
    return s


def _bullet(p, indent=0.22):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(indent)))
    pPr.set("indent", str(-Inches(indent)))
    etree.SubElement(pPr, qn("a:buChar"), char="•")


def text(ctx, slide, x, y, w, h, paras, pt, color=None, bold=False, align=None, anchor=MSO_ANCHOR.TOP,
         bullets=False, min_pt=None, shape=None, gap=4):
    """paras: list of str. Font size shrinks to fit (down to min_pt); still too long -> warning."""
    paras = [_s(p) for p in (paras if isinstance(paras, list) else [paras])]
    min_pt = min_pt or max(10, pt - 4)
    tw = w - (0.22 if bullets else 0)
    size = pt
    while size > min_pt and text_height(paras, tw, size, gap_pt=gap) > h:
        size -= 1
    if text_height(paras, tw, size, gap_pt=gap) > h + 0.05:
        ctx.warn(f"overflow '{paras[0][:12]}…' (shorten or split)")
    s = shape or slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = s.text_frame
    tf.word_wrap, tf.auto_size, tf.vertical_anchor = True, MSO_AUTO_SIZE.NONE, anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(0.05))
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = t
        r.font.size, r.font.bold = Pt(size), bold
        r.font.color.rgb = rgb(color or ctx.tone["ink"])
        p.space_after = Pt(gap)
        if align:
            p.alignment = align
        if bullets:
            _bullet(p)
    return s


def _s(v):
    """YAML turns '매출: 12%' into a dict; flatten it back to the sentence the author wrote."""
    if isinstance(v, dict) and len(v) == 1:
        k, val = next(iter(v.items()))
        return f"{k}: {val}"
    return str(v)


# ---------- theme / deck setup ----------

def new_deck(tone) -> Presentation:
    prs = Presentation()
    ratio = Inches(W) / prs.slide_width
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    for layout_owner in [prs.slide_master, *prs.slide_layouts]:  # default template is 4:3; widen placeholders
        for sh in layout_owner.placeholders:
            if sh.left is not None:
                sh.left, sh.width = int(sh.left * ratio), int(sh.width * ratio)
    _apply_theme(prs, tone)
    return prs


def _apply_theme(prs, tone):
    """Write tone colors/fonts into the theme so PowerPoint's own pickers and new slides match."""
    part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(part.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    slots = {"dk1": tone["ink"], "lt1": "FFFFFF", "dk2": tone["primary"], "lt2": tone["tint"],
             "accent5": tone["primary"], "accent6": tone["accent"]}
    slots.update({f"accent{i + 1}": c for i, c in enumerate(tone["series"][:4])})
    for name, hexv in slots.items():
        el = root.find(f".//{a}clrScheme/{a}{name}")
        for child in list(el):
            el.remove(child)
        etree.SubElement(el, f"{a}srgbClr", val=hexv)
    for kind, face in (("majorFont", tone["fonts"]["title"]), ("minorFont", tone["fonts"]["body"])):
        f = root.find(f".//{a}fontScheme/{a}{kind}")
        f.find(f"{a}latin").set("typeface", face)
        f.find(f"{a}ea").set("typeface", face)
    part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def content_slide(ctx, spec, layout=5):
    ctx.page += 1
    t = ctx.tone
    slide = ctx.prs.slides.add_slide(ctx.prs.slide_layouts[layout])
    plain = t["frame"] == "plain"
    title = slide.shapes.title
    title.left, title.top, title.width, title.height = Inches(MX), Inches(0.35), Inches(W - 2 * MX), Inches(0.75)
    text(ctx, slide, 0, 0, W - 2 * MX, 0.75, [spec["title"]], 28 if plain else 24, t["primary"], bold=True,
         anchor=MSO_ANCHOR.MIDDLE, shape=title, min_pt=18, align=PP_ALIGN.LEFT)
    y = 1.2
    if spec.get("message") and not plain:
        text(ctx, slide, MX, 1.1, W - 2 * MX, 0.5, [spec["message"]], 15, t["muted"])
        y = 1.7
    src = spec.get("source") or (ctx.meta.get("source") if _has_data(spec) else None)
    if src:
        text(ctx, slide, MX, H - 0.55, 9, 0.3, [f"출처: {src}"], 10, t["muted"], min_pt=8)
    text(ctx, slide, W - MX - 1, H - 0.55, 1, 0.3, [str(ctx.page)], 10, t["muted"], align=PP_ALIGN.RIGHT)
    if spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = str(spec["notes"])
    return slide, (MX, y, W - 2 * MX, H - 0.75 - y)


def _has_data(spec):
    return any(k in spec for k in ("data", "kpis", "pivot"))


# ---------- patterns ----------

def p_cover(ctx, spec):
    ctx.page += 1
    t = ctx.tone
    slide = ctx.prs.slides.add_slide(ctx.prs.slide_layouts[0])
    dark = t["cover"] == "dark"
    if dark:
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb(t["primary"])
    fg, sub = ("FFFFFF", "D9DEE7") if dark else (t["primary"], t["muted"])
    ttl, st = slide.shapes.title, slide.placeholders[1]
    for ph, (x, y, w, h) in ((ttl, (0.9, 2.2, 11.5, 1.7)), (st, (0.9, 4.0, 11.5, 0.9))):
        ph.left, ph.top, ph.width, ph.height = Inches(x), Inches(y), Inches(w), Inches(h)
    text(ctx, slide, 0, 0, 11.5, 1.7, [spec["title"]], 40, fg, bold=True, anchor=MSO_ANCHOR.BOTTOM, shape=ttl, min_pt=28,
         align=PP_ALIGN.LEFT)
    if spec.get("subtitle"):
        text(ctx, slide, 0, 0, 11.5, 0.9, [spec["subtitle"]], 20, sub, shape=st, align=PP_ALIGN.LEFT)
    else:
        st._element.getparent().remove(st._element)
    meta = " · ".join(str(v) for v in (spec.get("date") or ctx.meta.get("date"), spec.get("author") or ctx.meta.get("author")) if v)
    if meta:
        text(ctx, slide, 0.9, 6.3, 11.5, 0.4, [meta], 14, sub)


def p_agenda(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    items = [_s(i) for i in spec.get("items", spec.get("bullets", []))]
    cols = 2 if len(items) > 5 else 1
    per = math.ceil(len(items) / cols)
    rh = min(0.9, h / per)
    for i, it in enumerate(items):
        cx, cy = x + (i // per) * (w / cols), y + (i % per) * rh
        text(ctx, slide, cx, cy, 0.9, rh, [f"{i + 1:02d}"], 26, ctx.tone["primary"], bold=True, anchor=MSO_ANCHOR.MIDDLE)
        text(ctx, slide, cx + 0.95, cy, w / cols - 1.1, rh, [it], 20, anchor=MSO_ANCHOR.MIDDLE)


def p_section(ctx, spec):
    ctx.page += 1
    t = ctx.tone
    slide = ctx.prs.slides.add_slide(ctx.prs.slide_layouts[5])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(t["tint"])
    ttl = slide.shapes.title
    ttl.left, ttl.top, ttl.width, ttl.height = Inches(0.9), Inches(3.3), Inches(11.5), Inches(1.2)
    if spec.get("number"):
        text(ctx, slide, 0.9, 2.1, 4, 1.2, [f"{int(spec['number']):02d}"], 60, t["primary"], bold=True)
    text(ctx, slide, 0, 0, 11.5, 1.2, [spec["title"]], 34, t["ink"], bold=True, shape=ttl, min_pt=24, align=PP_ALIGN.LEFT)


def p_key_message(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, {**spec, "message": None})
    text(ctx, slide, x, y + 0.8, w * 0.85, 2.0, [spec.get("statement", spec["title"])], 34, ctx.tone["primary"], bold=True,
         anchor=MSO_ANCHOR.BOTTOM, min_pt=24)
    if spec.get("support"):
        text(ctx, slide, x, y + 3.0, w * 0.85, 1.5, [spec["support"]], 18, ctx.tone["muted"])


def _callout(ctx, slide, x, y, w, h, title, items):
    t = ctx.tone
    items = items if isinstance(items, list) else [items]
    pt = t["density"]["body_pt"]
    h = min(h, max(2.5, text_height(list(map(_s, items)), w - 0.72, pt, gap_pt=pt * 0.6) + 1.1))
    box(slide, x, y, w, h, fill=t["tint"])
    text(ctx, slide, x + 0.25, y + 0.2, w - 0.5, 0.45, [title], 15, t["primary"], bold=True)
    text(ctx, slide, x + 0.25, y + 0.75, w - 0.5, h - 0.95, items, pt, bullets=True, gap=pt * 0.6)


def p_bullets_callout(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    bullets = spec.get("bullets", [])
    pt = ctx.tone["density"]["body_pt"] + 3
    bw = w * 0.6 if spec.get("callout") else w
    text(ctx, slide, x, y + 0.1, bw, h - 0.2, bullets, pt, bullets=True, gap=pt * 0.8)
    if spec.get("callout"):
        _callout(ctx, slide, x + w * 0.64, y, w * 0.36, h, spec.get("callout_title", "시사점"), spec["callout"])


def p_exec_summary(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    points, nums = spec.get("points", []), spec.get("numbers", [])
    pw = w * 0.62 if nums else w
    rh = h / max(len(points), 1)
    for i, pt_ in enumerate(points):
        cy = y + i * rh
        b = box(slide, x, cy + 0.1, 0.5, 0.5, fill=t["primary"])
        text(ctx, slide, 0, 0, 0.5, 0.5, [str(i + 1)], 16, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, shape=b)
        text(ctx, slide, x + 0.7, cy + 0.05, pw - 0.8, rh - 0.1, [_s(pt_)], t["density"]["body_pt"] + 1)
    for i, n in enumerate(nums[:3]):
        th = (h - 0.2 * (len(nums[:3]) - 1)) / len(nums[:3])
        cy = y + i * (th + 0.2)
        box(slide, x + w * 0.66, cy, w * 0.34, th, fill=t["tint"])
        text(ctx, slide, x + w * 0.66 + 0.25, cy + 0.1, w * 0.34 - 0.5, th * 0.5, [str(n["value"])], 32, t["primary"],
             bold=True, anchor=MSO_ANCHOR.BOTTOM, min_pt=20)
        text(ctx, slide, x + w * 0.66 + 0.25, cy + th * 0.62, w * 0.34 - 0.5, th * 0.33, [n["label"]], 13, t["muted"])


def p_closing(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    box(slide, x, y, w, 1.5, fill=t["tint"])
    text(ctx, slide, x + 0.3, y + 0.15, 3, 0.4, ["요청 사항"], 14, t["primary"], bold=True)
    text(ctx, slide, x + 0.3, y + 0.55, w - 0.6, 0.85, [spec.get("ask", "")], 22, t["ink"], bold=True, min_pt=16)
    steps = [s if isinstance(s, str) else f"{s['t']} ({', '.join(str(s[k]) for k in ('who', 'when') if s.get(k))})"
             for s in spec.get("next", [])]
    if steps:
        text(ctx, slide, x, y + 1.8, 4, 0.4, ["다음 단계"], 15, t["primary"], bold=True)
        text(ctx, slide, x, y + 2.3, w, h - 2.4, steps, t["density"]["body_pt"] + 1, bullets=True)


def p_compare(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    cols = spec.get("columns", [])
    rec = spec.get("recommend")
    gap = 0.3
    cw = (w - gap * (len(cols) - 1)) / max(len(cols), 1)
    pt = t["density"]["body_pt"]
    need = max((text_height(list(map(_s, c.get("items", []))), cw - 0.62, pt, gap_pt=pt * 0.6) for c in cols), default=0)
    ch_ = min(h - 0.7, max(1.8, need + 0.5))  # cards hug the longest column
    for i, c in enumerate(cols):
        cx = x + i * (cw + gap)
        is_rec = rec == i + 1
        hd = box(slide, cx, y, cw, 0.7, fill=t["primary"] if is_rec else t["tint"])
        text(ctx, slide, 0, 0, cw, 0.7, [c["title"]], 18, "FFFFFF" if is_rec else t["ink"], bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=hd)
        box(slide, cx, y + 0.7, cw, ch_, line=t["primary"] if is_rec else t["line"])
        text(ctx, slide, cx + 0.2, y + 0.9, cw - 0.4, ch_ - 0.3, c.get("items", []), pt, bullets=True, gap=pt * 0.6)
        if is_rec:
            bd = box(slide, cx + cw - 0.95, y + 0.15, 0.8, 0.4, fill=t["accent"], shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
            text(ctx, slide, 0, 0, 0.8, 0.4, ["추천"], 12, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE, shape=bd)


def p_matrix(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    notes = spec.get("callout")
    side = min(h - 0.5, (w * 0.62 if notes else w) - 0.6)
    ox, oy = x + 0.6, y
    q = spec.get("quadrants", ["", "", "", ""])  # TL, TR, BL, BR
    for i, (qx, qy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        box(slide, ox + qx * side / 2, oy + qy * side / 2, side / 2, side / 2, fill=t["tint"] if i == 1 else "FFFFFF",
            line=t["line"])
        ly = oy + 0.08 if qy == 0 else oy + side - 0.48  # names sit on the outer edge, items cluster mid-quadrant
        text(ctx, slide, ox + qx * side / 2 + 0.1, ly, side / 2 - 0.2, 0.4, [q[i]], 12, t["muted"], bold=True,
             align=PP_ALIGN.RIGHT if qx else PP_ALIGN.LEFT)
    text(ctx, slide, ox, oy + side + 0.05, side, 0.35, [f"{spec.get('x_axis', '')} →"], 12, t["muted"], align=PP_ALIGN.RIGHT)
    lbl = text(ctx, slide, ox - 0.25 - side / 2, oy + side / 2 - 0.18, side, 0.36, [f"{spec.get('y_axis', '')} →"], 12,
               t["muted"], align=PP_ALIGN.RIGHT)
    lbl.rotation = 270
    for it in spec.get("items", []):
        px, py = ox + float(it["x"]) * side, oy + (1 - float(it["y"])) * side
        box(slide, px - 0.1, py - 0.1, 0.2, 0.2, fill=t["series"][0], shape=MSO_SHAPE.OVAL)
        lw = min(2.4, sum(_cw(c) for c in it["label"]) * 12 / 72 / 0.92 + 0.2)  # hug the label
        text(ctx, slide, px + 0.15, py - 0.18, lw, 0.36, [it["label"]], 12)
    if notes:
        _callout(ctx, slide, x + w * 0.64, y, w * 0.36, h, spec.get("callout_title", "시사점"), notes)


def p_process(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    steps = [s if isinstance(s, dict) else {"title": _s(s)} for s in spec.get("steps", [])]
    sw = w / max(len(steps), 1)
    for i, s in enumerate(steps):
        shp = MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON
        hl = spec.get("highlight") == i + 1
        c = box(slide, x + i * sw, y + 0.3, sw - 0.06, 1.0, fill=t["accent"] if hl else t["primary"], shape=shp)
        text(ctx, slide, 0, 0, sw, 1.0, [s["title"]], 16, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.MIDDLE, shape=c, min_pt=11)
        if s.get("desc"):
            text(ctx, slide, x + i * sw + 0.15, y + 1.55, sw - 0.3, h - 1.6, [s["desc"]], t["density"]["body_pt"])


def p_timeline(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    ev = spec.get("events", [])
    ly = y + h * 0.45
    box(slide, x, ly - 0.02, w, 0.04, fill=t["line"])
    step = w / max(len(ev), 1)
    for i, e in enumerate(ev):
        cx = x + step * (i + 0.5)
        box(slide, cx - 0.14, ly - 0.14, 0.28, 0.28, fill=t["accent"] if e.get("now") else t["primary"], shape=MSO_SHAPE.OVAL)
        text(ctx, slide, cx - step / 2 + 0.05, ly - 0.75, step - 0.1, 0.5, [str(e["when"])], 16, t["primary"], bold=True,
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)
        text(ctx, slide, cx - step / 2 + 0.05, ly + 0.3, step - 0.1, h * 0.5, [e["label"]], t["density"]["body_pt"] - 1,
             align=PP_ALIGN.CENTER)


def p_kpi(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    t = ctx.tone
    kpis = spec.get("kpis", [])
    gap = 0.3
    tw = (w - gap * (len(kpis) - 1)) / max(len(kpis), 1)
    th = min(h, 2.9 if any(k.get("note") for k in kpis) else 2.4)
    for i, k in enumerate(kpis):
        cx = x + i * (tw + gap)
        box(slide, cx, y, tw, th, fill=t["tint"])
        text(ctx, slide, cx + 0.25, y + 0.25, tw - 0.5, 0.45, [k["label"]], 14, t["muted"], bold=True)
        text(ctx, slide, cx + 0.25, y + 0.75, tw - 0.5, 1.0, [str(k["value"])], 36, t["ink"], bold=True, min_pt=22)
        if k.get("delta"):
            d = str(k["delta"])
            down = d.startswith(("-", "▼"))
            good = down if k.get("good") == "down" else not down
            arrow = "▼" if down else "▲"  # icon + label, never color alone
            text(ctx, slide, cx + 0.25, y + 1.8, tw - 0.5, 0.45, [f"{arrow} {d.lstrip('-▲▼ ')}"], 15, GOOD if good else BAD,
                 bold=True)
        if k.get("note"):
            text(ctx, slide, cx + 0.25, y + 2.35, tw - 0.5, th - 2.45, [k["note"]], 12, t["muted"])
    if spec.get("callout"):
        _callout(ctx, slide, x, y + th + 0.3, w, h - th - 0.3, spec.get("callout_title", "시사점"), spec["callout"])


def p_chart(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    tk = spec.get("takeaways")
    cw = w * 0.63 if tk else w
    _chart(ctx, slide, x, y, cw, h, spec)
    if tk:
        _callout(ctx, slide, x + w * 0.66, y, w * 0.34, h, spec.get("callout_title", "시사점"), tk)


def _numfmt(vals, spec):
    if spec.get("fmt") == "pct":
        return "0.0%"
    v = pd.Series(vals).dropna()
    return "#,##0" if v.abs().max() >= 100 or (v % 1 == 0).all() else "#,##0.0"


def _chart(ctx, slide, x, y, w, h, spec):
    t = ctx.tone
    kind = spec.get("chart", "column-trend")
    df = data.load(ctx.base / spec["data"])
    wide = data.aggregate(df, spec["x"], spec["y"], spec.get("series"), spec.get("agg", "sum"), spec.get("where"))
    if kind == "bar-ranked":
        wide = wide.sort_values(wide.columns[0]).tail(spec.get("top", 10))  # ascending: largest drawn on top
    unit = spec.get("unit", t.get("unit"))
    if unit:
        text(ctx, slide, x, y - 0.05, w, 0.3, [f"단위: {unit}"], 11, t["muted"], align=PP_ALIGN.RIGHT)
    cd = CategoryChartData()
    cd.categories = [str(c) for c in wide.index]
    for col in wide.columns:
        cd.add_series(_label(ctx, spec, col), [None if pd.isna(v) else round(float(v), 4) for v in wide[col]])
    xl = {"column-trend": XL_CHART_TYPE.COLUMN_CLUSTERED, "bar-ranked": XL_CHART_TYPE.BAR_CLUSTERED,
          "line-trend": XL_CHART_TYPE.LINE_MARKERS}[kind]
    ch = slide.shapes.add_chart(xl, Inches(x), Inches(y + 0.25), Inches(w), Inches(h - 0.25), cd).chart
    ctx.charts += 1
    fmt = _numfmt(wide.values.ravel(), spec)
    single = len(wide.columns) == 1
    ch.font.size, ch.font.color.rgb = Pt(12), rgb(t["muted"])
    ch.has_title = False  # the slide title names the chart
    ch.has_legend = not single
    if not single:
        ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
    va, ca = ch.value_axis, ch.category_axis
    va.format.line.fill.background()
    va.tick_labels.number_format, va.tick_labels.number_format_is_linked = fmt, False
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(t["line"])
    va.major_gridlines.format.line.width = Pt(0.75)
    ca.format.line.color.rgb = rgb(t["line"])
    ca.major_tick_mark = va.major_tick_mark = XL_TICK_MARK.NONE
    plot = ch.plots[0]
    hl = str(spec["highlight"]) if spec.get("highlight") is not None else None
    if kind == "line-trend":
        for i, s in enumerate(plot.series):
            col = t["series"][i % len(t["series"])]
            s.smooth = False
            s.format.line.color.rgb, s.format.line.width = rgb(col), Pt(2.25)
            s.marker.style, s.marker.size = XL_MARKER_STYLE.CIRCLE, 7
            s.marker.format.fill.solid()
            s.marker.format.fill.fore_color.rgb = rgb(col)
            s.marker.format.line.color.rgb = rgb("FFFFFF")
            last = next(j for j in range(len(wide) - 1, -1, -1) if pd.notna(wide.iloc[j, i]))
            dl = s.points[last].data_label  # selective label: last point only
            dl.has_text_frame, dl.position = True, XL_LABEL_POSITION.RIGHT
            dl.text_frame.text = _fmt_num(wide.iloc[last, i], fmt)
        return
    plot.gap_width = 60 if single else 80
    if not single:
        plot.overlap = -10
    dense = len(wide) * len(wide.columns) > 24
    if single and not dense:  # labels carry the values, so the axis can go
        va.visible, va.has_major_gridlines = False, False
    if not dense:
        plot.has_data_labels = True
        dls = plot.data_labels
        dls.number_format, dls.number_format_is_linked = fmt, False
        dls.position = XL_LABEL_POSITION.OUTSIDE_END
        dls.font.size, dls.font.color.rgb = Pt(12), rgb(t["ink"])
    for i, s in enumerate(plot.series):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(t["series"][i % len(t["series"])])
        if single and hl:  # one accent: the highlighted point keeps the series color, the rest go neutral
            for j, cat in enumerate(wide.index):
                if str(cat) != hl:
                    pf = s.points[j].format.fill
                    pf.solid()
                    pf.fore_color.rgb = rgb(t["neutral_series"])


def _label(ctx, spec, name):
    """Display name for a data column/value: slide `labels:` beats deck `labels:`."""
    return str({**ctx.meta.get("labels", {}), **spec.get("labels", {})}.get(name, name))


def _fmt_num(v, fmt):
    if fmt == "0.0%":
        return f"{v:.1%}"
    return f"{v:,.0f}" if fmt == "#,##0" else f"{v:,.1f}"


def _mix(c1, c2, t_):
    a, b = rgb(c1), rgb(c2)
    return "".join(f"{round(a[i] + (b[i] - a[i]) * t_):02X}" for i in range(3))


def p_pivot(ctx, spec, heat=False):
    df = data.load(ctx.base / spec["data"])
    pv = data.pivot(df, spec["rows"], spec["cols"], spec["val"], spec.get("agg", "sum"), spec.get("top"), spec.get("where"))
    has_total = "합계" in pv.index
    body, total = (pv.iloc[:-1], pv.iloc[-1:]) if has_total else (pv, pv.iloc[:0])
    max_rows = spec.get("max_rows", 12)
    chunks = [body.iloc[i:i + max_rows] for i in range(0, len(body), max_rows)] or [body]
    for n, chunk in enumerate(chunks):
        part = pd.concat([chunk, total]) if n == len(chunks) - 1 else chunk
        s = {**spec, "title": spec["title"] + (" (계속)" if n else "")}
        slide, (x, y, w, h) = content_slide(ctx, s)
        unit = spec.get("unit", ctx.tone.get("unit"))
        if unit:
            text(ctx, slide, x, y - 0.05, w, 0.3, [f"단위: {unit}"], 11, ctx.tone["muted"], align=PP_ALIGN.RIGHT)
        _table(ctx, slide, x, y + 0.3, w, h - 0.3, part, body, heat, has_total, spec)


def _table(ctx, slide, x, y, w, h, part, body, heat, has_total, spec):
    t = ctx.tone
    nr, nc = len(part) + 1, len(part.columns) + 1
    rh = min(0.45, h / nr)
    first_w = min(2.4, w * 0.22)
    gt = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rh * nr))
    ctx.tables += 1
    tb = gt.table
    tb.horz_banding = tb.first_row = False
    tb.columns[0].width = Inches(first_w)
    for j in range(1, nc):
        tb.columns[j].width = Inches((w - first_w) / (nc - 1))
    numeric = body.drop(columns=["합계"], errors="ignore")
    vmin, vmax = float(numeric.min().min()), float(numeric.max().max())
    fmt = _numfmt(numeric.values.ravel(), {})
    pt = 12 if nr <= 10 else 11
    header = [_label(ctx, spec, part.index.name or "")] + [_label(ctx, spec, c) for c in part.columns]

    def cell(i, j, val, fill, color, bold=False, align=PP_ALIGN.RIGHT):
        c = tb.cell(i, j)
        c.fill.solid()
        c.fill.fore_color.rgb = rgb(fill)
        c.margin_left = c.margin_right = Inches(0.08)
        c.margin_top = c.margin_bottom = Inches(0.02)
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = c.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = val
        r.font.size, r.font.bold, r.font.color.rgb = Pt(pt), bold, rgb(color)

    for j, hv in enumerate(header):
        cell(0, j, hv, t["primary"], "FFFFFF", True, PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER)
    for i, (idx, row) in enumerate(part.iterrows(), start=1):
        is_total = has_total and str(idx) == "합계"
        cell(i, 0, str(idx), t["tint"] if is_total else "FFFFFF", t["ink"], is_total, PP_ALIGN.LEFT)
        for j, (col, v) in enumerate(row.items(), start=1):
            fill, color = ("FFFFFF", t["ink"])
            if is_total or col == "합계":
                fill = t["tint"]
            elif heat and vmax > vmin:
                k = (float(v) - vmin) / (vmax - vmin)
                fill = _mix("F7F9FC", t["series"][0], 0.15 + 0.8 * k)
                color = "FFFFFF" if k > 0.6 else t["ink"]
            cell(i, j, "" if pd.isna(v) else _fmt_num(v, fmt), fill, color, is_total or col == "합계")


PATTERNS = {
    "cover": p_cover, "agenda": p_agenda, "section": p_section, "key-message": p_key_message,
    "bullets-callout": p_bullets_callout, "exec-summary": p_exec_summary, "closing": p_closing,
    "compare": p_compare, "matrix-2x2": p_matrix, "process": p_process, "timeline": p_timeline,
    "kpi-tiles": p_kpi, "chart-takeaway": p_chart, "pivot-table": p_pivot,
    "heatmap-table": lambda c, s: p_pivot(c, s, heat=True),
}
# key present in a slide -> pattern, when `pattern:` is omitted
INFER = [("chart", "chart-takeaway"), ("rows", "pivot-table"), ("kpis", "kpi-tiles"), ("steps", "process"),
         ("events", "timeline"), ("columns", "compare"), ("quadrants", "matrix-2x2"), ("points", "exec-summary"),
         ("ask", "closing"), ("statement", "key-message"), ("items", "agenda")]


# ---------- deck.md ----------

def parse(md: str):
    meta = {}
    if md.lstrip().startswith("---"):
        _, fm, md = md.lstrip().split("---", 2)
        meta = yaml.safe_load(fm) or {}
    slides = []
    for block in re.split(r"(?m)^# ", md)[1:]:
        title, _, body = block.partition("\n")
        spec = yaml.safe_load(body) if body.strip() else {}
        if isinstance(spec, list):
            spec = {"bullets": spec}
        spec = dict(spec or {})
        spec["title"] = title.strip()
        spec.setdefault("pattern", next((p for k, p in INFER if k in spec), "bullets-callout"))
        slides.append(spec)
    return meta, slides


def load_tone(meta, base: Path):
    t = meta.get("tone")
    if t and str(t).endswith((".yaml", ".yml")):
        return yaml.safe_load((base / t).read_text(encoding="utf-8"))
    brief = meta.get("brief", {})
    if isinstance(brief, str):
        brief = yaml.safe_load((base / brief).read_text(encoding="utf-8")) or {}
    if t:
        brief = {**brief, "tone": t}
    return persona.resolve_tone(brief)[0]


def lint(ctx, spec):
    d, voice = ctx.tone["density"], ctx.tone.get("voice")
    for key in ("bullets", "callout", "takeaways", "points"):
        items = spec.get(key)
        if not isinstance(items, list):
            continue
        if len(items) > d["max_bullets"]:
            ctx.warn(f"{key} {len(items)}>{d['max_bullets']} items")
        long = [i for i in map(_s, items) if len(i) > d["max_chars"]]
        if long:
            ctx.warn(f"{key} {len(long)} item(s) >{d['max_chars']}자")
        if voice == "gaejosik":
            bad = [i for i in map(_s, items) if re.search(r"(다|요)[.!]?$", i.strip())]
            if bad:
                ctx.warn(f"{key} voice: {len(bad)} item(s) end with ~다/~요, use ~함/~임")


def build(md_path, out=None, sample=False):
    md_path = Path(md_path)
    meta, slides = parse(md_path.read_text(encoding="utf-8"))
    base = md_path.parent
    tone = load_tone(meta, base)
    if sample:  # tone check: cover + first data-bearing (or first content) slide
        rest = [s for s in slides if s["pattern"] != "cover"]
        pick = next((s for s in rest if _has_data(s)), rest[0] if rest else None)
        slides = [s for s in slides if s["pattern"] == "cover"][:1] + ([pick] if pick else [])
    ctx = Ctx(new_deck(tone), tone, meta, base)
    for spec in slides:
        fn = PATTERNS.get(spec["pattern"])
        if not fn:
            raise SystemExit(f"unknown pattern '{spec['pattern']}' on '{spec['title']}'. known: {', '.join(PATTERNS)}")
        first_page = ctx.page + 1
        fn(ctx, spec)
        _lint_at(ctx, spec, first_page)
    out = Path(out or md_path.with_suffix(".sample.pptx" if sample else ".pptx"))
    ctx.prs.save(out)
    head = f"OK {ctx.page} slides, {ctx.charts} charts, {ctx.tables} tables, tone={tone['name']} -> {out}"
    return "\n".join([head] + [f"WARN {w}" for w in ctx.warnings])


def _lint_at(ctx, spec, page):
    saved, ctx.page = ctx.page, page
    lint(ctx, spec)
    ctx.page = saved
