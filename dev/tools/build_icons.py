"""Dev only: Lucide icon nodes -> pptkit/icons.json (polylines in a 24x24 box).

pptkit draws them as freeform shapes (vector, recolourable, no images). Run:
  PYTHONPATH=<dir with svgpathtools> python3 dev/tools/build_icons.py <lucide-static>/icon-nodes.json
Lucide is ISC licensed; the licence ships as pptkit/icons.LICENSE.
"""
import json
import math
import sys
from pathlib import Path

from svgpathtools import parse_path

NAMES = """users user user-check user-plus users-round contact id-card target goal flag milestone route compass trending-up
trending-down chart-column chart-line chart-pie gauge percent banknote wallet coins receipt circle-dollar-sign piggy-bank
hand-coins landmark scale shield-check lock key badge-check award star thumbs-up heart circle-check triangle-alert circle-x
clock timer hourglass calendar rocket lightbulb sparkles zap brain bot cpu code terminal settings wrench hammer puzzle
layers workflow git-branch refresh-cw recycle arrow-right search scan eye globe building factory store warehouse boxes
package truck forklift car plane ship shopping-cart smartphone monitor database server cloud wifi link share-2 download
upload file-text clipboard-check list-checks list-todo presentation briefcase handshake megaphone message-circle mail phone
bell headphones camera image video map-pin leaf sprout wheat tractor sun battery-charging plug hospital stethoscope pill
microscope flask-conical ruler pen-tool palette graduation-cap book-open school baby mic mic-vocal audio-lines
message-square clipboard-list notebook-pen user-round calendar-check chart-no-axes-combined hand-heart house""".split()


def flatten(d, step=0.6):
    """Every subpath of an SVG path as a list of points, curves sampled about every `step` units."""
    out = []
    for sub in parse_path(d).continuous_subpaths():
        pts = []
        for seg in sub:
            n = max(2, math.ceil(seg.length() / step)) if seg.length() > 0 else 2
            for k in range(0 if not pts else 1, n + 1):
                z = seg.point(k / n)
                pts.append([round(z.real, 2), round(z.imag, 2)])
        closed = abs(sub.start - sub.end) < 1e-6
        out.append({"p": pts, "z": closed})
    return out


def ellipse(cx, cy, rx, ry, n=36):
    return [{"p": [[round(cx + rx * math.cos(2 * math.pi * k / n), 2), round(cy + ry * math.sin(2 * math.pi * k / n), 2)]
                   for k in range(n)], "z": True}]


def node(tag, a):
    f = lambda k, v=0: float(a.get(k, v))
    if tag == "path":
        return flatten(a["d"])
    if tag == "circle":
        return ellipse(f("cx"), f("cy"), f("r"), f("r"))
    if tag == "ellipse":
        return ellipse(f("cx"), f("cy"), f("rx"), f("ry"))
    if tag == "line":
        return [{"p": [[f("x1"), f("y1")], [f("x2"), f("y2")]], "z": False}]
    if tag in ("polyline", "polygon"):
        nums = [float(v) for v in a["points"].replace(",", " ").split()]
        return [{"p": [nums[i:i + 2] for i in range(0, len(nums), 2)], "z": tag == "polygon"}]
    if tag == "rect":
        x, y, w, h = f("x"), f("y"), f("width"), f("height")
        r = min(f("rx", a.get("ry", 0)), w / 2, h / 2)
        if not r:
            return [{"p": [[x, y], [x + w, y], [x + w, y + h], [x, y + h]], "z": True}]
        d = (f"M{x + r} {y}H{x + w - r}A{r} {r} 0 0 1 {x + w} {y + r}V{y + h - r}A{r} {r} 0 0 1 {x + w - r} {y + h}"
             f"H{x + r}A{r} {r} 0 0 1 {x} {y + h - r}V{y + r}A{r} {r} 0 0 1 {x + r} {y}Z")
        return flatten(d)
    raise ValueError(tag)


def main(nodes_json):
    nodes = json.loads(Path(nodes_json).read_text())
    icons = {n: [c for tag, a in nodes[n] for c in node(tag, a)] for n in NAMES if n in nodes}
    out = Path(__file__).resolve().parents[2] / "pptkit" / "icons.json"
    out.write_text(json.dumps(icons, separators=(",", ":")))
    print(f"{len(icons)} icons -> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
