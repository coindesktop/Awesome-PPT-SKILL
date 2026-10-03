---
name: ppt
description: >-
  Build or revise PowerPoint decks tailored to who the user is and what they are making, with native
  (editable) charts and pivot tables from CSV/XLSX, at minimal token cost via the prebuilt `pptkit` CLI.
  Use whenever the user wants a PPT, 피피티, PPT 만들어줘, 장표, 발표자료, 보고 자료, 보고서 슬라이드, 덱,
  제안서, IR/피치덱, 교육 자료, presentation, slides, or wants charts, 피벗, 통계, KPI put into slides, or wants
  to fix/update an existing .pptx (숫자 바꿔줘, 겹친 거 정리, 장표 수정), even if no file format is named.
  Prefer this over hand-writing python-pptx or pptxgenjs code.
---

# ppt

`pptkit` renders and edits everything. **You only write small text files: `brief.yaml`, `deck.md`, or a
patch `ops.yaml`.** Never write Python/JS to draw slides or compute numbers, never unzip slide XML, never print
raw data files. Every pptkit command prints a short result written for you; act on it. If pptkit cannot do
something, say so plainly instead of coding around it.

If `pptkit` is missing: `uv tool install git+https://github.com/coindesktop/Awesome-PPT-SKILL`
(or `pip install -e <repo>`), then `pptkit install-skill`.

## New deck (personalize first, then build)

1. **Who** - `pptkit profile`. `PROFILE OK` → ask nothing. `PROFILE MISSING` → infer each field from the
   request first; ask only what you cannot infer. `ASSUME` fields are never asked: use them, mention them in one
   line. Save with `pptkit profile set role=.. industry=.. org_culture=.. audiences=a,b brand=none`.
   If the user has an old deck they like, `pptkit style extract old.pptx` learns its colors, fonts, density and
   voice (and uses it as the template when it is 16:9) → then `pptkit profile set design=<name> org_culture=..`.
2. **What** - write `brief.yaml` in the work folder:
   ```yaml
   purpose: report        # report | proposal | pitch | ir | sales | education | review
   audience: 사업본부장
   ask: 영업 인력 2명 증원 승인   # what the audience must decide/do after this deck
   mode: balanced         # present | balanced | handout
   formality: formal      # formal | neutral | friendly ("딱딱하지 않게", "친근하게" → friendly)
   length: 8
   # design: forest       # optional override; `pptkit design` lists them
   ```
   `ask` and `mode` drive quality most. If you cannot infer them, ask (bundle with step 1 questions).
3. **Tone** - `pptkit tone --brief brief.yaml`. It picks a DESIGN (look) and prints `VOICE` and `RULES`;
   obey them in every sentence you write. A `BRIEF MISSING` block means ask first.
4. **Data** - `pptkit data <file>` for a summary (KOSIS-style downloads are normalized automatically).
   For numbers in your messages use `pptkit pivot <file> --rows .. --cols .. --val ..`; weighted averages
   (e.g. revenue-weighted margin) use `--agg wmean --weight <col>`.
5. **Deck** - write `deck.md` per [references/deck-spec.md](references/deck-spec.md). Titles are conclusion
   sentences backed by numbers you got from pptkit. Pick patterns by the order below and vary them; when a
   slide holds one chart, prefer `chart-table` or `chart-pair` if a second view adds information.
6. **Tone sample** - `pptkit build deck.md --sample` → give the user `deck.sample.pptx` (cover + one data
   slide) and ask if the look and voice fit. Compare looks with `--design <name>`. Lasting preferences go to
   `pptkit profile set ...` (e.g. `design=forest`, `brand=0B5E7A`, `dislikes=..`); deck-only ones to `brief.yaml`.
7. **Build** - `pptkit build deck.md`. Fix every `WARN` by editing deck.md, rebuild, then
   `pptkit qa deck.pptx` until it prints `OK` (on Windows with PowerPoint, `--com` measures text exactly).
8. **Deliver** the .pptx path (in a cloud/app session, send the file).

## Edit an existing deck (any .pptx, ours or not)

A pptkit deck: change `deck.md` and rebuild. Any other deck: `pptkit map deck.pptx` (one line per slide with
shape ids, qa warnings and `read=L1|L2|L3`) → `pptkit read deck.pptx -s 3,5 -l <that level>` for only the slides
you will touch → write `ops.yaml` → `pptkit patch deck.pptx ops.yaml` (keeps formatting, saves a `.bak` once,
re-checks only touched slides). Syntax: [references/editing.md](references/editing.md). After edits,
`pptkit map deck.pptx --changed` shows only what changed. Look at rendered images only if qa reports something
you cannot resolve from its message.

## Pattern selection order

1. sequence → `process` (dates → `timeline`, task bars → `gantt`, phases × workstreams → `roadmap`)
2. alternatives → `compare` (many criteria → `compare-table`), change → `before-after` / `problem-solution`
3. two-axis judgment → `matrix-2x2`; internal/external analysis → `swot`; causes → `logic-tree`
4. data file → time series `chart-takeaway`/`chart-table`, composition `chart: stacked-share`,
   category × category `heatmap-table`/`pivot-table`, two related views `chart-pair`, conversion → `funnel`
5. 3-4 headline numbers → `kpi-tiles`; one number → `big-number`; market → `market-size`
6. one sentence → `key-message` 7. otherwise `bullets-callout` (two lists → `two-column`)
Structure: `cover`, `agenda`, `section` (sets the eyebrow of following slides), `exec-summary`, `closing`.

Default orders by purpose - report: cover, exec-summary, data slides, closing. proposal: cover,
problem-solution, compare-table, roadmap/timeline, closing. pitch: cover, problem-solution, market-size,
kpi-tiles or funnel, roadmap, closing.

## Numbers you did not compute

Only put numbers on slides that come from the user's files or from pptkit (`data`, `pivot`, `fetch`). Never
fill a chart with figures from memory or loose web snippets: they differ run to run. Public statistics:
`pptkit fetch wb <indicator> --country KOR,JPN --years 2021-2025` needs no key (World Bank); if it reports the
network is unreachable, ask the user to download the table as CSV (KOSIS, e-나라지표, 한국은행) and use
`pptkit data`. KOSIS API needs the user's own key: they run `pptkit key set kosis` themselves; never ask for a
key in chat. `fetch` writes provenance that becomes the slide footnote; mark provisional years "(잠정)".
