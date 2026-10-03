"""Geometry + text-fit checks that print failures only. No rendering, no images.
On Windows with PowerPoint, check_com() replaces the text-fit estimate with PowerPoint's own measurement."""
import re
import subprocess
import sys
import tempfile

from pptx import Presentation
from pptx.util import Emu

from .render import bulleted, extent, text_height

PLACEHOLDER = re.compile(r"lorem|ipsum|\bTODO\b|\[insert|x{3,}|클릭하여", re.I)


def _in(v):
    return Emu(v).inches


def check(path, slides=None) -> list[str]:
    prs = Presentation(path)
    sw, sh = _in(prs.slide_width), _in(prs.slide_height)
    issues = []
    for n, slide in enumerate(prs.slides, start=1):
        if slides and n not in slides:
            continue
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
                boxes.append((x, y, w, h, label))
                if not sizes:  # inherited size is unknown here; guessing produces false alarms
                    continue
                tf = s.text_frame
                sa = tf.paragraphs[0].space_after
                need = text_height(paras, w - (0.22 if bulleted(s) else 0), max(sizes), gap_pt=sa.pt if sa is not None else 4,
                                   pad=_in((tf.margin_top or 0) + (tf.margin_bottom or 0)))
                if need > h + 0.05:
                    issues.append(f"S{n} overflow '{label}' needs {need:.2f}in > {h:.2f}in")
        sparse = _sparse(slide, sh)
        if sparse:
            issues.append(f"S{n} sparse: lower {sparse}% of the body is empty (add content, enlarge, or merge slides)")
        for i, a in enumerate(boxes):  # partial overlap between text boxes; containment is intended layering
            for b in boxes[i + 1:]:
                ix = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
                iy = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
                if ix > 0.02 and iy > 0.02 and not (_contains(a, b) or _contains(b, a)):
                    issues.append(f"S{n} overlap '{a[4]}' x '{b[4]}' {ix * iy:.2f}in2")
    return issues


def _sparse(slide, sh):
    """Percent of the body (below the title, above the footer band) left empty, if it is more than 40%."""
    title = slide.shapes.title
    if title is None or title.top is None or _in(title.top) > 1.6 or _in(title.height) > 1.6:
        return 0  # cover, section and closing slides are meant to be airy
    top, foot = _in(title.top + title.height), sh - 0.6
    body = [extent(s) for s in slide.shapes if s.shape_id != title.shape_id and s.top is not None
            and top - 0.05 <= _in(s.top) < foot]
    if not body:
        return 0
    empty = (foot - max(b for _, b in body)) / (foot - top)
    return round(empty * 100) if empty > 0.4 else 0


def _contains(a, b):
    return a[0] <= b[0] + 0.01 and a[1] <= b[1] + 0.01 and a[0] + a[2] >= b[0] + b[2] - 0.01 and a[1] + a[3] >= b[1] + b[3] - 0.01


# PowerPoint measures the real text height (installed fonts, real line breaking). Read-only, no window.
_PS = r"""
param([string]$path)
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$app = New-Object -ComObject PowerPoint.Application
$p = $app.Presentations.Open($path, -1, 0, 0)
foreach ($s in $p.Slides) {
  foreach ($sh in $s.Shapes) {
    if ($sh.HasTextFrame -and $sh.TextFrame2.HasText) {
      $tf = $sh.TextFrame2
      $need = $tf.TextRange.BoundHeight + $tf.MarginTop + $tf.MarginBottom
      if ($need -gt ($sh.Height + 2)) {
        $t = $tf.TextRange.Text
        $t = $t.Substring(0, [Math]::Min(14, $t.Length))
        "S{0} overflow '{1}' needs {2:N2}in > {3:N2}in (PowerPoint)" -f $s.SlideIndex, $t, ($need / 72), ($sh.Height / 72)
      }
    }
  }
}
$p.Close()
if ($app.Presentations.Count -eq 0) { $app.Quit() }
"""


def check_com(path, slides=None) -> list[str]:
    """Geometry checks from check() plus PowerPoint-measured overflow (Windows + PowerPoint only)."""
    if sys.platform != "win32":
        raise SystemExit("qa --com needs Windows with PowerPoint installed; plain `pptkit qa` works everywhere")
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False, encoding="utf-8-sig") as f:
        f.write(_PS)
    from pathlib import Path
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", f.name,
                        str(Path(path).resolve())], capture_output=True, text=True, encoding="utf-8", timeout=300)
    if r.returncode != 0:
        raise SystemExit("PowerPoint COM failed: " + r.stderr.strip()[-300:])
    com = [l for l in r.stdout.splitlines() if l.strip() and (not slides or int(l.split()[0][1:]) in slides)]
    return [i for i in check(path, slides) if " overflow " not in i] + com
