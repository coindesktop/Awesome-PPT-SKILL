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
2. **Purpose → structure (ask, then let the user choose)** - Do not invent the deck's structure.
   - Purpose unclear from the request → ask it first (`pptkit plan` lists purposes: pitch, sales, report,
     proposal, education).
   - `pptkit plan <purpose>` lists proven storylines (pitch: VC seed, Sequoia, traction-first, demo day,
     정부지원사업 PSST, ...; report: 결론 먼저, SCR, 목표 대비 실적, 프로젝트 진척). Show them to the user as choices (AskUserQuestion if you have it), your
     recommendation first with one reason. Skip the choice only if the user already named a structure.
   - `pptkit plan <id> -o deck.md` writes the skeleton (one slide per step, `TODO`s) and prints the content
     questions. Ask the ones the request and files do not answer, in one message, together with any step 1 or
     brief questions. If the user says "알아서", draft from what you know and label invented figures `(예시)`.
   - Fill every `TODO` (build warns on leftovers); delete steps the user does not need or merge two to reach
     the requested length (build notes a mismatch with `length`).
   - Ask at most 5 questions in that first message. Anything with a safe default (mode → balanced, a provisional
     year → mark "(잠정)", column meanings) is not asked: state the default in one line instead.
3. **What** - write `brief.yaml` in the work folder:
   ```yaml
   purpose: report        # report | proposal | pitch | ir | sales | education | review
   storyline: report/exec-report   # the id the user picked; sets mode and design defaults
   audience: 사업본부장
   ask: 영업 인력 2명 증원 승인   # what the audience must decide/do after this deck
   mode: balanced         # present | balanced | handout
   formality: formal      # formal | neutral | friendly ("딱딱하지 않게", "친근하게" → friendly)
   length: 8
   # design: forest       # optional override; `pptkit design` lists them
   ```
   `ask` and `mode` drive quality most. If you cannot infer them, ask (bundle with step 1 questions).
4. **Tone** - `pptkit tone --brief brief.yaml`. It picks a DESIGN (look) and prints `VOICE` and `RULES`;
   obey them in every sentence you write (`friendly` overrides the profile's report shorthand for this deck).
   A `BRIEF MISSING` block means ask first.
5. **Data** - `pptkit data <file>` for a summary (KOSIS and World Bank web downloads are normalized automatically).
   Every number in a title or bullet comes from `pptkit pivot <file> --rows .. [--cols ..] --val ..`: totals and
   CAGR are printed; `--pct row|col` gives shares, `--pct growth` the change vs the previous period;
   `--where year=2025,2026` filters, `--group 수도권=서울,경기,인천` merges rows (combined shares);
   `--agg wmean --weight <col>` gives weighted averages (e.g. revenue-weighted margin) with weighted totals.
   `--pct diff` gives net adds; `--cols year --bridge 2025,2026 [--top 5]` prints the `values:` line of a
   `chart: waterfall` (start, changes largest first, the rest as 기타, end) and each change's share of the total
   change. Do not do arithmetic on pivot output yourself.
   For a pitch, derived metrics persuade: growth rate, net adds, revenue per customer, ARR. Get growth and net
   adds from pivot (`--pct growth`, `--pct diff`, multiples are printed), revenue per customer from
   `--val mrr --per customers`; a plain unit conversion like ARR = MRR×12 is fine if the slide says so.
6. **Deck** - complete `deck.md` per [references/deck-spec.md](references/deck-spec.md) (`pptkit icons` for icon names). Titles are conclusion
   sentences backed by numbers you got from pptkit. Pick patterns by the order below and vary them; when a
   slide holds one chart, prefer `chart-table` or `chart-pair` if a second view adds information.
7. **Tone sample** - `pptkit build deck.md --sample` → give the user `deck.sample.pptx` (cover + one data
   slide) and ask if the look and voice fit. Compare looks with `--design <name>`. Lasting preferences go to
   `pptkit profile set ...` (e.g. `design=forest`, `brand=0B5E7A`, `dislikes=..`); deck-only ones to `brief.yaml`.
8. **Build** - `pptkit build deck.md` (`-o 이름.pptx` names the file). Its `WARN` lines are about content (keys, length, voice); `pptkit qa
   deck.pptx` is about layout (overflow, overlap, `sparse`). Fix both by editing deck.md and rebuilding until
   neither reports anything (on Windows with PowerPoint, `qa --com` measures text exactly).
9. **Deliver** the .pptx path (in a cloud/app session, send the file).

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
4. data file → change from A to B by factor `chart: waterfall`, parts of one total `chart: donut`, target vs actual
   `progress`, task/RAG status `status-table`, time series `chart-takeaway`/`chart-table`, composition `chart: stacked-share`,
   category × category `heatmap-table`/`pivot-table`, two related views `chart-pair`, conversion → `funnel`
5. 3-4 headline numbers → `kpi-tiles`; one number → `big-number`; market → `market-size`;
   growth with headline metrics → `traction`; 3-4 strengths/reasons → `pillars`; people → `team`;
   plans and prices → `pricing`; product with features → `product-shot`; money and its use → `funding-ask`
6. one sentence → `key-message` 7. otherwise `bullets-callout` (two lists → `two-column`)
Structure: `cover`, `agenda`, `section` (sets the eyebrow of following slides), `exec-summary`, `closing`.

Slide order comes from the storyline the user picked (`pptkit plan`), not from this list.

## Numbers you did not compute

Only put numbers on slides that come from the user's files or from pptkit (`data`, `pivot`, `fetch`). When a
storyline step has no source (e.g. market size not ready), ask for it; if the user cannot supply it, delete
that slide rather than fill it with `(예시)` placeholders (build lists any that remain). A `data:` file that is
not there yet builds as a "데이터 대기" placeholder slide with a WARN; tell the user which file it waits for. Never
fill a chart with figures from memory or loose web snippets: they differ run to run. Public statistics:
`pptkit fetch wb <indicator> --country KOR,JPN --years 2021-2025` needs no key (World Bank); if it reports the
network is unreachable, ask the user to download the table as CSV (KOSIS, e-나라지표, 한국은행) and use
`pptkit data` (fetch prints the download page). If the user said where a slide goes ("맨 앞"), put it right
after the cover. KOSIS API needs the user's own key: they run `pptkit key set kosis` themselves; never ask for a
key in chat. `fetch` writes provenance that becomes the slide footnote; mark provisional years "(잠정)".
