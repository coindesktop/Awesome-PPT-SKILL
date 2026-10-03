# deck.md

```markdown
---
brief: brief.yaml            # or tone: corporate-clean | tone.yaml
source: "통계청 KOSIS, 2026"   # footer on data slides (slide-level source: overrides)
date: 2026-10-03
author: 사업기획팀
labels: {region: 지역, revenue_100m_krw: 매출}   # display names for data columns
---

# Slide title = conclusion sentence
key: value                   # YAML body; `pattern:` optional (inferred from keys)
```

Each `# ` line starts a slide. Body is YAML. A bare list body means `bullets`. Common optional keys on any
content slide: `message:` (governing line under the title, kr-report frame), `source:`, `notes:` (speaker
notes). Data paths are relative to deck.md. Long text is auto-shrunk; if still too long, build prints WARN.

| pattern | keys (inferred by) | notes |
|---|---|---|
| `cover` | `subtitle`, `date`, `author` | must set `pattern: cover` |
| `agenda` | `items: [..]` | ≤10 |
| `section` | `number: 1` | must set `pattern: section` |
| `exec-summary` | `points: [..]`, `numbers: [{value, label}]` ≤3 | |
| `key-message` | `statement`, `support` | |
| `bullets-callout` | `bullets: [..]`, `callout: [..]`, `callout_title` | default pattern |
| `compare` | `columns: [{title, items: [..]}]`, `recommend: 2` (1-based) | 2-3 columns |
| `matrix-2x2` | `quadrants: [TL, TR, BL, BR]`, `x_axis`, `y_axis`, `items: [{label, x, y}]` 0..1, `callout` | |
| `process` | `steps: [{title, desc}]`, `highlight: 3` | 3-5 steps |
| `timeline` | `events: [{when, label, now: true}]` | 4-7 events |
| `kpi-tiles` | `kpis: [{label, value, delta, good: down, note}]`, `callout` | delta "-0.2%p" → ▼ |
| `chart-takeaway` | `chart`, `data`, `x`, `y`, `series`, `where`, `agg`, `highlight`, `top`, `unit`, `fmt: pct`, `takeaways` | see charts |
| `pivot-table` | `data`, `rows`, `cols`, `val`, `agg`, `top`, `where`, `unit`, `max_rows` | totals + 기타 for sum |
| `heatmap-table` | same as pivot-table | needs `pattern: heatmap-table` |

## Charts (`chart:`)

| id | use | data shape |
|---|---|---|
| `column-trend` | change over ≤12 periods | `x` time, `y` one column; `highlight: 2026` = one accent, rest gray |
| `line-trend` | longer series or several series | `series: channel` splits long data into lines; last point labeled |
| `bar-ranked` | ranking categories | `x` category, `top: 10`; `highlight: 서울` |

Rules baked in (do not fight them): one chart per slide, no dual axis (two measures → two slides or
`kpi-tiles`), one accent color, values labeled, axis/grid recessive. `where: {year: 2026}` filters rows;
`agg` is sum by default (mean/count also work; totals/기타 only for sum).
