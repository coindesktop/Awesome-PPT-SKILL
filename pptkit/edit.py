"""Read and patch any .pptx with minimal tokens: map (one line per slide) -> read (only what is needed) -> patch."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import yaml
from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches

from . import data, qa


def _in(v):
    return round(Emu(v).inches, 2) if v is not None else None


def _kind(s):
    if s.has_chart:
        ch = s.chart
        return f"chart:{ch.chart_type.name.lower().split('_')[0]} {len(list(ch.plots[0].categories))}x{len(list(ch.plots[0].series))}"
    if s.has_table:
        return f"table {len(s.table.rows)}x{len(s.table.columns)}"
    if s.shape_type == MSO_SHAPE_TYPE.GROUP:
        return "group"
    if s.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return "picture"
    if s._element.tag == qn("p:graphicFrame"):
        return "object"  # SmartArt / OLE: text not reachable through python-pptx
    if s.has_text_frame and s.text_frame.text.strip():
        return "text"
    return "shape"


def _title(slide):
    t = slide.shapes.title
    if t is not None and t.text_frame.text.strip():
        return t.text_frame.text.strip()
    texts = [s.text_frame.text.strip() for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()]
    return texts[0] if texts else ""


def _short(t, n=28):
    t = " ".join(t.split())
    return t if len(t) <= n else t[:n - 1] + "…"


def _hash(slide):
    """Slide XML plus the parts it points to that edits change: chart data and speaker notes."""
    h = hashlib.md5(etree.tostring(slide._element))
    for s in slide.shapes:
        if getattr(s, "has_chart", False) and s.has_chart:
            h.update(etree.tostring(s.chart_part._element))
    if slide.has_notes_slide:
        h.update(slide.notes_slide.notes_text_frame.text.encode())
    return h.hexdigest()[:10]


def _map_cache(path):
    """Kept in ~/.pptkit/maps, not next to the deck."""
    from . import persona
    d = persona.home() / "maps"
    d.mkdir(parents=True, exist_ok=True)
    return d / (hashlib.md5(str(Path(path).resolve()).encode()).hexdigest()[:16] + ".json")


def deck_map(path, changed=False) -> str:
    """One line per slide plus the recommended read level. With changed=True only slides edited since last map."""
    prs = Presentation(path)
    cache = _map_cache(path)
    old = json.loads(cache.read_text()) if changed and cache.exists() else {}
    issues = qa.check(path)
    by_slide = {}
    for i in issues:
        n = int(i.split()[0][1:])
        by_slide.setdefault(n, []).append(i)
    lines, hashes = [], {}
    for n, slide in enumerate(prs.slides, start=1):
        h = hashes[str(n)] = _hash(slide)
        if changed and old.get(str(n)) == h:
            continue
        kinds = [(s.shape_id, _kind(s)) for s in slide.shapes]
        body = [f"#{sid} {k}" for sid, k in kinds if k != "shape"]
        shown = " ".join(body[:7]) + (f" +{len(body) - 7}" if len(body) > 7 else "")
        level = "L1"
        if any(k in ("object", "group") for _, k in kinds):
            level = "L3"
        elif by_slide.get(n):
            level = "L2"
        warn = f" | ⚠{len(by_slide[n])} qa" if by_slide.get(n) else ""
        notes = " | notes" if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip() else ""
        lines.append(f'S{n} "{_short(_title(slide))}" | {shown}{warn}{notes} | read={level}')
    cache.write_text(json.dumps(hashes))
    head = f"{Path(path).name}: {len(prs.slides)} slides" + (" (changed only)" if changed else "")
    return "\n".join([head] + (lines or ["no changes"]))


def _vals(vs, n=12):
    vs = list(vs)
    out = ", ".join("" if v is None else (f"{v:g}" if isinstance(v, float) else str(v)) for v in vs[:n])
    return out + (f", …(+{len(vs) - n})" if len(vs) > n else "")


def read(path, slides, level="L1", shapes=None) -> str:
    prs = Presentation(path)
    out = []
    for n in slides:
        slide = prs.slides[n - 1]
        out.append(f"== S{n}")
        for s in slide.shapes:
            if shapes and s.shape_id not in shapes:
                continue
            geo = f" @({_in(s.left)},{_in(s.top)},{_in(s.width)},{_in(s.height)})" if level != "L1" else ""
            if level == "L3":
                out.append(f"#{s.shape_id}{geo}\n" + etree.tostring(s._element, encoding="unicode")[:4000])
                continue
            if s.has_chart:
                p = s.chart.plots[0]
                out.append(f"#{s.shape_id} chart {s.chart.chart_type.name}{geo} cats=[{_vals(p.categories)}]")
                out += [f"   {ser.name}=[{_vals(ser.values)}]" for ser in p.series]
            elif s.has_table:
                out.append(f"#{s.shape_id} table{geo}")
                out += [f"   r{i}: " + " | ".join(c.text for c in r.cells) for i, r in enumerate(s.table.rows)][:16]
            elif s.has_text_frame and s.text_frame.text.strip():
                paras = [p.text for p in s.text_frame.paragraphs if p.text.strip()]
                size = next((r.font.size.pt for p in s.text_frame.paragraphs for r in p.runs if r.font.size), None)
                fmt = f" {size:g}pt" if level == "L2" and size else ""
                out.append(f"#{s.shape_id} text{geo}{fmt}: " + " / ".join(paras))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            out.append("notes: " + _short(slide.notes_slide.notes_text_frame.text, 200))
    return "\n".join(out)


# ---------- patch ----------

def _shape(slide, sid):
    for s in slide.shapes:
        if s.shape_id == sid:
            return s
    raise SystemExit(f"shape #{sid} not found (run pptkit map/read for ids)")


def _set_text(shape, paras):
    """Replace text but keep the first paragraph's and first run's formatting."""
    txBody = shape.text_frame._txBody
    ps = txBody.findall(qn("a:p"))
    p0 = ps[0]
    pPr = p0.find(qn("a:pPr"))
    r0 = p0.find(qn("a:r"))
    rPr = r0.find(qn("a:rPr")) if r0 is not None else None
    for p in ps:
        txBody.remove(p)
    for t in paras:
        p = etree.SubElement(txBody, qn("a:p"))
        if pPr is not None:
            p.append(copy.deepcopy(pPr))
        r = etree.SubElement(p, qn("a:r"))
        if rPr is not None:
            r.append(copy.deepcopy(rPr))
        etree.SubElement(r, qn("a:t")).text = str(t)


def _replace_all(prs, pairs):
    n = 0
    for slide in prs.slides:
        frames = [s.text_frame for s in slide.shapes if s.has_text_frame]
        frames += [c.text_frame for s in slide.shapes if s.has_table for r in s.table.rows for c in r.cells]
        for tf in frames:
            for p in tf.paragraphs:
                for r in p.runs:
                    for a, b in pairs.items():
                        if str(a) in r.text:
                            r.text, n = r.text.replace(str(a), str(b)), n + r.text.count(str(a))
    return n


def _fix_overlap(slide, sh_in):
    """Push the lower of each partially overlapping pair of text boxes below the upper one."""
    moved = []
    for _ in range(5):
        boxes = sorted([s for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip() and s.rotation == 0
                        and s.width is not None], key=lambda s: (s.top, s.left))
        hit = False
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                ra = (a.left, a.top, a.left + a.width, a.top + a.height)
                rb = (b.left, b.top, b.left + b.width, b.top + b.height)
                ix, iy = min(ra[2], rb[2]) - max(ra[0], rb[0]), min(ra[3], rb[3]) - max(ra[1], rb[1])
                contained = ra[0] <= rb[0] and ra[1] <= rb[1] and ra[2] >= rb[2] and ra[3] >= rb[3]
                if ix > Inches(0.02) and iy > Inches(0.02) and not contained:
                    new_top = a.top + a.height + Inches(0.1)
                    if new_top + b.height > Inches(sh_in - 0.3):  # no room below: shrink instead of leaving the slide
                        b.height = max(Inches(0.3), Inches(sh_in - 0.3) - new_top)
                    moved.append(f"#{b.shape_id}↓{_in(new_top - b.top)}in")
                    b.top = new_top
                    hit = True
                    break
            if hit:
                break
        if not hit:
            break
    return moved


def patch(path, ops_path, out=None) -> str:
    path, ops_path = Path(path), Path(ops_path)
    ops = yaml.safe_load(ops_path.read_text(encoding="utf-8")) or []
    prs = Presentation(path)
    sh_in = Emu(prs.slide_height).inches
    done, touched = [], set()
    for op in ops:
        n = op.get("slide")
        slide = prs.slides[n - 1] if n else None
        if "replace" in op:
            done.append(f"replace {_replace_all(prs, op['replace'])} hit(s)")
            touched.update(range(1, len(prs.slides) + 1))
            continue
        touched.add(n)
        if "stack" in op:
            ids = [_shape(slide, i) for i in op["stack"]]
            top, gap = ids[0].top, Inches(op.get("gap", 0.2))
            for s in ids:
                s.left, s.width, s.top = ids[0].left, ids[0].width, top
                top += s.height + gap
            done.append(f"S{n} stack " + " ".join(f"#{s.shape_id}" for s in ids))
        elif op.get("fix") == "overlap":
            done.append(f"S{n} fix overlap " + (", ".join(_fix_overlap(slide, sh_in)) or "none found"))
        elif "notes" in op:
            slide.notes_slide.notes_text_frame.text = str(op["notes"])
            done.append(f"S{n} notes")
        elif "delete" in op:
            s = _shape(slide, op["delete"])
            s._element.getparent().remove(s._element)
            done.append(f"S{n} delete #{op['delete']}")
        else:
            s = _shape(slide, op["shape"])
            if "text" in op or "paras" in op:
                _set_text(s, op.get("paras") or [op["text"]])
                done.append(f"S{n} text #{s.shape_id}")
            if "move" in op:
                for attr, v in zip(("left", "top", "width", "height"), op["move"]):
                    if v is not None:
                        setattr(s, attr, Inches(v))
                done.append(f"S{n} move #{s.shape_id}")
            if "cells" in op:
                for rc, v in op["cells"].items():
                    r, c = map(int, str(rc).split(","))
                    cell = s.table.cell(r, c)
                    _set_text(cell, [v]) if cell.text_frame.paragraphs[0].runs else setattr(cell, "text", str(v))
                done.append(f"S{n} cells #{s.shape_id} x{len(op['cells'])}")
            if "chart" in op:
                spec = op["chart"]
                cd = CategoryChartData()
                if "data" in spec:
                    df = data.load(ops_path.parent / spec["data"])
                    wide = data.aggregate(df, spec["x"], spec["y"], spec.get("series"), spec.get("agg", "sum"),
                                          spec.get("where"), spec.get("weight"))
                    if spec.get("last"):
                        wide = wide.tail(spec["last"])
                    cd.categories = [str(v) for v in wide.index]
                    for col in wide.columns:
                        cd.add_series(str(spec.get("labels", {}).get(col, col)),
                                      [None if pd.isna(v) else float(v) for v in wide[col]])
                else:
                    cd.categories = [str(c) for c in spec["categories"]]
                    for name, vals in spec["series"].items():
                        cd.add_series(str(name), vals)
                s.chart.replace_data(cd)
                done.append(f"S{n} chart #{s.shape_id} {len(cd.categories)} cats")
    out = Path(out or path)
    if out == path:
        bak = path.with_suffix(".bak.pptx")
        if not bak.exists():
            shutil.copy(path, bak)  # first in-place patch keeps the original
    prs.save(out)
    issues = qa.check(out, slides=touched)
    tail = "\n".join(issues) if issues else f"qa({','.join(f'S{t}' for t in sorted(touched))}) OK"
    return f"OK {len(ops)} op(s) -> {out}\n" + "\n".join(done) + "\n" + tail
