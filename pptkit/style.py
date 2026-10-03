"""Learn a personal look from decks the user already made: theme colors, fonts, density, voice -> DESIGN.md."""
import re
from collections import Counter
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.util import Emu

from . import persona
from .render import dark_color, mix

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
VOICE = {"gaejosik": r"(함|임|음|됨|필요|예정|추진|강화|검토|확대|완료)[.]?$", "formal": r"(니다|습니다)[.]?$",
         "spoken": r"(요|죠|해요|세요)[.!?]?$"}


def _theme(prs):
    root = etree.fromstring(prs.slide_master.part.part_related_by(RT.THEME).blob)
    colors = {}
    for el in root.find(f".//{A}clrScheme"):
        v = el.find(f"{A}srgbClr")
        sys_ = el.find(f"{A}sysClr")
        colors[el.tag.replace(A, "")] = (v.get("val") if v is not None else sys_.get("lastClr") if sys_ is not None else None)
    fonts = {k: (root.find(f".//{A}{k}/{A}ea").get("typeface") or root.find(f".//{A}{k}/{A}latin").get("typeface"))
             for k in ("majorFont", "minorFont")}
    return colors, fonts


def _saturated(h):
    from pptx.dml.color import RGBColor
    r, g, b = RGBColor.from_string(h)
    return max(r, g, b) - min(r, g, b) > 60


def extract(path, name=None):
    path = Path(path)
    prs = Presentation(path)
    w, h = Emu(prs.slide_width).inches, Emu(prs.slide_height).inches
    tcolors, tfonts = _theme(prs)
    fonts, fills, endings = Counter(), Counter(), Counter()
    chars, bullets, titles = [], [], []
    for owner in [prs.slide_master, *prs.slide_layouts]:  # brand marks usually live on the master
        for s in owner.shapes:
            try:
                if s.fill.type == 1:
                    fills[str(s.fill.fore_color.rgb)] += 10
            except Exception:
                pass
    for slide in prs.slides:
        n_chars = n_par = 0
        title = slide.shapes.title
        if title is not None and title.text_frame.text.strip():
            titles.append(len(title.text_frame.text.strip()))
        for s in slide.shapes:
            try:
                if s.fill.type == 1:
                    fills[str(s.fill.fore_color.rgb)] += 1
            except Exception:
                pass
            if not s.has_text_frame or (title is not None and s.shape_id == title.shape_id):
                continue
            for p in s.text_frame.paragraphs:
                t = p.text.strip()
                if not t:
                    continue
                n_par += 1
                n_chars += len(t)
                if len(t) >= 8:
                    endings[next((k for k, rx in VOICE.items() if re.search(rx, t)), "other")] += 1
                for r in p.runs:
                    rpr = r._r.find(f"{A}rPr")
                    ea = rpr.find(f"{A}ea") if rpr is not None else None
                    face = (ea.get("typeface") if ea is not None else None) or r.font.name
                    if face and not face.startswith("+"):
                        fonts[face] += len(r.text)
        chars.append(n_chars)
        bullets.append(n_par)
    accent = next((c for c, _ in fills.most_common() if _saturated(c)), None) or tcolors.get("accent1") or "2F54EB"
    ink = tcolors.get("dk1") or "141414"
    ink = ink if dark_color(ink) else "141414"
    dark = tcolors.get("dk2") if tcolors.get("dk2") and dark_color(tcolors["dk2"]) else mix(accent, "000000", 0.6)
    bg = tcolors.get("lt1") or "FFFFFF"
    font = fonts.most_common(1)[0][0] if fonts else (tfonts["minorFont"] or "맑은 고딕")
    total = sum(v for k, v in endings.items() if k != "other") or 1
    voice = max(("gaejosik", "formal", "spoken"), key=lambda k: endings[k]) if total > 1 else "gaejosik"
    avg_c = sum(chars) / max(len(chars), 1)
    mode = "handout" if avg_c > 260 else "present" if avg_c < 110 else "balanced"
    name = name or re.sub(r"[^a-z0-9-]+", "-", path.stem.lower()).strip("-") or "mine"
    widescreen = abs(w - 13.333) < 0.02 and abs(h - 7.5) < 0.02
    design = f"""---
name: {name}
description: {path.name}에서 추출한 개인 디자인. 강조색 {accent}, 폰트 {font}.
formality: neutral
use_for: [report, proposal, review]
{"template: " + str(path.resolve()) if widescreen else "# template: not used (only 13.33x7.5in widescreen decks can be templates)"}
colors:
  bg: "{bg}"
  dark: "{dark}"
  ink: "{ink}"
  body: "{mix(ink, 'FFFFFF', 0.25)}"
  muted: "{mix(ink, 'FFFFFF', 0.5)}"
  accent: "{accent}"
  card: "{mix(bg, accent, 0.06)}"
  line: "{mix(bg, accent, 0.2)}"
  neutral_series: "{mix(bg, ink, 0.22)}"
  positive: "0F8A5F"
  negative: "D93838"
series: ["{accent}", "EB6834", "1BAF7A", "EDA100"]
fonts: {{title: "{font}", body: "{font}"}}
type: {{cover: 40, title: 26, eyebrow: 12, message: 15, body: 15, metric: 36, small: 10}}
shape: {{radius: 0.08, border_pt: 1}}
cover: {{bg: light, decor: none}}
section: dark
closing: dark
bullet: "•"
---

# {name}

`pptkit style extract {path.name}`로 만든 디자인이다. 값은 자유롭게 고쳐도 된다.
차트 계열 색(series)의 첫 색은 브랜드 강조색이다. 나머지는 검증된 기본 팔레트다.
"""
    out = persona.home() / "designs" / f"{name}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(design, encoding="utf-8")
    top_fonts = ", ".join(f"{f}({v * 100 // max(sum(fonts.values()), 1)}%)" for f, v in fonts.most_common(2)) or tfonts["minorFont"]
    vshare = ", ".join(f"{k} {endings[k] * 100 // total}%" for k in ("gaejosik", "formal", "spoken") if endings[k])
    return "\n".join([
        f"STYLE {path.name}: {len(prs.slides)} slides {w:.2f}x{h:.2f}in | fonts {top_fonts} | accent {accent} dark {dark} ink {ink}",
        f"TEXT avg {avg_c:.0f} chars/slide, {sum(bullets) / max(len(bullets), 1):.1f} paras, title {sum(titles) / max(len(titles), 1):.0f}자"
        f" | voice {vshare or 'n/a'} -> mode≈{mode}",
        f"-> {out}" + (" (template linked)" if widescreen else " (not 16:9 widescreen: colors/fonts only)"),
        f"use: pptkit profile set design={name} org_culture={voice}",
    ])
