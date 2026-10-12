"""deck.md -> .pptx. Visual tokens come from a DESIGN.md (pptkit/designs). Every shape stays native and editable."""
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_MARK
from pptx.enum.dml import MSO_LINE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

from . import data, persona

W, H = 13.333, 7.5
MX = 0.6  # side margin
ROMAN = "ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ"


# ---------- text measurement (shared with qa) ----------

def _cw(ch):
    o = ord(ch)
    if 0x2000 <= o <= 0x206F:
        return 0.5  # general punctuation (quotes, dashes) is narrow
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


def bulleted(sh):
    return any(p._p.pPr is not None and p._p.pPr.find(qn("a:buChar")) is not None for p in sh.text_frame.paragraphs)


def extent(sh):
    """(top, bottom) in inches. An unfilled, top-anchored text box ends where its text ends (estimated)."""
    t = sh.top / 914400
    b = t + sh.height / 914400
    if not sh.has_text_frame or sh._element.tag != qn("p:sp") or sh.text_frame.vertical_anchor not in (None, MSO_ANCHOR.TOP):
        return t, b
    sp = sh._element.spPr
    if sp.find(qn("a:solidFill")) is not None or sp.find(qn("a:gradFill")) is not None:
        return t, b
    paras = [p.text for p in sh.text_frame.paragraphs if p.text.strip()]
    sizes = [r.font.size.pt for p in sh.text_frame.paragraphs for r in p.runs if r.font.size]
    if not paras or not sizes:
        return t, b
    tf = sh.text_frame
    sa = tf.paragraphs[0].space_after
    need = text_height(paras, sh.width / 914400 - (0.22 if bulleted(sh) else 0), max(sizes),
                       gap_pt=sa.pt if sa is not None else 4, pad=((tf.margin_top or 0) + (tf.margin_bottom or 0)) / 914400)
    return t, min(b, t + need)


def balance(ctx):
    """Short content leaves the lower body empty: move the body down so the space splits top/bottom (4:6)."""
    slide, start, top, bottom = ctx.body
    shapes = list(slide.shapes)[start:]
    if not shapes:
        return
    ext = [extent(sh) for sh in shapes]
    empty = bottom - max(b for _, b in ext)
    if empty < 0.8 or empty < 0.28 * (bottom - top):
        return
    dy = min(empty * 0.4, 1.2)
    for sh, (t, b) in zip(shapes, ext):
        if t + sh.height / 914400 + dy > bottom:  # declared box would cross the footer: trim to its text
            sh.height = Inches(max(b - t + 0.12, bottom - t - dy))
        sh.top = Inches(t + dy)


def text_width(s, pt):
    return sum(_cw(c) for c in s) * pt / 72


# ---------- primitives ----------

def rgb(h):
    return RGBColor.from_string(h)


def mix(c1, c2, t_):
    a, b = rgb(c1), rgb(c2)
    return "".join(f"{round(a[i] + (b[i] - a[i]) * t_):02X}" for i in range(3))


def _lum(h):
    ch = [v / 255 for v in rgb(h)]
    ch = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def on_color(h):
    """White or near-black text on a fill, whichever has the higher WCAG contrast."""
    lw = (1.05) / (_lum(h) + 0.05)
    ld = (_lum(h) + 0.05) / (_lum("1A1A1A") + 0.05)
    return "FFFFFF" if lw >= ld else "1A1A1A"


def dark_color(h):
    r, g, b = rgb(h)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b < 140


class Ctx:
    def __init__(self, prs, tone, meta, base: Path):
        self.prs, self.tone, self.meta, self.base = prs, tone, meta, base
        self.c = {"surface": "FFFFFF", **tone["colors"]}  # surface: cards/tables that sit on bg (dark designs set it)
        self.ty = tone["type"]
        # visual treatments a design can switch on (designs/*.md `style:`); defaults keep the quiet look
        self.st = {"header": "plain", "chart": "neutral", "table_head": "card", "callout": "card", "kpi": "plain",
                   **tone.get("style", {})}
        self.sections = []
        extra = ["E87BA4", "008300", "4A3AA7", "E34948", "8A919C"]
        self.series = list(tone["series"]) + [e for e in extra if e not in tone["series"]]
        self.warnings, self.page, self.charts, self.tables = [], 0, 0, 0
        self.section = meta.get("eyebrow", "")
        self.template = bool(tone.get("template"))
        self.footer_y = H - 0.5
        if self.template:  # keep footer text clear of master/layout artwork (logo bars, rules) near the bottom
            tops = [sh.top / 914400 for owner in [prs.slide_master, *prs.slide_layouts] for sh in owner.shapes
                    if not sh.is_placeholder and sh.top is not None and sh.top / 914400 > H - 0.75]
            if tops:
                self.footer_y = min(tops) - 0.34

    def layout(self, kind):
        """kind: cover | content. Default deck: built-in layouts 0/5. Template: match by name, then by placeholders."""
        lays = list(self.prs.slide_layouts)
        if not self.template:
            return lays[0 if kind == "cover" else 5]
        names = {"cover": ("title slide", "제목 슬라이드"), "content": ("title only", "제목만")}[kind]
        for lay in lays:
            if lay.name.strip().lower() in names:
                return lay
        def score(lay):
            types = [ph.placeholder_format.type for ph in lay.placeholders]
            has_title = any(t in (1, 3) for t in types)  # TITLE, CENTER_TITLE
            return (not has_title, -len(types) if kind == "cover" else len(types))
        return sorted(lays, key=score)[0]

    def warn(self, msg):
        self.warnings.append(f"S{self.page} {msg}")


def box(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE, line_pt=0.75, radius=None):
    """radius in inches -> rounded rectangle."""
    if radius:
        shape = MSO_SHAPE.ROUNDED_RECTANGLE
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s._element.remove(s._element.find(qn("p:style")))  # theme style refs add shadows; fill/line are explicit here
    if fill:
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
    else:
        s.fill.background()
    if line:
        s.line.color.rgb = rgb(line)
        s.line.width = Pt(line_pt)
    else:
        s.line.fill.background()
    if radius:
        s.adjustments[0] = min(0.5, radius / min(w, h))
    return s


def card(ctx, slide, x, y, w, h, fill=None, line=None, line_pt=None):
    sh = ctx.tone["shape"]
    border = line or (ctx.c["line"] if sh["border_pt"] else None)
    return box(slide, x, y, w, h, fill=fill or ctx.c["card"], line=border, line_pt=line_pt or sh["border_pt"] or 0.75,
               radius=sh["radius"] or None)


def hline(slide, x, y, w, color, pt=0.75):
    ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y), Inches(x + w), Inches(y))
    st = ln._element.find(qn("p:style"))
    if st is not None:
        ln._element.remove(st)  # theme effects render as a thick blurred bar in some viewers
    ln.line.color.rgb, ln.line.width = rgb(color), Pt(pt)
    return ln


_ICONS = None


def icon_names():
    global _ICONS
    if _ICONS is None:
        import json
        _ICONS = json.loads((Path(__file__).parent / "icons.json").read_text(encoding="utf-8"))
    return _ICONS


def icon(ctx, slide, name, x, y, size, color, weight=2.0):
    """Lucide line icon as one freeform shape (vector, recolourable in PowerPoint; no image). size in inches."""
    icons = icon_names()
    if name not in icons:
        import difflib
        near = difflib.get_close_matches(str(name), icons, n=3)
        ctx.warn(f"unknown icon '{name}'" + (f" (did you mean {', '.join(near)}?)" if near else "; `pptkit icons` lists them"))
        return None
    unit = Inches(size / 24)
    contours = icons[name]
    fb = slide.shapes.build_freeform(contours[0]["p"][0][0], contours[0]["p"][0][1], scale=unit)
    for k, c in enumerate(contours):
        if k:
            fb.move_to(*c["p"][0])
        fb.add_line_segments([tuple(pt) for pt in c["p"][1:]], close=c["z"])
    sh = fb.convert_to_shape(Inches(x), Inches(y))
    st = sh._element.find(qn("p:style"))
    if st is not None:
        sh._element.remove(st)
    sh.fill.background()
    sh.line.color.rgb, sh.line.width = rgb(color), Pt(max(0.75, size * 72 * weight / 24))
    ln = sh._element.spPr.find(qn("a:ln"))
    ln.set("cap", "rnd")
    etree.SubElement(ln, qn("a:round"))
    sh.name = f"icon:{name}"
    return sh


def icon_badge(ctx, slide, name, x, y, d, filled=False):
    """Icon centred in a tinted (or accent-filled) circle of diameter d."""
    c = ctx.c
    box(slide, x, y, d, d, fill=c["accent"] if filled else mix(c["bg"], c["accent"], 0.14), shape=MSO_SHAPE.OVAL)
    return icon(ctx, slide, name, x + d * 0.22, y + d * 0.22, d * 0.56, "FFFFFF" if filled else c["accent"])


def bg(slide, color, ctx=None):
    if ctx is not None and ctx.template:
        return  # keep the template master's background (logos, artwork)
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = rgb(color)


def _bullet(p, char, color, indent=0.24):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(indent)))
    pPr.set("indent", str(-Inches(indent)))
    clr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr"), val=color)
    etree.SubElement(pPr, qn("a:buChar"), char=char)


