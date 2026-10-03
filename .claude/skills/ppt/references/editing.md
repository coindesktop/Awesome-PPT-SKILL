# Editing any .pptx: map → read → patch

```bash
pptkit map deck.pptx                  # S3 "제목" | #2 text #4 text #7 chart:column 5x1 | ⚠1 qa | read=L2
pptkit read deck.pptx -s 3,5          # L1: text per shape id, chart categories/series, table rows, notes
pptkit read deck.pptx -s 3 -l L2      # + geometry @(x,y,w,h in inches) and font size: for layout fixes
pptkit read deck.pptx -s 4 -l L3 --shape 6   # raw XML of one shape: SmartArt/OLE/groups only
pptkit patch deck.pptx ops.yaml       # in place, first run saves deck.bak.pptx; -o new.pptx to keep the original
pptkit map deck.pptx --changed        # only slides changed since the last map
```

Read only the slides you will change, at the level `map` recommends. Shape ids (`#7`) are stable within a deck.

## ops.yaml

A YAML list; each item is one operation. Paths are relative to ops.yaml.

```yaml
- {slide: 3, shape: 4, text: "새 문장"}              # replace text, keeps the first run's font/size/color
- {slide: 3, shape: 4, paras: ["첫 줄", "둘째 줄"]}   # several paragraphs, same formatting
- {slide: 3, shape: 5, move: [0.8, 3.1, null, null]}  # x, y, w, h in inches; null keeps the value
- {slide: 3, fix: overlap}                           # push partially overlapping text boxes apart (vertical only)
- {slide: 3, stack: [3, 4, 5], gap: 0.2}             # same left/width as #3, stacked top to bottom: tidy rows
- {slide: 5, shape: 3, chart: {data: kpi.csv, x: quarter, y: mau_k, labels: {mau_k: MAU}}}
- {slide: 5, shape: 3, chart: {data: kpi.csv, x: quarter, y: mau_k, last: 6}}   # only the latest 6 rows
- {slide: 5, shape: 3, chart: {categories: [Q1, Q2], series: {매출: [10, 12]}}}  # inline values
- {slide: 6, shape: 4, cells: {"1,2": "1,321", "2,2": "914"}}   # table cell "row,col" (0-based, row 0 = header)
- {replace: {"2025년": "2026년", "잠정": "확정"}}          # every slide; matches inside a single text run
- {slide: 4, delete: 9}                              # remove a shape
- {slide: 5, notes: "2026년 3분기까지의 수치"}            # speaker notes
```

Chart data from a file uses the same keys as deck.md charts (`x`, `y`, `series`, `where`, `agg`, `weight`).
After patching, pptkit re-runs qa on the touched slides and prints only problems (or `qa(S3,S5) OK`).
Untouched slides keep their content and geometry.
