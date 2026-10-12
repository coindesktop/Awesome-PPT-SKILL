"""`pptkit spec [names]`: the slice of references/deck-spec.md a deck needs, instead of the whole file."""
import re
from pathlib import Path

CHARTY = {"chart-takeaway", "chart-table", "chart-pair", "traction"}


def _doc():
    here = Path(__file__).parent
    for p in (here / "skill" / "references" / "deck-spec.md",
              here.parent / ".claude" / "skills" / "ppt" / "references" / "deck-spec.md"):
        if p.exists():
            return p.read_text(encoding="utf-8")
    raise SystemExit("deck-spec.md not found (reinstall pptkit)")


def _rows(doc):
    """name -> (table header, row) for every `| `name` | ... |` line."""
    out, head = {}, None
    for line in doc.splitlines():
        if line.startswith("| ") and not line.startswith("| `") and not line.startswith("|---"):
            head = line
        m = re.match(r"\| `([\w-]+)` \|", line)
        if m:
            out[m[1]] = (head, line)
    return out


def _section(doc, start, stop):
    i = doc.find(start)
    j = doc.find(stop, i + len(start)) if i >= 0 else -1
    return doc[i:j].strip() if i >= 0 else ""


def report(names):
    doc = _doc()
    rows = _rows(doc)
    if not names:
        intro = doc[:doc.find("| pattern |")].strip()
        pats = [n for n, (h, _) in rows.items() if h.startswith("| pattern")]
        charts = [n for n, (h, _) in rows.items() if h.startswith("| chart")]
        return "\n".join([intro, "", "patterns: " + ", ".join(pats), "charts: " + ", ".join(charts),
                          "`pptkit spec <name> ..` prints the keys of the ones you use."])
    unknown = [n for n in names if n not in rows]
    if unknown:
        raise SystemExit(f"unknown {unknown}. `pptkit spec` lists the names")
    lines, groups = [], {}
    for n in dict.fromkeys(names):
        groups.setdefault(rows[n][0], []).append(rows[n][1])
    for head, rs in groups.items():
        lines += ["", head, "|---|---|---|", *rs]
    if any(n in CHARTY or rows[n][0].startswith("| chart") for n in names):
        lines += ["", _section(doc, "## Chart keys", "| chart |")]
    if any(n in ("waterfall", "donut") or n in CHARTY for n in names):
        lines += ["", _section(doc, "Numbers the user typed", "## Chart keys")]
    return "\n".join(lines).strip()