def text(ctx, slide, x, y, w, h, paras, pt, color=None, bold=False, align=None, anchor=MSO_ANCHOR.TOP,
         bullets=False, min_pt=None, shape=None, gap=4, spacing=None):
    """paras: list of str. Font size shrinks to fit (down to min_pt); still too long -> warning."""
    paras = [_s(p) for p in (paras if isinstance(paras, list) else [paras])]
    min_pt = min_pt or max(10, pt - 4)
    tw = (w - (0.24 if bullets else 0)) * (0.88 if bold and pt >= 24 else 1)  # big bold glyphs run wider
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
        r.font.color.rgb = rgb(color or ctx.c["body"])
        if i < len(paras) - 1:
            p.space_after = Pt(gap)
        if spacing:
            p.line_spacing = spacing
        if align:
            p.alignment = align
        if bullets:
            _bullet(p, ctx.tone.get("bullet", "•"), ctx.c["accent"])
    return s


def _s(v):
    """YAML turns '매출: 12%' into a dict; flatten it back to the sentence the author wrote."""
    if isinstance(v, dict) and len(v) == 1:
        k, val = next(iter(v.items()))
        return f"{k}: {val}"
    return str(v)


# ---------- theme / deck setup ----------

def new_deck(tone) -> Presentation:
    if tone.get("template"):
        prs = Presentation(tone["template"])
        if abs(prs.slide_width - Inches(W)) > Inches(0.02) or abs(prs.slide_height - Inches(H)) > Inches(0.02):
            raise SystemExit("template must be 16:9 widescreen (13.33x7.5in); its colors/fonts are still in the design")
        lst = prs.slides._sldIdLst
        for sid in list(lst):  # start from the template's masters only
            prs.part.drop_rel(sid.rId)
            lst.remove(sid)
        return prs
    prs = Presentation()
    ratio = Inches(W) / prs.slide_width
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    for owner in [prs.slide_master, *prs.slide_layouts]:  # default template is 4:3; widen placeholders
        for sh in owner.placeholders:
            xfrm = sh._element.spPr.find(qn("a:xfrm"))
            if xfrm is None:
                continue  # inherits the (already widened) master position
            off, ext = xfrm.find(qn("a:off")), xfrm.find(qn("a:ext"))
            off.set("x", str(int(int(off.get("x")) * ratio)))
            ext.set("cx", str(int(int(ext.get("cx")) * ratio)))
    _apply_theme(prs, tone)
    return prs


