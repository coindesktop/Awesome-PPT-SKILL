"""Purpose -> storyline options -> deck.md skeleton + the content questions. The model relays, the user picks."""
from pathlib import Path

import yaml

HERE = Path(__file__).parent
CAT = yaml.safe_load((HERE / "storylines.yaml").read_text(encoding="utf-8"))

# Minimal body per pattern; every TODO must be replaced before build (build warns on leftovers).
SKELETON = {
    "cover": "pattern: cover\nsubtitle: TODO 한 줄 소개 (누구의 무슨 문제를 어떻게)",
    "big-number": "figure: TODO 숫자\nlabel: TODO 숫자가 뜻하는 것\nsupport: TODO 근거 한 문장",
    "key-message": "statement: TODO 한 문장\nsupport: TODO 근거",
    "pillars": "pillars:\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}",
    "problem-solution": "problems: [TODO, TODO]\nsolutions: [TODO, TODO]",
    "market-size": "tam: {value: TODO, label: TODO 정의}\nsam: {value: TODO, label: TODO}\nsom: {value: TODO, label: TODO}\n"
                   "source: TODO 근거 자료",
    "traction": "metrics:\n  - {value: TODO, label: TODO}\n  - {value: TODO, label: TODO}\n  - {value: TODO, label: TODO}\n"
                "chart: line-trend\ndata: TODO.csv\nx: TODO\ny: TODO",
    "pricing": "tiers:\n  - {name: TODO, price: TODO, unit: /월, features: [TODO]}\n"
               "  - {name: TODO, price: TODO, unit: /월, features: [TODO], highlight: true}",
    "compare-table": "options: [TODO 대안1, TODO 대안2, 우리]\ncriteria:\n  - {label: TODO, values: [○, ◐, ●]}\nrecommend: 3",
    "matrix-2x2": "x_axis: TODO\ny_axis: TODO\nquadrants: [TODO, TODO, TODO, TODO]\nitems:\n  - {label: 우리, x: 0.8, y: 0.8}",
    "team": "members:\n  - {name: TODO, role: TODO, bio: TODO 관련 이력}\n  - {name: TODO, role: TODO, bio: TODO}",
    "funding-ask": "amount: TODO 금액\nround: TODO 라운드\nuse:\n  - {label: TODO, pct: 50}\n  - {label: TODO, pct: 30}\n"
                   "  - {label: TODO, pct: 20}\nmilestones: [TODO 이 돈으로 달성할 것]",
    "product-shot": "features:\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}",
    "timeline": "events:\n  - {when: TODO, label: TODO}\n  - {when: TODO, label: TODO}\n  - {when: TODO, label: TODO, now: true}",
    "exec-summary": "points: [TODO, TODO, TODO]\nnumbers:\n  - {value: TODO, label: TODO}",
    "process": "steps:\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}\n  - {title: TODO, desc: TODO}",
    "roadmap": "phases: [TODO, TODO, TODO]\nlanes:\n  - {name: TODO, cells: [TODO, TODO, TODO]}\nnow: 1",
    "kpi-tiles": "kpis:\n  - {label: TODO, value: TODO}\n  - {label: TODO, value: TODO}\n  - {label: TODO, value: TODO}",
    "before-after": "before: {title: 도입 전, items: [TODO]}\nafter: {title: 도입 후, items: [TODO]}",
    "closing": "ask: TODO 청중에게 바라는 행동\nnext:\n  - {t: TODO, who: TODO, when: TODO}",
    "chart-table": "chart: column-trend\ndata: TODO.csv\nx: TODO\ny: TODO\ngrowth: true",
    "chart-pair": "data: TODO.csv\ncharts:\n  - {subtitle: TODO, chart: column-trend, x: TODO, y: TODO}\n"
                  "  - {subtitle: TODO, chart: stacked-share, x: TODO, y: TODO, series: TODO}",
    "heatmap-table": "pattern: heatmap-table\ndata: TODO.csv\nrows: TODO\ncols: TODO\nval: TODO",
    "bullets-callout": "bullets: [TODO, TODO, TODO]\ncallout: [TODO]",
    "logic-tree": "root: TODO 문제\nbranches:\n  - {label: TODO, leaves: [TODO]}\n  - {label: TODO, leaves: [TODO]}",
    "swot": "swot: {S: [TODO], W: [TODO], O: [TODO], T: [TODO]}",
    "agenda": "items: [TODO, TODO, TODO]",
    "compare": "columns:\n  - {title: TODO, items: [TODO]}\n  - {title: TODO, items: [TODO]}",
}


def report(arg=None) -> str:
    """No arg: purposes. A purpose: its storylines. A storyline id: the outline and questions."""
    if not arg:
        lines = ["ASK THE USER what the deck is for (skip if the request already says), then `pptkit plan <purpose>`:"]
        lines += [f"  {k:10} {v}" for k, v in CAT["purposes"].items()]
        return "\n".join(lines)
    if arg in CAT["purposes"]:
        opts = {k: v for k, v in CAT["storylines"].items() if k.startswith(arg + "/")}
        lines = [f"STORYLINES for {arg}. Show these to the user as choices (name + when + flow) and let them pick; "
                 "recommend one from what you know:"]
        for k, s in opts.items():
            flow = " → ".join(dict.fromkeys(sl[0] for sl in s["slides"]))
            lines.append(f"- {k} | {s['name']} | {s['length']}장 {s['mode']} | {s['when']}\n    {flow}")
        lines.append("then: `pptkit plan <id> -o deck.md`")
        return "\n".join(lines)
    s = _get(arg)
    qs = [sl[3] for sl in s["slides"] if sl[3]]
    return "\n".join([f"STORYLINE {arg}: {s['name']} · {s['length']}장 · mode={s['mode']}"
                      + (f" · design={s['design']}" if s.get("design") else ""),
                      "FLOW " + " → ".join(sl[0] for sl in s["slides"]),
                      "ASK THE USER in one message (skip what the request or files already answer; offer to draft "
                      "from what you know if they prefer):"] + [f"- {q}" for q in dict.fromkeys(qs)])


def _get(sid):
    if sid not in CAT["storylines"]:
        raise SystemExit(f"unknown storyline '{sid}'. `pptkit plan` lists purposes, `pptkit plan <purpose>` storylines")
    return CAT["storylines"][sid]


def skeleton(sid, brief="brief.yaml") -> str:
    """deck.md with one slide per storyline step: role as eyebrow, title hint, pattern keys with TODOs."""
    s = _get(sid)
    out = [f"---\nbrief: {brief}\nstoryline: {sid}\n---\n"]
    for role, pattern, hint, _ in s["slides"]:
        body = SKELETON.get(pattern, f"pattern: {pattern}")
        if not body.startswith("pattern:"):
            body = f"pattern: {pattern}\n" + body
        if pattern not in ("cover", "closing"):
            body += f"\neyebrow: {role}"  # the storyline step labels the slide (문제, 트랙션, 1. 문제 인식 ...)
        out.append(f"# TODO {hint}\n{body}\n")
    return "\n".join(out)
