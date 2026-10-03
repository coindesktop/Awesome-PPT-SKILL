"""Geometry + text-fit checks that print failures only. No rendering, no images."""
import re

from pptx import Presentation
from pptx.util import Emu

from .render import text_height

PLACEHOLDER = re.compile(r"lorem|ipsum|\bTODO\b|\[insert|x{3,}|클릭하여", re.I)


def _in(v):
    return Emu(v).inches


def check(path) -> list[str]:
    prs = Presentation(path)
    sw, sh = _in(prs.slide_width), _in(prs.slide_height)
    issues = []
    for n, slide in enumerate(prs.slides, start=1):
        boxes = []
        for s in slide.shapes:
            if s.width is None:
                continue
            x, y, w, h = _in(s.left), _in(s.top), _in(s.width), _in(s.height)
            label = (s.text_frame.text.strip()[:14] if s.has_text_frame else s.shape_type and str(s.name))
            if s.rotation == 0 and (x < -0.01 or y < -0.01 or x + w > sw + 0.01 or y + h > sh + 0.01):
                issues.append(f"S{n} off-slide '{label}'")
            if not s.has_text_frame:
                continue
            txt = s.text_frame.text
            if s.is_placeholder and not txt.strip():
                issues.append(f"S{n} empty placeholder '{s.name}'")
            if PLACEHOLDER.search(txt):
                issues.append(f"S{n} placeholder text '{label}'")
            paras = [p.text for p in s.text_frame.paragraphs if p.text.strip()]
            sizes = [r.font.size.pt for p in s.text_frame.paragraphs for r in p.runs if r.font.size]
            if paras and s.rotation == 0:
                sa = s.text_frame.paragraphs[0].space_after
                need = text_height(paras, w - (0.22 if _bulleted(s) else 0), max(sizes) if sizes else 18,
                                   gap_pt=sa.pt if sa is not None else 4)
                if need > h + 0.05:
                    issues.append(f"S{n} overflow '{label}' needs {need:.2f}in > {h:.2f}in")
                boxes.append((x, y, w, h, label))
        for i, a in enumerate(boxes):  # partial overlap between text boxes; containment is intended layering
            for b in boxes[i + 1:]:
                ix = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
                iy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
                if ix > 0.02 and iy > 0.02 and not (_contains(a, b) or _contains(b, a)):
                    issues.append(f"S{n} overlap '{a[4]}' x '{b[4]}' {ix * iy:.2f}in2")
    return issues


def _contains(a, b):
    return a[0] <= b[0] + 0.01 and a[1] <= b[1] + 0.01 and a[0] + a[2] >= b[0] + b[2] - 0.01 and a[1] + a[3] >= b[1] + b[3] - 0.01


def _bulleted(s):
    return any(p._p.pPr is not None and p._p.pPr.find(
        "{http://schemas.openxmlformats.org/drawingml/2006/main}buChar") is not None for p in s.text_frame.paragraphs)