def _apply_theme(prs, tone):
    """Write design colors/fonts into the theme so PowerPoint's pickers and new slides match."""
    c = tone["colors"]
    part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(part.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    slots = {"dk1": c["ink"], "lt1": "FFFFFF", "dk2": c["dark"], "lt2": c["bg"], "accent5": c["accent"], "accent6": c["line"]}
    slots.update({f"accent{i + 1}": col for i, col in enumerate(tone["series"][:4])})
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


def content_slide(ctx, spec):
    """Header rhythm on every content slide: eyebrow -> title -> message -> body -> source + page."""
    ctx.page += 1
    c, ty = ctx.c, ctx.ty
    slide = ctx.prs.slides.add_slide(ctx.layout("content"))
    bg(slide, c["bg"], ctx)
    title = slide.shapes.title
    bar = ctx.st["header"] in ("bar", "bar-rule") and not ctx.template
    if not ctx.template:
        tx = MX + (0.24 if bar else 0)  # an accent bar sits left of the title
        two = text_width(spec["title"], ty["title"]) > (W - MX - tx) * 0.8  # long titles get a second line, body moves down
        title.left, title.top, title.width = Inches(tx), Inches(0.68), Inches(W - MX - tx)
        title.height = Inches(0.72 + (ty["title"] * 1.2 / 72 if two else 0))
    if bar:
        box(slide, MX, title.top / 914400 + 0.14, 0.08, title.height / 914400 - 0.28, fill=c["accent"])
    t_top, t_h = title.top / 914400, title.height / 914400
    eyebrow = spec.get("eyebrow", ctx.section)
    if eyebrow and t_top >= 0.6:
        text(ctx, slide, title.left / 914400, t_top - 0.3, 9, 0.32, [eyebrow], ty["eyebrow"], c["accent"], bold=True)
    text(ctx, slide, 0, 0, title.width / 914400, t_h, [spec["title"]], ty["title"], c["ink"], bold=True,
         anchor=MSO_ANCHOR.MIDDLE, shape=title, min_pt=18, align=PP_ALIGN.LEFT)
    y = t_top + t_h + 0.2
    if spec.get("message"):
        if ctx.tone.get("message_box"):
            b = box(slide, MX, y - 0.1, W - 2 * MX, 0.6, fill=c["card"])
            text(ctx, slide, 0, 0, W - 2 * MX, 0.6, [spec["message"]], ty["message"], c["ink"], bold=True,
                 anchor=MSO_ANCHOR.MIDDLE, shape=b)
            b.text_frame.margin_left = Inches(0.25)
            y += 0.7
        else:
            text(ctx, slide, title.left / 914400, y - 0.18, W - MX - title.left / 914400, 0.45, [spec["message"]],
                 ty["message"], c["body"])
            y += 0.4
    if ctx.st["header"] in ("rule", "bar-rule") and not ctx.template:
        hline(slide, MX, y - 0.06, W - 2 * MX, c["line"], 1)  # separates the header from the body
        y += 0.12
    src = spec.get("source") or _meta_source(ctx, spec) or (ctx.meta.get("source") if _has_data(spec) else None)
    if src:
        label = "자료" if ctx.tone["name"] == "public" else "출처"
        src = re.sub(r"^\s*(자료|출처|source)\s*[:：]\s*", "", str(src), flags=re.I)  # the label is added here
        text(ctx, slide, MX, ctx.footer_y, 9, 0.3, [f"{label}: {src}"], ty["small"], c["muted"], min_pt=8)
    text(ctx, slide, W - MX - 1, ctx.footer_y, 1, 0.3, [str(ctx.page)], ty["small"], c["muted"], align=PP_ALIGN.RIGHT)
    if spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = str(spec["notes"])
    ctx.body = (slide, len(slide.shapes), y, ctx.footer_y - 0.25)
    return slide, (MX, y, W - 2 * MX, ctx.footer_y - 0.25 - y)


def _meta_source(ctx, spec):
    """Provenance written by `pptkit fetch` next to the csv (<file>.meta.json)."""
    files = [spec.get("data")] + [c.get("data") for c in spec.get("charts", []) if isinstance(c, dict)]
    for f in filter(None, files):
        m = (ctx.base / f).with_suffix(".meta.json")
        if m.exists():
            import json
            return json.loads(m.read_text(encoding="utf-8")).get("source")
    return None


def _has_data(spec):
    return any(k in spec for k in ("data", "kpis", "charts"))


def _dark_slide(ctx, kind):
    """Background for cover/section/closing per design: dark | light | tint."""
    if ctx.template:
        return ctx.c["bg"]  # the template paints these slides; assume a light ground
    return {"dark": ctx.c["dark"], "light": ctx.c["bg"], "tint": ctx.c["card"], "accent": ctx.c["accent"]}[kind]


# ---------- structure patterns ----------

def _label_on(c, fill):
    """Accent labels vanish on an accent-filled slide (bold design): use a light tint there instead."""
    if fill.upper() == c["accent"].upper():
        return mix(fill, "FFFFFF", 0.8)
    if dark_color(fill) and dark_color(c["accent"]):  # blue on navy: lift the accent so it reads
        return mix(c["accent"], "FFFFFF", 0.45)
    return c["accent"]


def p_cover(ctx, spec):
    ctx.page += 1
    c, ty, cov = ctx.c, ctx.ty, ctx.tone["cover"]
    slide = ctx.prs.slides.add_slide(ctx.layout("cover"))
    fill = _dark_slide(ctx, cov["bg"])
    bg(slide, fill, ctx)
    dark = dark_color(fill)
    fg, sub, meta_c = ("FFFFFF", mix(fill, "FFFFFF", 0.75), mix(fill, "FFFFFF", 0.55)) if dark else (c["ink"], c["body"], c["muted"])
    if ctx.template:
        pass  # the template's own cover art stays
    elif cov.get("decor") == "circles":
        ring = mix(fill, c["accent"], 0.45 if dark else 0.25)
        cx = W - 2.5
        for r in (0.8, 1.45, 2.1):
            box(slide, cx - r, H / 2 - r, 2 * r, 2 * r, line=ring, shape=MSO_SHAPE.OVAL, line_pt=1)
        box(slide, cx - 0.16, H / 2 - 0.16, 0.32, 0.32, fill=c["accent"], shape=MSO_SHAPE.OVAL)
    elif cov.get("decor") == "orb":  # soft glow: accent-tinted discs, largest first, kept inside the slide
        cx, cy = W - 2.6, H / 2 + 0.3
        for r, t_ in ((2.5, 0.10), (1.9, 0.2), (1.3, 0.38), (0.68, 0.75)):
            box(slide, cx - r, cy - r, 2 * r, 2 * r, fill=mix(fill, "FFFFFF" if fill == c["accent"] else c["accent"], t_),
                shape=MSO_SHAPE.OVAL)
    elif cov.get("decor") == "stripe":  # accent edge + thin rule: the corporate cover
        box(slide, 0, 0, 0.32, H, fill=c["accent"])
    elif cov.get("decor") == "rule":
        box(slide, 0.9, 1.95, 0.9, 0.05, fill=c["accent"])
    ttl = slide.shapes.title
    st = next((ph for ph in slide.placeholders if ph.placeholder_format.idx == 1), None)
    if st is None:
        st = slide.shapes.add_textbox(Inches(0.9), Inches(4.55), Inches(7.6), Inches(0.8))
    if not ctx.template:
        tw = 7.0 if cov.get("decor") in ("orb", "circles") else 11.5  # keep text clear of the artwork
        th = min(3.0, max(1.9, text_height([spec["title"]], tw * 0.88, ty["cover"], spacing=1.05)))
        top = 2.55 - max(0, th - 1.9) / 2  # long titles grow both ways; the subtitle follows the title
        for ph, (x, y, w, h) in ((ttl, (0.9, top, tw, th)), (st, (0.9, top + th + 0.1, tw, 0.8))):
            ph.left, ph.top, ph.width, ph.height = Inches(x), Inches(y), Inches(w), Inches(h)
    if (spec.get("eyebrow") or ctx.meta.get("eyebrow")) and (spec.get("eyebrow") or ctx.meta.get("eyebrow")) != spec["title"]:
        ey = ttl.top / 914400 - 0.45
        if ey > 0.2:
            text(ctx, slide, ttl.left / 914400, ey, 8, 0.4, [spec.get("eyebrow") or ctx.meta["eyebrow"]], 14,
                 _label_on(c, fill), bold=True)
    text(ctx, slide, 0, 0, ttl.width / 914400, ttl.height / 914400, [spec["title"]], ty["cover"], fg, bold=True, anchor=MSO_ANCHOR.TOP, shape=ttl,
         min_pt=28, align=PP_ALIGN.LEFT, spacing=1.05)
    if spec.get("subtitle"):
        text(ctx, slide, 0, 0, st.width / 914400, st.height / 914400, [spec["subtitle"]], 18, sub, shape=st, align=PP_ALIGN.LEFT)
    else:
        st._element.getparent().remove(st._element)
    if spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = str(spec["notes"])
    meta = " · ".join(str(v) for v in (spec.get("date") or ctx.meta.get("date"),
                                       spec.get("author") or ctx.meta.get("author")) if v)
    if meta:
        text(ctx, slide, 0.9, 6.35, 8, 0.4, [meta], 13, meta_c)


def p_section(ctx, spec):
    ctx.page += 1
    c = ctx.c
    slide = ctx.prs.slides.add_slide(ctx.layout("content"))
    fill = _dark_slide(ctx, ctx.tone["section"])
    bg(slide, fill, ctx)
    fg = "FFFFFF" if dark_color(fill) else c["ink"]
    n = int(spec.get("number", 0) or 0)
    tag = (ROMAN[n - 1] if ctx.tone.get("section_numerals") == "roman" else f"{n:02d}") if n else ""
    ctx.section = f"{tag}  {spec['title']}".strip()
    if tag:
        text(ctx, slide, 0.9, 2.2, 4, 1.2, [tag], 64, _label_on(c, fill), bold=True)
    ttl = slide.shapes.title
    ttl.left, ttl.top, ttl.width, ttl.height = Inches(0.9), Inches(3.45), Inches(11.5), Inches(1.1)
    text(ctx, slide, 0, 0, 11.5, 1.1, [spec["title"]], 36, fg, bold=True, shape=ttl, min_pt=24, align=PP_ALIGN.LEFT)
    if spec.get("subtitle"):
        text(ctx, slide, 0.9, 4.6, 7, 0.6, [spec["subtitle"]], 16, mix(fill, fg, 0.7))
    if len(ctx.sections) > 1 and not ctx.template:  # where we are in the deck
        ttl.width = Inches(6.6)
        lx, ly = 8.4, max(1.2, H / 2 - 0.4 * len(ctx.sections))
        box(slide, lx - 0.35, ly - 0.1, 0.02, 0.8 * len(ctx.sections), fill=mix(fill, fg, 0.25))
        for k, name in enumerate(ctx.sections):
            cur = name == spec["title"]
            text(ctx, slide, lx, ly + k * 0.8, 0.7, 0.5, [f"{k + 1:02d}"], 16, _label_on(c, fill) if cur else mix(fill, fg, 0.4),
                 bold=True)
            text(ctx, slide, lx + 0.7, ly + k * 0.8, 3.9, 0.5, [name], 16, fg if cur else mix(fill, fg, 0.5), bold=cur,
                 min_pt=11)


def p_agenda(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    items = [_s(i) for i in spec.get("items", spec.get("bullets", []))]
    cols = 2 if len(items) > 5 else 1
    per = math.ceil(len(items) / cols)
    rh = min(0.95, h / max(per, 1))
    cw = (w - 0.5 * (cols - 1)) / cols
    for i, it in enumerate(items):
        cx, cy = x + (i // per) * (cw + 0.5), y + (i % per) * rh
        hline(slide, cx, cy, cw, c["line"])
        text(ctx, slide, cx, cy + 0.08, 1.0, rh - 0.16, [f"{i + 1:02d}"], 26, c["accent"], bold=True,
             anchor=MSO_ANCHOR.MIDDLE)
        text(ctx, slide, cx + 1.05, cy + 0.08, cw - 1.1, rh - 0.16, [it], 20, c["ink"], anchor=MSO_ANCHOR.MIDDLE)


def p_exec_summary(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, ty = ctx.c, ctx.ty
    points, nums = spec.get("points", []), spec.get("numbers", [])[:3]
    pw = w * 0.6 if nums else w
    rh = min(1.15, h / max(len(points), 1))
    for i, pt_ in enumerate(points):
        cy = y + i * rh
        hline(slide, x, cy, pw, c["line"])
        text(ctx, slide, x, cy + 0.12, 0.7, 0.45, [f"{i + 1:02d}"], 18, c["accent"], bold=True)
        text(ctx, slide, x + 0.75, cy + 0.12, pw - 0.8, rh - 0.2, [_s(pt_)], ty["body"] + 2, c["ink"])
    if nums:
        gap = 0.22
        th = (h - gap * (len(nums) - 1)) / len(nums)
        for i, n in enumerate(nums):
            cy = y + i * (th + gap)
            cx = x + w * 0.64
            lead = i == 0 and ctx.st["kpi"] == "strip"  # the headline number gets the filled card
            card(ctx, slide, cx, cy, w * 0.36, th, fill=c["accent"] if lead else None, line=c["accent"] if lead else None)
            vh = th * 0.56  # value then label, stacked by construction so they never overlap
            text(ctx, slide, cx + 0.3, cy + 0.08, w * 0.36 - 0.6, vh, [str(n["value"])], ty["metric"],
                 "FFFFFF" if lead else c["accent"], bold=True, anchor=MSO_ANCHOR.BOTTOM, min_pt=20)
            text(ctx, slide, cx + 0.3, cy + 0.08 + vh, w * 0.36 - 0.6, th - vh - 0.12, [n["label"]], 13,
                 mix(c["accent"], "FFFFFF", 0.8) if lead else c["muted"], min_pt=10)


def p_closing(ctx, spec):
    ctx.page += 1
    c = ctx.c
    slide = ctx.prs.slides.add_slide(ctx.layout("content"))
    fill = _dark_slide(ctx, ctx.tone["closing"])
    bg(slide, fill, ctx)
    dark = dark_color(fill)
    fg = "FFFFFF" if dark else c["ink"]
    sub = mix(fill, fg, 0.7)
    label = spec.get("eyebrow") or (spec["title"] if spec.get("ask") and len(spec["title"]) <= 24 else "요청 사항")
    text(ctx, slide, 0.9, 0.9, 6.4, 0.4, [label], 14, _label_on(c, fill), bold=True)
    ttl = slide.shapes.title
    ttl.left, ttl.top, ttl.width, ttl.height = Inches(0.9), Inches(1.35), Inches(6.4), Inches(2.6)
    text(ctx, slide, 0, 0, 6.4, 2.6, [spec.get("ask") or spec["title"]], 32, fg, bold=True, shape=ttl, min_pt=22,
         align=PP_ALIGN.LEFT, spacing=1.1)
    if spec.get("support"):
        text(ctx, slide, 0.9, 4.1, 6.2, 1.2, [spec["support"]], 16, sub)
    steps = [s if isinstance(s, dict) else {"t": _s(s)} for s in spec.get("next", [])][:4]
    if steps:
        text(ctx, slide, 7.75, 0.9, 4.6, 0.4, ["다음 단계"], 14, _label_on(c, fill), bold=True)
        sh = min(1.25, (H - 1.9) / len(steps) - 0.18)
        for i, s in enumerate(steps):
            cy = 1.4 + i * (sh + 0.18)
            box(slide, 7.75, cy, 4.95, sh, fill=mix(fill, fg, 0.08), radius=ctx.tone["shape"]["radius"] or None)
            dot = box(slide, 7.97, cy + sh / 2 - 0.22, 0.44, 0.44, fill=c["accent"], shape=MSO_SHAPE.OVAL)
            text(ctx, slide, 0, 0, 0.44, 0.44, [str(i + 1)], 14, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE, shape=dot)
            meta = ", ".join(str(s[k]) for k in ("who", "when") if s.get(k))
            text(ctx, slide, 8.6, cy + 0.1, 3.95, sh - 0.2, [s["t"]] + ([meta] if meta else []), 15, fg,
                 anchor=MSO_ANCHOR.MIDDLE, gap=2)
    text(ctx, slide, W - MX - 1, H - 0.5, 1, 0.3, [str(ctx.page)], ctx.ty["small"], sub, align=PP_ALIGN.RIGHT)
    if spec.get("notes"):
        slide.notes_slide.notes_text_frame.text = str(spec["notes"])


# ---------- message patterns ----------

def p_key_message(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, {**spec, "message": None})
    c = ctx.c
    if ctx.st["callout"] == "tint":
        box(slide, x, y + 0.1, w, h - 0.2, fill=mix(c["bg"], c["accent"], 0.07), radius=ctx.tone["shape"]["radius"] or None)
        box(slide, x, y + 0.1, 0.08, h - 0.2, fill=c["accent"])
        x, w = x + 0.4, w - 0.6
    text(ctx, slide, x, y + 0.3, 0.9, 1.4, ["“"], 72, mix(c["bg"], c["accent"], 0.45), bold=True, min_pt=72)
    text(ctx, slide, x + 0.9, y + 0.9, w * 0.8, 2.2, [spec.get("statement", spec["title"])], 32, c["ink"], bold=True,
         min_pt=22, spacing=1.1)
    if spec.get("support"):
        text(ctx, slide, x + 0.9, y + 3.2, w * 0.75, 1.4, [spec["support"]], 18, c["body"])


def _callout(ctx, slide, x, y, w, h, title, items):
    c = ctx.c
    items = items if isinstance(items, list) else [items]
    pt = ctx.tone["density"]["body_pt"]
    h = min(h, max(2.4, text_height(list(map(_s, items)), w - 0.74, pt, gap_pt=pt * 0.6) + 1.05))
    if ctx.st["callout"] == "tint":
        box(slide, x, y, w, h, fill=mix(c["bg"], c["accent"], 0.08), radius=ctx.tone["shape"]["radius"] or None)
        box(slide, x, y, 0.07, h, fill=c["accent"])
    else:
        card(ctx, slide, x, y, w, h)
    text(ctx, slide, x + 0.28, y + 0.22, w - 0.56, 0.4, [title], 13, c["accent"], bold=True)
    text(ctx, slide, x + 0.28, y + 0.7, w - 0.56, h - 0.9, items, pt, c["ink"], bullets=True, gap=pt * 0.6)


def p_bullets_callout(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    pt = ctx.tone["density"]["body_pt"] + 3
    bw = w * 0.6 if spec.get("callout") else w
    items = list(map(_s, spec.get("bullets", [])))
    while pt < ctx.tone["density"]["body_pt"] + 7 and text_height(items, bw - 0.22, pt + 1, gap_pt=(pt + 1) * 0.9) < h * 0.45:
        pt += 1  # few short bullets: larger type instead of an empty lower half
    text(ctx, slide, x, y + 0.05, bw, h - 0.1, spec.get("bullets", []), pt, ctx.c["ink"], bullets=True, gap=pt * 0.9)
    if spec.get("callout"):
        _callout(ctx, slide, x + w * 0.64, y, w * 0.36, h, spec.get("callout_title", ctx.tone.get("callout_title", "시사점")), spec["callout"])


# ---------- comparison / structure ----------

def p_compare(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    cols, rec = spec.get("columns", []), spec.get("recommend")
    gap = 0.3
    cw = (w - gap * (len(cols) - 1)) / max(len(cols), 1)
    pt = ctx.tone["density"]["body_pt"]
    need = max((text_height(list(map(_s, col.get("items", []))), cw - 0.8, pt, gap_pt=pt * 0.7) for col in cols), default=0)
    ch = min(h, max(2.4, need + 1.35))
    for i, col in enumerate(cols):
        cx = x + i * (cw + gap)
        is_rec = rec == i + 1
        card(ctx, slide, cx, y, cw, ch, fill=c["surface"] if is_rec else None, line=c["accent"] if is_rec else None,
             line_pt=1.75 if is_rec else None)
        text(ctx, slide, cx + 0.3, y + 0.25, cw - 1.5, 0.5, [col["title"]], 18, c["ink"], bold=True, min_pt=13)
        if is_rec:
            pill = box(slide, cx + cw - 1.05, y + 0.28, 0.8, 0.36, fill=c["accent"], radius=0.18)
            text(ctx, slide, 0, 0, 0.8, 0.36, ["추천"], 11, "FFFFFF", bold=True, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE, shape=pill)
        hline(slide, cx + 0.3, y + 0.88, cw - 0.6, c["accent"] if is_rec else c["line"])
        text(ctx, slide, cx + 0.3, y + 1.05, cw - 0.6, ch - 1.25, col.get("items", []), pt, c["ink"], bullets=True,
             gap=pt * 0.7)


def p_matrix(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    notes = spec.get("callout")
    side = min(h - 0.45, (w * 0.62 if notes else w) - 0.7)
    mw = (w * 0.6 if notes else w) - 0.4  # wide quadrants: labels have room, the slide is used
    ox, oy = x + 0.2, y + 0.35
    side = min(side, h - 0.8)
    q = spec.get("quadrants", ["", "", "", ""])  # TL, TR, BL, BR
    for i, (qx, qy) in enumerate(((0, 0), (1, 0), (0, 1), (1, 1))):
        box(slide, ox + qx * mw / 2, oy + qy * side / 2, mw / 2, side / 2,
            fill=c["card"] if i == 1 else c["surface"], line=c["line"])
        ly = oy + 0.1 if qy == 0 else oy + side - 0.5  # names on the outer edge; items cluster mid-quadrant
        text(ctx, slide, ox + qx * mw / 2 + 0.12, ly, mw / 2 - 0.24, 0.4, [q[i]], 12,
             c["accent"] if i == 1 else c["muted"], bold=True, align=PP_ALIGN.RIGHT if qx else PP_ALIGN.LEFT)
    text(ctx, slide, ox, oy + side + 0.05, mw, 0.35, [f"{spec.get('x_axis', '')} →"], 12, c["muted"], align=PP_ALIGN.RIGHT)
    text(ctx, slide, ox, oy - 0.35, mw, 0.32, [f"↑ {spec.get('y_axis', '')}"], 12, c["muted"])
    band = 0.6 / side  # keep dots out of the quadrant-name bands at the top and bottom edges
    for it in spec.get("items", []):
        fx = min(max(float(it["x"]), 0.05), 0.95)
        fy = min(max(float(it["y"]), band + 0.03), 1 - band - 0.03)
        px, py = ox + fx * mw, oy + (1 - fy) * side
        box(slide, px - 0.11, py - 0.11, 0.22, 0.22, fill=c["accent"], shape=MSO_SHAPE.OVAL)
        lw = min(2.6, text_width(it["label"], 12) / 0.92 + 0.2)
        lx = px + 0.15 if fx <= 0.7 else px - 0.15 - lw
        text(ctx, slide, lx, py - 0.18, lw, 0.36, [it["label"]], 12, c["ink"], bold=True,
             align=PP_ALIGN.LEFT if fx <= 0.7 else PP_ALIGN.RIGHT)
    if notes:
        _callout(ctx, slide, x + w * 0.64, y, w * 0.36, h, spec.get("callout_title", ctx.tone.get("callout_title", "시사점")), notes)


def _lines_of(v):
    return [_s(x) for x in v] if isinstance(v, list) else [_s(v)]


def p_process(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    steps = [s if isinstance(s, dict) else {"title": _s(s)} for s in spec.get("steps", [])]
    sw = w / max(len(steps), 1)
    cy = y + 0.55
    hline(slide, x + sw / 2, cy, sw * (len(steps) - 1), c["line"], 1.5)
    for i, s in enumerate(steps):
        cx = x + i * sw + sw / 2
        hl = spec.get("highlight") == i + 1
        dot = box(slide, cx - 0.4, cy - 0.4, 0.8, 0.8, fill=c["accent"] if hl else c["card"],
                  line=None if hl else c["line"], shape=MSO_SHAPE.OVAL)
        if s.get("icon"):
            icon(ctx, slide, s["icon"], cx - 0.22, cy - 0.22, 0.44, "FFFFFF" if hl else c["accent"])
        else:
            text(ctx, slide, 0, 0, 0.8, 0.8, [f"{i + 1}"], 20, "FFFFFF" if hl else c["accent"], bold=True,
                 align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=dot)
        ch = max(2.2, (y + h * 0.88) - (cy + 0.6))  # each step sits on a card that reaches down the body
        card(ctx, slide, cx - sw / 2 + 0.1, cy + 0.6, sw - 0.2, ch, fill=c["surface"] if hl else None,
             line=c["accent"] if hl else None, line_pt=1.75 if hl else None)
        text(ctx, slide, cx - sw / 2 + 0.2, cy + 0.8, sw - 0.4, 0.5, [s["title"]], 17, c["accent"] if hl else c["ink"],
             bold=True, align=PP_ALIGN.CENTER, min_pt=12)
        if s.get("desc"):
            text(ctx, slide, cx - sw / 2 + 0.25, cy + 1.4, sw - 0.5, ch - 1.0 - (0.5 if s.get("note") else 0),
                 _lines_of(s["desc"]), ctx.tone["density"]["body_pt"] - 1, c["body"], align=PP_ALIGN.CENTER, gap=4)
        if s.get("note"):  # duration, owner or output of the step, at the card bottom
            text(ctx, slide, cx - sw / 2 + 0.2, cy + 0.6 + ch - 0.55, sw - 0.4, 0.4, [_s(s["note"])], 12, c["accent"],
                 bold=True, align=PP_ALIGN.CENTER, min_pt=10)


def p_timeline(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c = ctx.c
    ev = spec.get("events", [])
    ly = y + min(h * 0.4, 1.6)
    hline(slide, x, ly, w, c["line"], 2)
    step = w / max(len(ev), 1)
    for i, e in enumerate(ev):
        cx = x + step * (i + 0.5)
        now = e.get("now")
        box(slide, cx - 0.15, ly - 0.15, 0.3, 0.3, fill=c["accent"] if now else c["surface"],
            line=None if now else c["accent"], line_pt=2, shape=MSO_SHAPE.OVAL)
        text(ctx, slide, cx - step / 2 + 0.05, ly - 0.8, step - 0.1, 0.55, [str(e["when"])], 18, c["accent"] if now else c["ink"],
             bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM)
        text(ctx, slide, cx - step / 2 + 0.1, ly + 0.3, step - 0.2, h * 0.5, [e["label"]],
             ctx.tone["density"]["body_pt"], c["body"], align=PP_ALIGN.CENTER)


def _spark_values(ctx, sp):
    """`spark: {data, x, y, per?, where?, last: 6}` -> the latest values, so a monthly refresh moves the line too."""
    df = data.load(ctx.base / sp["data"])
    agg = lambda col: data.aggregate(df, sp["x"], col, None, sp.get("agg", "sum"), sp.get("where"), sp.get("weight"))
    s = agg(sp["y"]).iloc[:, 0]
    if sp.get("per"):
        s = s / agg(sp["per"]).iloc[:, 0] * 100
    return [round(float(v), 4) for v in s.tail(int(sp.get("last", 6)))]


def p_kpi(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, ty = ctx.c, ctx.ty
    kpis = [{**k, "spark": _spark_values(ctx, k["spark"])} if isinstance(k.get("spark"), dict) else k
            for k in spec.get("kpis", [])]
    gap = 0.28
    tw = (w - gap * (len(kpis) - 1)) / max(len(kpis), 1)
    sp = 0.85 if any(k.get("spark") for k in kpis) else 0  # room for a sparkline under the delta
    th = min(h, (2.9 if any(k.get("note") for k in kpis) else 2.4) + sp)
    if spec.get("callout"):
        th = min(th, h - 1.7)  # the callout below always keeps at least 1.4in
        if th < 2.3:
            sp, th = 0, min(h - 1.7, 2.4)
            ctx.warn("kpi-tiles: sparklines dropped to leave room for the callout (or move the callout to `message:`)")
    else:
        th = max(th, min(h, 3.4))  # tiles take the body when nothing sits below them
    for i, k in enumerate(kpis):
        cx = x + i * (tw + gap)
        card(ctx, slide, cx, y, tw, th)
        if ctx.st["kpi"] == "strip":
            box(slide, cx, y, tw, 0.07, fill=c["accent"] if i == 0 else mix(c["bg"], c["accent"], 0.45))
        if k.get("icon"):
            icon(ctx, slide, k["icon"], cx + tw - 0.68, y + 0.24, 0.4, c["accent"] if i == 0 else mix(c["card"], c["accent"], 0.7))
        text(ctx, slide, cx + 0.28, y + 0.25, tw - 0.56 - (0.45 if k.get("icon") else 0), 0.4, [k["label"]], 13,
             c["muted"], bold=True)
        vpt = ty["metric"]
        while vpt > 18 and text_width(str(k["value"]), vpt) > (tw - 0.56) * 0.78:
            vpt -= 2  # a value stays on one line: shrink it rather than wrap "월 49만 원"
        text(ctx, slide, cx + 0.28, y + 0.7, tw - 0.56, 1.0, [str(k["value"])], vpt, c["accent"], bold=True, min_pt=vpt)
        if k.get("delta"):
            d = str(k["delta"])
            down = d.startswith(("-", "▼"))
            good = down if k.get("good") == "down" else not down
            arrow = "▼" if down else "▲"  # icon + label, never color alone
            text(ctx, slide, cx + 0.28, y + 1.72, tw - 0.56, 0.42, [f"{arrow} {d.lstrip('▲▼ ')}"], 15,
                 c["positive"] if good else c["negative"], bold=True)
        if k.get("spark") and sp:
            _spark(ctx, slide, cx + 0.2, y + 2.15, tw - 0.4, 0.75, k["spark"], i == 0)
        if k.get("note"):
            text(ctx, slide, cx + 0.28, y + 2.2 + sp, tw - 0.56, th - 2.3 - sp, [k["note"]], 12, c["muted"])
    if spec.get("callout"):
        _callout(ctx, slide, x, y + th + 0.3, w, h - th - 0.3, spec.get("callout_title", ctx.tone.get("callout_title", "시사점")), spec["callout"])


def _spark(ctx, slide, x, y, w, h, values, lead):
    """Tiny trend line in a KPI tile: no axes, no grid, last point marked."""
    vals = [float(v) for v in values]
    cd = CategoryChartData()
    cd.categories = [str(i) for i in range(len(vals))]
    cd.add_series("trend", vals)
    ch = slide.shapes.add_chart(XL_CHART_TYPE.LINE, Inches(x), Inches(y), Inches(w), Inches(h), cd).chart
    _no_fill(ch)
    ch.has_legend = ch.has_title = False
    ch.value_axis.visible = ch.category_axis.visible = False
    ch.value_axis.has_major_gridlines = False
    lo, hi = min(vals), max(vals)
    ch.value_axis.minimum_scale, ch.value_axis.maximum_scale = lo - (hi - lo) * 0.1, hi + (hi - lo) * 0.15 or hi + 1
    s = ch.plots[0].series[0]
    col = ctx.c["accent"] if lead else mix(ctx.c["bg"], ctx.c["accent"], 0.6)
    s.smooth = False
    s.format.line.color.rgb, s.format.line.width = rgb(col), Pt(2)
    s.marker.style = XL_MARKER_STYLE.NONE
    pt = s.points[len(vals) - 1]
    pt.marker.style, pt.marker.size = XL_MARKER_STYLE.CIRCLE, 7
    pt.marker.format.fill.solid()
    pt.marker.format.fill.fore_color.rgb = rgb(col)
    pt.marker.format.line.color.rgb = rgb(ctx.c["card"])


# ---------- data patterns ----------

def p_chart(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    tk = spec.get("takeaways")
    cw = w * 0.63 if tk else w
    _chart(ctx, slide, x, y, cw, h, spec)
    if tk:
        _callout(ctx, slide, x + w * 0.66, y, w * 0.34, h, spec.get("callout_title", ctx.tone.get("callout_title", "시사점")), tk)


def p_chart_table(ctx, spec):
    """Chart on the left, the same numbers as a compact table on the right (optionally with growth)."""
    if spec.get("chart") in SPECIAL_CHARTS:  # a bridge or ring already carries its numbers
        return p_chart(ctx, spec)
    slide, (x, y, w, h) = content_slide(ctx, spec)
    wide = _chart(ctx, slide, x, y, w * 0.56, h, spec)
    tbl = wide.copy()
    tbl.columns = [_label(ctx, spec, col) for col in tbl.columns]
    timed = data.is_time(list(wide.index))
    if spec.get("growth") and len(tbl.columns) == 1:
        tbl["증감률"] = tbl.iloc[:, 0].pct_change() * 100
    elif spec.get("growth") and len(wide.columns) >= 2 and data.is_time(list(wide.columns)):  # periods as series
        tbl["증감률"] = (wide.iloc[:, -1] / wide.iloc[:, 0] - 1).values * 100
    tbl.index.name = _label(ctx, spec, spec["x"])
    if not timed and spec.get("agg", "sum") == "sum" and not _is_share(spec) and len(tbl) > 2:  # regions: a total row
        tot = wide.sum()
        row = [tot[c] for c in wide.columns]
        if "증감률" in tbl.columns:
            row.append(np.nan if len(wide.columns) == 1 else (tot.iloc[-1] / tot.iloc[0] - 1) * 100)
        tbl.loc["합계"] = row
    if timed and len(tbl) > 8:  # the chart shows the whole series; the table keeps the latest rows readable
        tbl = tbl.tail(int(spec.get("table_rows", 6)))
    elif len(tbl) > 13:  # categories: up to 12 rows + 합계
        ctx.warn(f"chart-table: table shows 12 of {len(tbl) - 1} categories; use `top` or `where`")
        tbl = pd.concat([tbl.head(12), tbl.tail(1)]) if tbl.index[-1] == "합계" else tbl.head(12)
    th = min(h - 0.3, 0.42 * (len(tbl) + 1))
    if spec.get("takeaways"):
        th = min(th, max(h - 1.9, 0.26 * (len(tbl) + 1)))  # leave the takeaways their room; rows get tighter
    _table(ctx, slide, x + w * 0.6, y + 0.3, w * 0.4, th, tbl, tbl, False, tbl.index[-1] == "합계", spec,
           pct_cols=["증감률"])
    if spec.get("takeaways") and h - th - 0.6 <= 1.0:
        ctx.warn("chart-table: no room for takeaways under the table (fewer rows via `where`, or use chart-takeaway)")
    if spec.get("takeaways") and h - th - 0.6 > 1.0:
        text(ctx, slide, x + w * 0.6, y + th + 0.55, w * 0.4, h - th - 0.6, spec["takeaways"],
             ctx.tone["density"]["body_pt"] - 1, ctx.c["ink"], bullets=True, gap=6)


def p_chart_pair(ctx, spec):
    slide, (x, y, w, h) = content_slide(ctx, spec)
    charts = spec.get("charts", [])[:2]
    gap = 0.5
    cw = (w - gap) / 2
    for i, sub in enumerate(charts):
        cx = x + i * (cw + gap)
        shared = ("data", "labels") if _is_share(sub) else ("data", "unit", "labels")  # % charts keep their own unit
        sub = {**{k: v for k, v in spec.items() if k in shared}, **sub}
        text(ctx, slide, cx, y, cw, 0.4, [sub.get("subtitle", "")], 15, ctx.c["ink"], bold=True)
        _chart(ctx, slide, cx, y + 0.45, cw, h - 0.45, sub)


def _is_share(spec):
    return spec.get("chart") == "stacked-share" or spec.get("fmt") == "pct"


def _numfmt(vals, spec, table=False):
    if spec.get("fmt") == "pct":
        return "0.0%"
    v = pd.Series(vals).dropna()
    if table:  # tables have room: 818.8 stays 818.8 so chart-table and heatmap agree
        return "#,##0" if v.abs().max() >= 100000 or (v.round(6) % 1 == 0).all() else "#,##0.0"
    return "#,##0" if v.abs().max() >= 1000 or (v.round(6) % 1 == 0).all() else "#,##0.0"  # 96.4 stays 96.4


def _no_fill(chart):
    """Transparent chart area so the slide background shows through."""
    cs = chart._chartSpace
    sp = cs.find(qn("c:spPr"))
    if sp is None:
        sp = etree.SubElement(cs, qn("c:spPr"))
        cs.insert(cs.index(cs.find(qn("c:chart"))) + 1, sp)
    sp.clear()
    etree.SubElement(sp, qn("a:noFill"))
    ln = etree.SubElement(sp, qn("a:ln"))
    etree.SubElement(ln, qn("a:noFill"))


CHARTS = {"column-trend": XL_CHART_TYPE.COLUMN_CLUSTERED, "bar-ranked": XL_CHART_TYPE.BAR_CLUSTERED,
          "line-trend": XL_CHART_TYPE.LINE_MARKERS, "stacked": XL_CHART_TYPE.COLUMN_STACKED,
          "stacked-share": XL_CHART_TYPE.COLUMN_STACKED}  # shares are precomputed


SPECIAL_CHARTS = {}  # waterfall, donut (patterns_report): drawn their own way


def _chart(ctx, slide, x, y, w, h, spec):
    c = ctx.c
    kind = spec.get("chart", "column-trend")
    if kind in SPECIAL_CHARTS:
        return SPECIAL_CHARTS[kind](ctx, slide, x, y, w, h, spec)
    if kind not in CHARTS:
        raise SystemExit(f"unknown chart '{kind}'. known: {', '.join([*CHARTS, *SPECIAL_CHARTS])}")
    if "values" in spec:  # numbers the user typed: {category: value} or {series: {category: value}}
        v = spec["values"]
        nested = all(isinstance(x, dict) for x in v.values())
        wide = pd.DataFrame(v if nested else {spec.get("y", "값"): v})
        wide.index = wide.index.map(str)
        spec = {"x": "", "y": wide.columns[0], **spec}
    else:
        df = data.load(ctx.base / spec["data"])
        wide = data.aggregate(df, spec["x"], spec["y"], spec.get("series"), spec.get("agg", "sum"), spec.get("where"),
                              spec.get("weight"))
        if not data.is_time(list(wide.index)):  # categories (regions, products): largest first with `top`, else file order
            if spec.get("top") and kind != "bar-ranked":
                wide = wide.loc[wide.iloc[:, -1].sort_values(ascending=False).index[:int(spec["top"])]]
            else:
                order = [k for k in dict.fromkeys(df[spec["x"]]) if k in wide.index]
                wide = wide.loc[order + [k for k in wide.index if k not in order]]
    if kind == "bar-ranked":
        wide = wide.sort_values(wide.columns[0]).tail(spec.get("top", 10))  # ascending: largest drawn on top
    if kind == "stacked-share":
        wide = wide.div(wide.sum(axis=1), axis=0)  # shares per category, labelled as %
    unit = spec.get("unit", "%" if _is_share(spec) else ctx.tone.get("unit"))
    if unit:
        text(ctx, slide, x, y - 0.05, w, 0.3, [f"단위: {unit}"], 11, c["muted"], align=PP_ALIGN.RIGHT)
    cd = CategoryChartData()
    cats = [str(v) for v in wide.index]
    if len(cats) > 6 and all(re.fullmatch(r"(19|20)\d{2}-\d{2}", c_) for c_ in cats):
        cats = [f"{c_[2:4]}.{c_[5:]}" for c_ in cats]  # 2026-01 -> 26.01 so long month axes do not wrap
    cd.categories = cats
    for col in wide.columns:
        cd.add_series(_label(ctx, spec, col), [None if pd.isna(v) else round(float(v), 4) for v in wide[col]])
    ch = slide.shapes.add_chart(CHARTS[kind], Inches(x), Inches(y + 0.25), Inches(w), Inches(h - 0.25), cd).chart
    ctx.charts += 1
    _no_fill(ch)
    fmt = "0%" if kind == "stacked-share" else _numfmt(wide.values.ravel(), spec)
    single = len(wide.columns) == 1
    ch.font.size, ch.font.color.rgb = Pt(12), rgb(c["muted"])
    ch.has_title = False  # the slide title names the chart
    ch.has_legend = not single
    if not single:
        ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.TOP, False
        ch.legend.font.color.rgb = rgb(c["body"])
    va, ca = ch.value_axis, ch.category_axis
    va.format.line.fill.background()
    axis_fmt = "#,##0" if fmt == "#,##0.0" and np.nanmax(np.abs(wide.values.astype(float))) >= 10 else \
        "0%" if fmt == "0.0%" else fmt
    va.tick_labels.number_format, va.tick_labels.number_format_is_linked = axis_fmt, False  # ticks stay round
    va.has_major_gridlines = True
    va.major_gridlines.format.line.color.rgb = rgb(c["line"])
    va.major_gridlines.format.line.width = Pt(0.75)
    ca.format.line.color.rgb = rgb(c["line"])
    ca.tick_labels.font.color.rgb = rgb(c["body"])
    ca.major_tick_mark = va.major_tick_mark = XL_TICK_MARK.NONE
    plot = ch.plots[0]
    series_c = [c["accent"]] if single else ctx.series  # one series = the design accent
    hls = spec.get("highlight")
    hls = [hls] if hls is not None and not isinstance(hls, list) else (hls or [])
    hls = {str(data.period(pd.Series(list(wide.index), name=spec.get("x", "x")), v)
               if isinstance(v, str) and data.PERIOD.fullmatch(v) else v) for v in hls}  # latest -> 2026
    hl = next(iter(hls)) if hls else None
    names = [_label(ctx, spec, col) for col in wide.columns]
    if not single and hls & (set(names) | {str(col) for col in wide.columns}):  # emphasise one series, mute the rest
        series_c = [c["accent"] if (n in hls or str(col) in hls) else mix(c["bg"], c["muted"], 0.55)
                    for n, col in zip(names, wide.columns)]
    elif not single and not kind.startswith("stacked") and data.is_time(list(wide.columns)):
        series_c = [mix(c["bg"], c["muted"], 0.3 + 0.25 * i / max(1, len(names) - 2)) for i in range(len(names) - 1)] \
            + [c["accent"]]  # periods as series (2025Q3 vs 2026Q3): the latest carries the accent
    if kind == "line-trend" or spec.get("ymin") is not None:
        lo_, hi_ = float(np.nanmin(wide.values)), float(np.nanmax(wide.values))
        ymin = spec.get("ymin")
        if ymin is None and kind == "line-trend" and lo_ > 0 and lo_ > 0.45 * hi_:
            step = 10 ** math.floor(math.log10(max(hi_ - lo_, 1e-9)))
            ymin = math.floor(lo_ * 0.95 / step) * step
        if ymin is not None:
            va.minimum_scale = float(ymin)
    if kind == "line-trend":
        for i, s in enumerate(plot.series):
            col = series_c[i % len(series_c)]
            s.smooth = False
            s.format.line.color.rgb, s.format.line.width = rgb(col), Pt(2.5)
            s.marker.style, s.marker.size = XL_MARKER_STYLE.CIRCLE, 7
            s.marker.format.fill.solid()
            s.marker.format.fill.fore_color.rgb = rgb(col)
            s.marker.format.line.color.rgb = rgb(c["bg"])
            last = next(j for j in range(len(wide) - 1, -1, -1) if pd.notna(wide.iloc[j, i]))
            dl = s.points[last].data_label  # selective label: last point only
            dl.has_text_frame, dl.position = True, XL_LABEL_POSITION.RIGHT
            dl.text_frame.text = _fmt_num(wide.iloc[last, i], fmt)
            dl.font.bold, dl.font.color.rgb = True, rgb(col)
        return wide
    plot.gap_width = 55 if single else 70
    if kind.startswith("stacked"):
        plot.overlap = 100
        va.visible, va.has_major_gridlines = False, False  # segment labels carry the values
        for i, s in enumerate(plot.series):
            col = series_c[i % len(series_c)]
            s.format.fill.solid()
            s.format.fill.fore_color.rgb = rgb(col)
            s.format.line.color.rgb, s.format.line.width = rgb(c["bg"]), Pt(1.5)  # surface gap between segments
            totals = wide.sum(axis=1).replace(0, np.nan)
            for j, v in enumerate(wide.iloc[:, i]):
                share = (v / totals.iloc[j]) if pd.notna(v) and pd.notna(totals.iloc[j]) else 0
                if share < 0.07 or (len(wide) > 8 and j != len(wide) - 1):
                    continue  # a label that cannot fit is worse than none; the table/legend carry it
                dl = s.points[j].data_label
                dl.has_text_frame = True
                dl.text_frame.text = _fmt_num(v, fmt) if fmt != "0%" else f"{v:.0%}"
                dl.position = XL_LABEL_POSITION.CENTER
                dl.font.size, dl.font.color.rgb = Pt(11), rgb(on_color(col))
        return wide
    if not single:
        plot.overlap = -10
    slot = w * 0.88 / max(1, len(wide)) / (len(wide.columns) + (0.55 if single else 0.7))  # one bar's width (in)
    longest = max((len(_fmt_num(v, fmt)) for v in wide.values.ravel() if pd.notna(v)), default=1)
    dense = len(wide) * len(wide.columns) > 24 or (kind != "bar-ranked" and longest * 12 * 0.62 / 72 > slot * 1.15)
    # ^ column labels wider than their bar collide; horizontal bars put labels at the bar end, so length is free
    if single and not dense:  # labels carry the values, so the axis can go
        va.visible, va.has_major_gridlines = False, False
    if not dense:
        plot.has_data_labels = True
        dls = plot.data_labels
        dls.number_format, dls.number_format_is_linked = fmt, False
        dls.position = XL_LABEL_POSITION.OUTSIDE_END
        dls.font.size, dls.font.color.rgb = Pt(12), rgb(c["body"])
    for i, s in enumerate(plot.series):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(series_c[i % len(series_c)])
        if single and hl:  # one accent: the highlighted point keeps the color, the rest go neutral
            for j, cat in enumerate(wide.index):
                if str(cat) not in hls:
                    pf = s.points[j].format.fill
                    pf.solid()
                    pf.fore_color.rgb = rgb(mix(c["bg"], c["accent"], 0.38) if ctx.st["chart"] == "tint"
                                            else c["neutral_series"])
    return wide


def _label(ctx, spec, name):
    """Display name for a data column/value: slide `labels:` beats deck `labels:`."""
    return str({**ctx.meta.get("labels", {}), **spec.get("labels", {})}.get(name, name))


def _fmt_num(v, fmt):
    if fmt == "0.0%":
        return f"{v:.1%}"
    return f"{v:,.0f}" if fmt == "#,##0" else f"{v:,.1f}"


def p_pivot(ctx, spec, heat=False):
    df = data.load(ctx.base / spec["data"])
    pv = data.pivot(df, spec["rows"], spec["cols"], spec["val"], spec.get("agg", "sum"), spec.get("top"),
                    spec.get("where"), weight=spec.get("weight"))
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
            text(ctx, slide, x, y - 0.05, w, 0.3, [f"단위: {unit}"], 11, ctx.c["muted"], align=PP_ALIGN.RIGHT)
        _table(ctx, slide, x, y + 0.3, w, h - 0.3, part, body, heat, has_total, spec)


def _border(cell, side, color, pt):
    """Cell edge line. Must precede the fill element inside a:tcPr."""
    tcPr = cell._tc.get_or_add_tcPr()
    ln = etree.Element(qn(f"a:ln{side}"), w=str(int(Pt(pt))))
    sf = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr"), val=color)
    order = ["L", "R", "T", "B"]
    pos = sum(1 for ch in tcPr if ch.tag in {qn(f"a:ln{o}") for o in order[:order.index(side)]})
    tcPr.insert(pos, ln)


def _table(ctx, slide, x, y, w, h, part, body, heat, has_total, spec, pct_cols=()):
    c = ctx.c
    public = ctx.tone["name"] == "public"
    nr, nc = len(part) + 1, len(part.columns) + 1
    rh = min(0.55 if nr <= 7 else 0.42, h / nr)  # short tables get roomier rows
    first_w = min(2.2, w * 0.24)
    gt = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(rh * nr))
    ctx.tables += 1
    tb = gt.table
    tb.horz_banding = tb.first_row = False
    tb.columns[0].width = Inches(first_w)
    for j in range(1, nc):
        tb.columns[j].width = Inches((w - first_w) / (nc - 1))
    numeric = body.drop(columns=["합계", *pct_cols], errors="ignore")
    vmin, vmax = float(numeric.min().min()), float(numeric.max().max())
    fmt = _numfmt(numeric.values.ravel(), {}, table=True)
    pt = 12 if nr <= 10 else 11
    header = [_label(ctx, spec, part.index.name or "")] + [_label(ctx, spec, col) for col in part.columns]
    head_fill, head_fg = {"dark": (c["dark"], "FFFFFF"), "accent": (c["accent"], "FFFFFF")}.get(
        "dark" if public else ctx.st["table_head"], (c["card"], c["ink"]))
    zebra = ctx.st["table_head"] != "card" and not heat

    def cell(i, j, val, fill, color, bold=False, align=PP_ALIGN.RIGHT):
        ce = tb.cell(i, j)
        ce.fill.solid()
        ce.fill.fore_color.rgb = rgb(fill)
        ce.margin_left = ce.margin_right = Inches(0.1)
        ce.margin_top = ce.margin_bottom = Inches(0.02)
        ce.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = ce.text_frame.paragraphs[0]
        p.alignment = align
        r = p.add_run()
        r.text = val
        r.font.size, r.font.bold, r.font.color.rgb = Pt(pt), bold, rgb(color)
        return ce

    for j, hv in enumerate(header):
        ce = cell(0, j, hv, head_fill, head_fg, True, PP_ALIGN.LEFT if j == 0 else PP_ALIGN.RIGHT)
        _border(ce, "B", c["ink"] if not public else head_fill, 1.25)
    for i, (idx, row) in enumerate(part.iterrows(), start=1):
        is_total = has_total and str(idx) == "합계"
        row_fill = mix(c["surface"], c["card"], 0.55) if zebra and i % 2 == 0 else c["surface"]
        ce = cell(i, 0, str(idx), c["card"] if is_total else row_fill, c["ink"], True, PP_ALIGN.LEFT)
        _border(ce, "B", c["line"], 0.75)
        if is_total:
            _border(ce, "T", c["ink"], 1)
        for j, (col, v) in enumerate(row.items(), start=1):
            fill, color = row_fill, c["ink"]
            if is_total or col == "합계":
                fill = c["card"]
            elif heat and vmax > vmin and col not in pct_cols:
                k = float((numeric.values.ravel() < float(v)).mean())  # percentile among the cells
                fill = mix(c["surface"], c["accent"], 0.08 + 0.72 * k)
                color = "FFFFFF" if k > 0.62 else c["ink"]
            val = ("-" if col in pct_cols else "") if pd.isna(v) else (f"{v:+.1f}%" if col in pct_cols else _fmt_num(v, fmt))
            ce = cell(i, j, val, fill, color, is_total or col == "합계")
            _border(ce, "B", c["line"], 0.75)
            if is_total:
                _border(ce, "T", c["ink"], 1)


def _drop_slides(prs, start):
    lst = prs.slides._sldIdLst
    for sid in list(lst)[start:]:
        prs.part.drop_rel(sid.rId)
        lst.remove(sid)


def p_waiting(ctx, spec, missing):
    """Placeholder for a slide whose data file is missing: the title stays, the body says what to supply."""
    slide, (x, y, w, h) = content_slide(ctx, {k: spec[k] for k in ("title", "eyebrow", "message") if k in spec})
    c = ctx.c
    b = box(slide, x, y, w, h, fill=c["surface"], line=c["muted"], radius=0.08)
    b.line.dash_style = MSO_LINE.DASH
    what = spec.get("chart") or spec["pattern"]
    text(ctx, slide, x, y + h / 2 - 0.55, w, 0.5, [f"데이터 대기: {missing}"], 20, c["ink"], True,
         align=PP_ALIGN.CENTER)
    text(ctx, slide, x, y + h / 2, w, 0.4, [f"{what} 장표에 쓸 데이터 파일을 넣고 다시 빌드하세요"], 14, c["muted"],
         align=PP_ALIGN.CENTER)
    ctx.warn(f"data file '{missing}' not found: drew a placeholder; add the file or replace `data:`")


PATTERNS = {
    "cover": p_cover, "agenda": p_agenda, "section": p_section, "key-message": p_key_message,
    "bullets-callout": p_bullets_callout, "exec-summary": p_exec_summary, "closing": p_closing,
    "compare": p_compare, "matrix-2x2": p_matrix, "process": p_process, "timeline": p_timeline,
    "kpi-tiles": p_kpi, "chart-takeaway": p_chart, "chart-table": p_chart_table, "chart-pair": p_chart_pair,
    "pivot-table": p_pivot, "heatmap-table": lambda c, s: p_pivot(c, s, heat=True),
}
COMMON = {"title", "pattern", "message", "source", "notes", "eyebrow", "labels"}
CHART_KEYS = {"chart", "data", "x", "y", "series", "where", "agg", "weight", "highlight", "top", "unit", "fmt", "values"}
KEYS = {
    "cover": {"subtitle", "date", "author"}, "agenda": {"items", "bullets"}, "section": {"number", "subtitle"},
    "key-message": {"statement", "support"}, "bullets-callout": {"bullets", "callout", "callout_title"},
    "exec-summary": {"points", "numbers"}, "closing": {"ask", "next", "support"},
    "compare": {"columns", "recommend"}, "matrix-2x2": {"quadrants", "x_axis", "y_axis", "items", "callout", "callout_title"},
    "process": {"steps", "highlight"}, "timeline": {"events"}, "kpi-tiles": {"kpis", "callout", "callout_title"},
    "chart-takeaway": CHART_KEYS | {"takeaways", "callout_title"}, "chart-table": CHART_KEYS | {"takeaways", "growth", "table_rows"},
    "chart-pair": {"charts", "data", "unit"},
    "pivot-table": {"data", "rows", "cols", "val", "agg", "weight", "top", "where", "unit", "max_rows"},
}
KEYS["heatmap-table"] = KEYS["pivot-table"]
# key present in a slide -> pattern, when `pattern:` is omitted
INFER = [("charts", "chart-pair"), ("growth", "chart-table"), ("chart", "chart-takeaway"), ("rows", "pivot-table"), ("kpis", "kpi-tiles"),
         ("ask", "closing"), ("steps", "process"), ("events", "timeline"), ("columns", "compare"),
         ("quadrants", "matrix-2x2"), ("points", "exec-summary"), ("statement", "key-message"), ("items", "agenda")]


# ---------- deck.md ----------

class _Yaml(yaml.SafeLoader):
    """YAML 1.1 reads on/off/yes/no (and 'y') as booleans; in a deck those are words, only true/false are not."""


_Yaml.yaml_implicit_resolvers = {k: [r for r in v if r[0] != "tag:yaml.org,2002:bool"]
                                 for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
_Yaml.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
                            list("tTfF"))


def parse(md: str):
    meta = {}
    if md.lstrip().startswith("---"):
        _, fm, md = md.lstrip().split("---", 2)
        meta = yaml.load(fm, Loader=_Yaml) or {}
    slides = []
    for block in re.split(r"(?m)^# ", md)[1:]:
        title, _, body = block.partition("\n")
        spec = yaml.load(body, Loader=_Yaml) if body.strip() else {}
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
        bp = base / brief
        brief = (yaml.safe_load(bp.read_text(encoding="utf-8")) or {}) if bp.exists() else {}
    if meta.get("storyline") and not brief.get("storyline"):
        brief = {**brief, "storyline": meta["storyline"]}
    design = meta.get("design") or t
    if design:
        brief = {**brief, "design": design}
    return persona.resolve_tone(brief)[0]


def _split_values(v, found=None):
    """`{value: 2,400억 원}` parses as {value: 2, '400억 원': None}: keys with None values betray the split."""
    found = [] if found is None else found
    if isinstance(v, dict):
        found += [k for k, x in v.items() if x is None and k not in ("pattern",)]
        for x in v.values():
            _split_values(x, found)
    elif isinstance(v, list):
        for x in v:
            _split_values(x, found)
    return found


def lint(ctx, spec):
    d, voice = ctx.tone["density"], ctx.tone.get("voice")
    if "TODO" in yaml.safe_dump(spec, allow_unicode=True):
        ctx.warn("TODO left from `pptkit plan`: fill it from the user's answers or delete the slide")
    unknown = set(spec) - COMMON - KEYS.get(spec["pattern"], set())
    if unknown:
        ctx.warn(f"unknown key(s) {sorted(unknown)} for {spec['pattern']} (ignored). see deck-spec.md")
    if spec["pattern"] not in ("cover", "section", "closing", "key-message") and \
            text_width(spec["title"], ctx.ty["title"]) > (W - 2 * MX) * 1.8:
        ctx.warn(f"title needs 3 lines ({len(spec['title'])}자): shorten it, move detail into `message:`")
    figs = [bool(isinstance(i, dict) and i.get("figure")) for i in spec.get("pillars", [])]
    if any(figs) and not all(figs):
        ctx.warn("pillars: give every card a `figure` or none (mixed 01/02 numbering and figures look uneven)")
    split = _split_values(spec)
    if split:
        ctx.warn(f"value(s) split at a comma by YAML near {split[:3]}: quote them, e.g. value: \"2,400억 원\"")
    if spec["pattern"] == "closing" and spec.get("ask") and len(spec["title"]) > 24 and not spec.get("eyebrow"):
        ctx.warn("closing: the headline is `ask`; a long `# title` is not shown. Use a short label like "
                 "`# 요청 사항` (shown above the ask) or move the sentence into `support`")
    for key in ("bullets", "callout", "takeaways", "points"):
        items = spec.get(key)
        if key == "points" and spec["pattern"] == "big-number":
            continue  # {title, desc} cards by design
        if not isinstance(items, list):
            continue
        odd = [i for i, v in enumerate(items, 1) if not isinstance(v, (str, int, float))]
        if odd:
            ctx.warn(f"{key} item(s) {odd} parsed as structured YAML: quote the sentence")
        if len(items) > d["max_bullets"]:
            ctx.warn(f"{key} {len(items)}>{d['max_bullets']} items")
        long = [i for i in map(_s, items) if len(i) > d["max_chars"]]
        if long:  # name the items so the author can fix them without counting
            ctx.warn(f"{key} {len(long)} item(s) >{d['max_chars']}자: " + "; ".join(f"'{i[:14]}…' {len(i)}자" for i in long[:3]))
        if voice == "gaejosik":
            bad = [i for i in map(_s, items) if re.search(r"(다|(어|아|해|에|예|세|지|네|게|래|까|죠)요)[.!]?$", i.strip())]
            if bad:
                ctx.warn(f"{key} voice: {len(bad)} item(s) end with ~다/~요, use ~함/~임")


def build(md_path, out=None, sample=False, design=None):
    md_path = Path(md_path)
    meta, slides = parse(md_path.read_text(encoding="utf-8"))
    if design:
        meta["design"] = design
    base = md_path.parent
    tone = load_tone(meta, base)
    from . import numvars
    values, missing, raw = (numvars.resolve(meta, base) if meta.get("vars") else {}), set(), slides
    slides = [numvars.substitute(s_, values, missing) for s_ in slides]  # $name -> the computed figure
    every = slides
    if sample:  # tone check: cover + first data-bearing (or first content) slide
        rest = [s for s in slides if s["pattern"] not in ("cover", "section")]
        pick = next((s for s in rest if "chart" in s or "charts" in s or "rows" in s),
                    next((s for s in rest if _has_data(s)), rest[0] if rest else None))
        slides = [s for s in slides if s["pattern"] == "cover"][:1] + ([pick] if pick else [])
    ctx = Ctx(new_deck(tone), tone, meta, base)
    ctx.sections = [s["title"] for s in slides if s["pattern"] == "section"]
    for spec in slides:
        fn = PATTERNS.get(spec["pattern"])
        if not fn:
            raise SystemExit(f"unknown pattern '{spec['pattern']}' on '{spec['title']}'. known: {', '.join(PATTERNS)}")
        first_page = ctx.page + 1
        ctx.body = None
        try:
            fn(ctx, spec)
        except FileNotFoundError as e:  # a data file not there yet: keep the slide as a placeholder, keep building
            _drop_slides(ctx.prs, first_page - 1)
            ctx.page = first_page - 1
            p_waiting(ctx, spec, Path(e.filename or "?").name)
        if ctx.body and ctx.body[0] is ctx.prs.slides[-1]:
            balance(ctx)
        for sl in list(ctx.prs.slides)[first_page - 1:]:  # template layouts may carry unused placeholders
            for ph in list(sl.placeholders):
                if ph.has_text_frame and not ph.text_frame.text.strip():
                    ph._element.getparent().remove(ph._element)
        saved, ctx.page = ctx.page, first_page
        lint(ctx, spec)
        ctx.page = saved
    if sample:  # the slides not drawn still get their content checks, numbered as in deck.md
        saved = ctx.page
        for i, spec in enumerate(every, start=1):
            if not any(spec is t for t in slides):
                ctx.page = i
                lint(ctx, spec)
        ctx.page = saved
    for name in sorted(missing):
        ctx.warnings.append(f"${name} is not defined under `vars:` (left as typed)")
    out = Path(out or md_path.with_suffix(".sample.pptx" if sample else ".pptx"))
    ctx.prs.save(out)
    head = f"OK {ctx.page} slides, {ctx.charts} charts, {ctx.tables} tables, design={tone['name']} -> {out}"
    want = tone.get("length")
    if want and not sample and abs(int(want) - ctx.page) >= 1:
        head += f"\nNOTE {ctx.page} slides; the brief asked for {want}: add or drop a slide, or update `length`"
    drafts = [i + 1 for i, s in enumerate(slides) if s["pattern"] != "cover" and re.search(  # a figure marked as made up
        r"\d[^\n]{0,15}\((예시|가정)\)|\((예시|가정)\)[^\n]{0,15}\d", yaml.safe_dump(s, allow_unicode=True))]
    if drafts:  # invented figures must not reach an audience unconfirmed
        head += f"\nNOTE (예시)/(가정) figures on slide(s) {drafts}: tell the user to replace or confirm them before use"
    moved = numvars.changes(md_path, values, raw, save=not sample) if values else []
    return "\n".join([head] + moved + [f"WARN {w}" for w in ctx.warnings])


from . import patterns_p1  # noqa: E402,F401  (registers the P1 patterns)
from . import patterns_pitch  # noqa: E402,F401  (registers the pitch patterns)
from . import patterns_report  # noqa: E402,F401  (registers report visuals)
