# deck.md

```markdown
---
brief: brief.yaml            # design/voice/density come from profile x brief (or set design: forest)
storyline: pitch/vc-seed     # written by `pptkit plan <id> -o deck.md`
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
| `process` | `steps: [{title, desc, note}]`, `highlight: 3` | 3-5 steps; `note` = duration/output at the card bottom |
| `timeline` | `events: [{when, label, now: true}]` | 4-7 events |
| `kpi-tiles` | `kpis: [{label, value, delta, good: down, note, spark: [..]}]`, `callout`, `callout_title` | delta "-0.2%p" → ▼; spark = recent values |
| `chart-takeaway` | chart keys + `takeaways: [..]` | |
| `chart-table` | chart keys + `growth: true`, `takeaways` | chart left, same numbers as a table right |
| `chart-pair` | `charts: [{subtitle, chart keys}, {...}]`, shared `data`/`unit` | two views side by side; % charts keep `%` |
| `pivot-table` | `data`, `rows`, `cols`, `val`, `agg`, `weight`, `top`, `where`, `unit`, `max_rows` | totals + 기타 for sum |
| `heatmap-table` | same as pivot-table | needs `pattern: heatmap-table` |
| `closing` | `ask`, `support`, `next: [{t, who, when}]` | headline is `ask`; a short `# 요청 사항` is the label above it (`eyebrow:` replaces it) |
| `two-column` | `columns: [{title, items}, {title, items}]` | must set `pattern: two-column` (else `compare`) |
| `before-after` | `before: {title, items}`, `after: {title, items}` | |
| `problem-solution` | `problems: [..]`, `solutions: [..]`, `problem_title`, `solution_title` | |
| `compare-table` | `options: [A, B, C]`, `criteria: [{label, values: [..]}]`, `recommend: 3`, `corner` | values: ●/◐/○ or short text |
| `swot` | `swot: {S: [..], W: [..], O: [..], T: [..]}` | |
| `logic-tree` | `root`, `branches: [{label, leaves: [..]}]` | issue tree / cause breakdown |
| `roadmap` | `phases: [..]`, `lanes: [{name, cells: [..]}]`, `now: 1` | phases × workstreams |
| `gantt` | `tasks: [{name, start, end, owner, baseline_end}]` or `data:` csv, `asof` | dates `2026-10-01`; must set `pattern: gantt` with data; `asof` (default: deck `date`) draws the now line and colours done/live/next; `baseline_end` shows the planned end as an outline |
| `funnel` | `stages: [{label, value}]`, `callout` | conversion % computed |
| `big-number` | `figure`, `label`, `support`, `points: [{title, desc}]` ≤3 | one headline number; `points` explain it in cards on the right |
| `market-size` | `tam/sam/som: {value, label}` | |
| `pillars` | `pillars: [{title, desc, figure, note}]` 3-4 | strengths, reasons, why now; `figure` replaces 01/02; `note` = proof line |
| `traction` | `metrics: [{value, label}]` ≤4 + chart keys | headline numbers over a growth chart (`line-trend` default) |
| `team` | `members: [{name, role, bio: [..], note}]` ≤8, `advisors: [..]` | initials badge; `note` = why this person |
| `pricing` | `tiers: [{name, price, unit, for, features: [..], highlight: true, badge: 추천}]` ≤4 | `highlight` frames a tier, `badge` labels it; "별도 협의" prices drop the unit |
| `product-shot` | `features: [{title, desc}]` ≤4, `frame: phone`, `screen` | empty frame: the user pastes a screenshot |
| `progress` | `items: [{label, actual, target}]` or `data` + `x`, `actual`, `target`; `unit`, `callout` | must set `pattern: progress`; bars to 120%, 목표 marker, 달성/근접/미달 by rate (≥100%, ≥90%) |
| `status-table` | `rows: [{item, owner, due, status, note}]` or `data`; `columns`, `headers` | must set `pattern: status-table`; status green/amber/red/done (or 정상/주의/지연/완료) as dot + word, counts below |
| `funding-ask` | `amount`, `round`, `use: [{label, pct}]`, `milestones: [..]`, `milestones_title`, `use_title` | doughnut of use of funds; retitle for grants (`사업비 집행 계획`) |

Public data files: a World Bank download (`.zip` or its `API_*.csv`) reads as columns `Country Name`,
`Country Code`, `year`, `value` → chart keys `x: year, y: value, series: Country Name, where: {Country Code: [KOR, JPN, USA]}`;
`pptkit fetch wb` output has `country`, `iso3`, `year`, `value`. KOSIS downloads become long tables with a `year` column.

Numbers the user typed (no file) go inline: `values: {2026-01: 1.2, 2026-02: 1.6}` or
`values: {ARR: {...}, 고객사: {...}}` instead of `data`/`x`/`y`. Quote any value that contains a comma inside
`{...}` (`value: "2,400억 원"`): unquoted, YAML splits it and build warns.

## Chart keys

`chart`, `data`, `x`, `y`, `series` (long data → one series per value), `where: {year: 2026}`,
`agg` (sum | mean | count | wmean), `weight` (for wmean), `highlight` (a category, a list of them, or a series
name on multi-series charts: the rest go muted), `top`, `unit`, `fmt: pct`, `ymin` (axis start; line charts far
above zero start near the data automatically). Up to 8 series get distinct colours; more should fold into 기타.

| chart | use | notes |
|---|---|---|
| `column-trend` | change over ≤12 periods | `highlight: 2026` = one accent, rest gray |
| `line-trend` | longer series or several series | last point labeled |
| `bar-ranked` | ranking categories | `top: 10`, `highlight: 서울` |
| `stacked` | totals with composition | needs `series` |
| `stacked-share` | composition in % | needs `series`; shares computed for you |
| `waterfall` | start → changes → end (매출 증감 요인) | `values: {2025 매출: 1174, 서울: 45, 감소 요인: -3, 2026 매출: "="}`; `"="` draws the running total; or `data`/`x`/`y` deltas with `start: {label, value}`, `end: label`; axis starts near the data (`zero: true` to keep 0) |
| `donut` | composition of one total (≤6 parts) | `values` or `data`/`x`/`y`; `highlight` one part, `center`, `center_label` |

Icons: `icon: rocket` on `pillars` items, `process` steps, `kpi-tiles` tiles and `big-number` points draws a line icon
as an editable vector shape (no image). `pptkit icons [word]` lists the 136 names (Lucide, ISC licence). Use one icon
per item only when it adds meaning; never invent names (build warns and suggests the closest).

Callout boxes are headed `시사점` (report voices) or `핵심` (friendly); set `callout_title` per slide.
`stacked-share` and `fmt: pct` charts show `단위: %` unless they set their own `unit`. Body content that is
shorter than the slide is moved down to balance the space; `qa` reports `sparse` when half the body is still empty.

Rules baked in: no dual axis (two measures → `chart-pair` or `kpi-tiles`), one accent color for single-series
charts, values labeled, recessive axes and grid.

## Designs

`pptkit design` lists looks: `corporate` (기업 보고, 기본), `executive` (컨설팅형 보고), `signal` (전략·IR),
`forest` (고객 제안, friendly), `public` (공공 보고), `launch` (어두운 피칭), `bold` (밝은 피칭). A storyline sets a
default design. KPI tiles take `spark: [..]` (a small trend line); section slides list all sections automatically. A user's own DESIGN.md in `~/.pptkit/designs/<name>.md` (same front-matter tokens as
`pptkit/designs/executive.md`) is picked up automatically.
