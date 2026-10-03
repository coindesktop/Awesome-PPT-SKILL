# deck.md

```markdown
---
brief: brief.yaml            # design/voice/density come from profile x brief (or set design: forest)
source: "통계청 KOSIS, 2026"   # footer on data slides, without "자료:"/"출처:" (the design adds it)
date: 2026-10-03
author: 사업기획팀
eyebrow: 사업본부 월간 보고    # label above titles until the first section slide
labels: {region: 지역, revenue_100m_krw: 매출}   # display names for data columns
---

# Slide title = conclusion sentence
key: value                   # YAML body; `pattern:` optional (inferred from keys)
```

Each `# ` line starts a slide. Body is YAML. A bare list body means `bullets`. Quote any sentence that contains
`: ` or starts with `{`/`[` (build warns when an item parsed as structure). Optional keys on any content
slide: `message:` (governing line under the title), `eyebrow:`, `source:`, `notes:` (speaker notes). Data
paths are relative to deck.md. Unknown keys and overlong text produce `WARN` lines.

| pattern | keys (inferred by) | notes |
|---|---|---|
| `cover` | `subtitle`, `date`, `author` | must set `pattern: cover` |
| `agenda` | `items: [..]` | ≤10 |
| `section` | `number: 1`, `subtitle` | must set `pattern: section`; becomes the eyebrow of later slides |
| `exec-summary` | `points: [..]`, `numbers: [{value, label}]` ≤3 | |
| `key-message` | `statement`, `support` | |
| `bullets-callout` | `bullets: [..]`, `callout: [..]`, `callout_title` | default pattern |
| `compare` | `columns: [{title, items: [..]}]`, `recommend: 2` (1-based) | 2-3 columns |
| `matrix-2x2` | `quadrants: [TL, TR, BL, BR]`, `x_axis`, `y_axis`, `items: [{label, x, y}]` 0..1, `callout` | |
| `process` | `steps: [{title, desc}]`, `highlight: 3` | 3-5 steps |
| `timeline` | `events: [{when, label, now: true}]` | 4-7 events |
| `kpi-tiles` | `kpis: [{label, value, delta, good: down, note}]`, `callout`, `callout_title` | delta "-0.2%p" → ▼ |
| `chart-takeaway` | chart keys + `takeaways: [..]` | |
| `chart-table` | chart keys + `growth: true`, `takeaways` | chart left, same numbers as a table right |
| `chart-pair` | `charts: [{subtitle, chart keys}, {...}]`, shared `data`/`unit` | two views side by side; % charts keep `%` |
| `pivot-table` | `data`, `rows`, `cols`, `val`, `agg`, `weight`, `top`, `where`, `unit`, `max_rows` | totals + 기타 for sum |
| `heatmap-table` | same as pivot-table | needs `pattern: heatmap-table` |
| `closing` | `ask`, `support`, `next: [{t, who, when}]` | headline is `ask`; write a short `# 요청 사항` label (shown above it) |
| `two-column` | `columns: [{title, items}, {title, items}]` | must set `pattern: two-column` (else `compare`) |
| `before-after` | `before: {title, items}`, `after: {title, items}` | |
| `problem-solution` | `problems: [..]`, `solutions: [..]`, `problem_title`, `solution_title` | |
| `compare-table` | `options: [A, B, C]`, `criteria: [{label, values: [..]}]`, `recommend: 3`, `corner` | values: ●/◐/○ or short text |
| `swot` | `swot: {S: [..], W: [..], O: [..], T: [..]}` | |
| `logic-tree` | `root`, `branches: [{label, leaves: [..]}]` | issue tree / cause breakdown |
| `roadmap` | `phases: [..]`, `lanes: [{name, cells: [..]}]`, `now: 1` | phases × workstreams |
| `gantt` | `tasks: [{name, start, end, owner}]` or `data:` csv with those columns | dates `2026-10-01`; must set `pattern: gantt` with data |
| `funnel` | `stages: [{label, value}]`, `callout` | conversion % computed |
| `big-number` | `figure`, `label`, `support` | one headline number |
| `market-size` | `tam/sam/som: {value, label}` | |

## Chart keys

`chart`, `data`, `x`, `y`, `series` (long data → one series per value), `where: {year: 2026}`,
`agg` (sum | mean | count | wmean), `weight` (for wmean), `highlight`, `top`, `unit`, `fmt: pct`.

| chart | use | notes |
|---|---|---|
| `column-trend` | change over ≤12 periods | `highlight: 2026` = one accent, rest gray |
| `line-trend` | longer series or several series | last point labeled |
| `bar-ranked` | ranking categories | `top: 10`, `highlight: 서울` |
| `stacked` | totals with composition | needs `series` |
| `stacked-share` | composition in % | needs `series`; shares computed for you |

Callout boxes are headed `시사점` (report voices) or `핵심` (friendly); set `callout_title` per slide.
`stacked-share` and `fmt: pct` charts show `단위: %` unless they set their own `unit`. Body content that is
shorter than the slide is moved down to balance the space; `qa` reports `sparse` when half the body is still empty.

Rules baked in: no dual axis (two measures → `chart-pair` or `kpi-tiles`), one accent color for single-series
charts, values labeled, recessive axes and grid.

## Designs

`pptkit design` lists looks: `executive` (경영 보고), `signal` (전략·IR), `forest` (고객 제안, friendly),
`public` (공공 보고). A user's own DESIGN.md in `~/.pptkit/designs/<name>.md` (same front-matter tokens as
`pptkit/designs/executive.md`) is picked up automatically.
