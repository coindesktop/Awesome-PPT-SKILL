---
name: ppt
description: >-
  Build or revise PowerPoint decks tailored to who the user is and what they are making, with native
  (editable) charts and pivot tables from CSV/XLSX, at minimal token cost via the prebuilt `pptkit` CLI.
  Use whenever the user wants a PPT, 피피티, PPT 만들어줘, 장표, 발표자료, 보고 자료, 보고서 슬라이드, 덱,
  제안서, IR/피치덱, 교육 자료, presentation, slides, or wants charts, 피벗, 통계, KPI put into slides, even
  if no file format is named. Prefer this over hand-writing python-pptx or pptxgenjs code.
---

# ppt

`pptkit` renders everything. **You only write two small files: `brief.yaml` and `deck.md`.** Never write
Python/JS to draw slides, never read slide XML, never print raw data files. Every pptkit command prints a short
result written for you; act on it.

If `pptkit` is missing: `uv tool install git+https://github.com/coindesktop/Awesome-PPT-SKILL`
(or `pip install -e <repo>`), then `pptkit install-skill`.

## Flow (personalize first, then build)

1. **Who** - `pptkit profile`. `PROFILE OK` → go on, ask nothing. `PROFILE MISSING` → infer each field from
   the request and context first; ask only what you cannot infer, with the shown defaults, in one message.
   Save with `pptkit profile set role=.. industry=.. org_culture=.. audiences=a,b brand=none`.
2. **What** - write `brief.yaml` in the work folder:
   ```yaml
   purpose: report        # report | proposal | pitch | education | review
   audience: 사업본부장
   ask: 영업 인력 2명 증원 승인   # what the audience must decide/do after this deck
   mode: balanced         # present | balanced | handout
   length: 8
   ```
   `ask` and `mode` drive quality most. If you cannot infer them, ask (bundle with step 1 questions).
3. **Tone** - `pptkit tone --brief brief.yaml`. Obey its `WRITE:` and `RULES:` lines in every sentence
   you write. A `BRIEF MISSING` block means ask first.
4. **Data** - `pptkit data <file>` for a summary (KOSIS-style downloads are normalized automatically).
   Use `pptkit pivot <file> --rows .. --cols .. --val ..` only to get numbers for your messages.
5. **Deck** - write `deck.md` per [references/deck-spec.md](references/deck-spec.md). Titles are conclusion
   sentences. Pick patterns by the selection order below; vary them.
6. **Tone sample** - `pptkit build deck.md --sample` → give the user `deck.sample.pptx` (cover + one data
   slide) and ask if the look and voice fit. Lasting preferences go to `pptkit profile set ...`
   (e.g. `dislikes=아이콘 남발`, `tone=corporate-clean`, `brand=0B5E7A`); deck-only ones go to `brief.yaml`.
7. **Build** - `pptkit build deck.md`. Fix every `WARN` by editing deck.md (shorten, split, re-voice),
   rebuild, then `pptkit qa deck.pptx` until it prints `OK`.
8. **Deliver** the .pptx path (in a cloud/app session, send the file).

Edits to a pptkit deck: change `deck.md` and rebuild; it is cheaper than editing the .pptx. Look at rendered
images only if `qa` reports something you cannot resolve from its message.

## Pattern selection order

1. sequence → `process` (dates → `timeline`) 2. alternatives → `compare` 3. two-axis judgment → `matrix-2x2`
4. data file → time series `chart-takeaway`, category × category `heatmap-table`/`pivot-table`
5. 3-4 headline numbers → `kpi-tiles` 6. one sentence → `key-message` 7. otherwise `bullets-callout`
Structure: `cover`, `agenda`, `section`, `exec-summary` (report page 1), `closing` (the ask + next steps).

Default orders by purpose - report: cover, exec-summary, data slides, closing. proposal: cover, key-message,
compare, process/timeline, closing. pitch: cover, key-message (problem), compare, kpi-tiles, timeline, closing.

## Statistics

No API key is ever needed. Prefer files the user downloads (KOSIS, e-나라지표, 한국은행 web pages → CSV) and
`pptkit data`. Do not ask for or handle API keys. Put the provider and reference date in `source:`.
