"""Smallest checks that fail if the core logic breaks. Run: python -m pytest tests -q  (or python tests/test_pptkit.py)"""
import os
import tempfile
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
os.environ["PPTKIT_HOME"] = tempfile.mkdtemp()

from pptkit import data, edit, persona, qa, render  # noqa: E402


def test_kosis_download_is_normalized_to_long():
    df = data.load(ROOT / "evals/data/kosis_style_population.csv")
    assert list(df.columns) == ["행정구역별", "성별", "year", "총인구"]
    assert len(df) == 4 * 3 * 5 and df["총인구"].dtype.kind in "if"


def test_pivot_totals_and_other_row():
    pv = data.pivot(data.load(ROOT / "evals/data/sales.csv"), "region", "year", "revenue_100m_krw", top=6)
    assert list(pv.index[-2:]) == ["기타", "합계"] and len(pv) == 8
    assert abs(pv.loc["합계", "합계"] - pv.drop("합계").drop(columns="합계").values.sum()) < 1e-6


def test_profile_then_tone_personalizes():
    rep = persona.profile_report()
    assert rep.startswith("PROFILE MISSING") and "ASSUME" in rep  # defaults are stated, not asked
    persona.set_profile(["role=사무관", "industry=public", "org_culture=gaejosik", "audiences=과장", "brand=none"])
    tone, summary = persona.resolve_tone({"purpose": "report", "ask": "승인", "mode": "handout"})
    assert tone["name"] == "public" and tone["density"]["max_bullets"] == 6 and "자료:" in summary
    persona.set_profile(["industry=startup"])
    assert persona.resolve_tone({"purpose": "ir", "ask": "투자", "mode": "present"})[0]["name"] == "signal"
    friendly, s2 = persona.resolve_tone({"purpose": "proposal", "ask": "파일럿", "mode": "present", "formality": "friendly"})
    assert friendly["name"] == "forest" and friendly["voice"] == "friendly" and "notes:" in s2


def test_weighted_mean_matches_manual():
    df = data.load(ROOT / "evals/data/sales.csv")
    pv = data.pivot(df, "category", "year", "gross_margin", "wmean", weight="revenue_100m_krw")
    d = df[(df.category == "구독") & (df.year == 2026)]
    assert abs(pv.loc["구독", 2026] - (d.gross_margin * d.revenue_100m_krw).sum() / d.revenue_100m_krw.sum()) < 1e-9


def test_example_deck_builds_native_and_passes_qa():
    out = Path(tempfile.mkdtemp()) / "deck.pptx"
    report = render.build(ROOT / "examples/sales-report/deck.md", out)
    assert report.startswith("OK 22 slides, 7 charts, 3 tables") and "WARN" not in report, report
    prs = Presentation(out)
    assert sum(s.has_chart for sl in prs.slides for s in sl.shapes) == 11  # 7 charts + 4 KPI sparklines
    assert qa.check(out) == []
    sample = render.build(ROOT / "examples/sales-report/deck.md", out.with_name("s.pptx"), sample=True)
    assert sample.startswith("OK 2 slides, 1 charts"), sample


def test_lint_flags_wrong_voice_and_density():
    md = Path(tempfile.mkdtemp()) / "d.md"
    md.write_text("---\ndesign: executive\n---\n# t\n- 첫째 문장입니다.\n- b\n- c\n- d\n- e\n- f\n"
                  "# u\nask: 승인\nsteps: [a]\n", encoding="utf-8")
    rep = render.build(md)
    assert "bullets 6>5" in rep and "voice" in rep and "unknown key(s) ['steps'] for closing" in rep, rep


def test_map_read_patch_on_a_foreign_deck():
    import shutil
    d = Path(tempfile.mkdtemp())
    shutil.copy(ROOT / "evals/data/review.pptx", d / "r.pptx")
    shutil.copy(ROOT / "evals/data/kpi_quarterly.csv", d)
    m = edit.deck_map(d / "r.pptx")
    assert "S3" in m and "read=L2" in m.splitlines()[3] and "chart:column 5x1" in m, m
    before = {n: edit.read(d / "r.pptx", [n], "L2") for n in (1, 2, 4, 6)}
    (d / "ops.yaml").write_text("- {slide: 3, fix: overlap}\n"
                                "- {slide: 5, shape: 3, chart: {data: kpi_quarterly.csv, x: quarter, y: mau_k}}\n",
                                encoding="utf-8")
    out = edit.patch(d / "r.pptx", d / "ops.yaml")
    assert "qa(S3,S5) OK" in out and (d / "r.bak.pptx").exists(), out
    assert all(edit.read(d / "r.pptx", [n], "L2") == v for n, v in before.items())  # untouched slides unchanged
    assert "2026Q3" in edit.read(d / "r.pptx", [5])


def test_p1_patterns_build_clean():
    out = Path(tempfile.mkdtemp()) / "p1.pptx"
    rep = render.build(ROOT / "examples/p1-patterns/deck.md", out)
    assert rep.startswith("OK 12 slides") and "WARN" not in rep, rep
    assert qa.check(out) == []


def test_style_extract_then_build_on_the_template():
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches
    from pptkit import style
    d = Path(tempfile.mkdtemp())
    prs = render.new_deck(persona.load_design("executive"))
    tmp = prs.slides.add_slide(prs.slide_layouts[6])
    logo = tmp.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(11.6), Inches(0.3), Inches(1.2), Inches(0.4))
    logo.fill.solid()
    logo.fill.fore_color.rgb = RGBColor(0xC8, 0x10, 0x2E)
    prs.slide_master.shapes._spTree.append(logo._element)  # brand mark on the master
    prs.save(d / "corp.pptx")
    rep = style.extract(d / "corp.pptx", "corp")
    assert "accent C8102E" in rep and "template linked" in rep, rep
    out = d / "deck.pptx"
    assert "design=corp" in render.build(ROOT / "examples/sales-report/deck.md", out, design="corp")
    built = Presentation(out)
    assert len(built.slides) == 22 and any(s.shape_type == 1 for s in built.slide_master.shapes)
    assert qa.check(out) == []


def test_fetch_parsers_and_cached_pipeline_offline():
    import hashlib
    import json
    from pptkit import sources
    fx = ROOT / "tests/fixtures"
    df, meta = sources.wb_parse(json.loads((fx / "synthetic_wb.json").read_text(encoding="utf-8")))
    assert len(df) == 5 and meta["provider"] == "World Bank WDI"  # null values dropped
    kdf, kmeta = sources.kosis_parse(json.loads((fx / "synthetic_kosis.json").read_text(encoding="utf-8")))
    assert kdf["value"].sum() == 1000 + 1010 + 500 + 510 and kmeta["indicator"] == "합성 테스트 표"
    try:
        sources.kosis_parse({"err": "11", "errMsg": "인증키 오류"})
        raise AssertionError("kosis error not raised")
    except SystemExit as e:
        assert "인증키 오류" in str(e)
    # cached response -> full fetch path without network, then a chart picks up the provenance automatically
    url = sources.wb_url("NY.GDP.MKTP.KD.ZG", ["KOR", "JPN"], "2023-2025")
    cache = persona.home() / "cache" / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".json")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text((fx / "synthetic_wb.json").read_text(encoding="utf-8"), encoding="utf-8")
    d = Path(tempfile.mkdtemp())
    rep = sources.fetch("wb", d, indicator="NY.GDP.MKTP.KD.ZG", countries=["KOR", "JPN"], years="2023-2025")
    assert "(cache)" in rep and (d / "wb_NY.GDP.MKTP.KD.ZG.meta.json").exists(), rep
    (d / "deck.md").write_text("---\ndesign: executive\n---\n# GDP\nchart: line-trend\ndata: wb_NY.GDP.MKTP.KD.ZG.csv\n"
                               "x: year\ny: value\nseries: country\n", encoding="utf-8")
    render.build(d / "deck.md", d / "deck.pptx")
    assert "World Bank WDI" in edit.read(d / "deck.pptx", [1])
    if not os.environ.get("KOSIS_API_KEY"):
        assert sources.key_cmd("status").startswith("kosis: not set")


def test_pivot_one_way_time_order_shares_and_weighted_totals():
    df = data.load(ROOT / "evals/data/sales.csv")
    one = data.pivot(df, "year", None, "revenue_100m_krw")
    assert list(one.index) == [2022, 2023, 2024, 2025, 2026, "합계"]  # chronological, not by size
    assert abs(data.cagr(one.drop(index="합계")).iloc[0] - 12.7) < 0.1
    share = data.pivot(df, "year", "channel", "revenue_100m_krw", pct="row")
    assert abs(share.sum(axis=1) - 100).max() < 1e-6
    wm = data.pivot(df, "year", "category", "gross_margin", agg="wmean", weight="revenue_100m_krw")
    overall = (df.gross_margin * df.revenue_100m_krw).sum() / df.revenue_100m_krw.sum()
    assert abs(wm.loc["합계", "합계"] - overall) < 1e-9


def test_world_bank_web_csv_is_normalized():
    f = Path(tempfile.mkdtemp()) / "wb.csv"
    f.write_text('"Data Source","World Development Indicators",\n\n"Last Updated Date","2026-07-01",\n\n'
                 '"Country Name","Country Code","Indicator Name","Indicator Code","2023","2024",\n'
                 '"Korea, Rep.","KOR","GDP growth","X","1.4","2.0",\n', encoding="utf-8")
    df = data.load(f)
    assert list(map(str, df["year"])) == ["2023", "2024"] and list(df["value"]) == [1.4, 2.0]


def test_stack_op_and_changed_map_sees_notes():
    d = Path(tempfile.mkdtemp())
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[6])
    for x, y in ((1, 1), (3, 1.5)):
        s.shapes.add_textbox(*(int(v * 914400) for v in (x, y, 4, 1))).text_frame.text = "box"
    deck = d / "d.pptx"
    prs.save(deck)
    edit.deck_map(deck)
    (d / "ops.yaml").write_text("- {slide: 1, stack: [2, 3], gap: 0.2}\n- {slide: 1, notes: hi}\n", encoding="utf-8")
    edit.patch(deck, d / "ops.yaml")
    a, b = Presentation(deck).slides[0].shapes
    assert a.left == b.left and b.top == a.top + a.height + int(0.2 * 914400)
    assert "S1" in edit.deck_map(deck, changed=True) and not list(d.glob("*.map.json"))


def test_gaejosik_lint_accepts_noun_endings():
    import re
    pat = re.compile(r"(다|(어|아|해|에|예|세|지|네|게|래|까|죠)요)[.!]?$")
    assert not any(pat.search(t) for t in ("추가 검토 필요", "수요 증가", "핵심 개요"))
    assert all(pat.search(t) for t in ("검토가 필요합니다", "늘었어요", "확대해요"))


def test_every_storyline_skeleton_uses_known_patterns_and_keys():
    from pptkit import plan
    for sid in plan.CAT["storylines"]:
        meta, slides = render.parse(plan.skeleton(sid))
        assert meta["storyline"] == sid and slides
        for sp in slides:
            assert sp["pattern"] in render.PATTERNS, (sid, sp["pattern"])
            assert not set(sp) - render.COMMON - render.KEYS[sp["pattern"]], (sid, sp["pattern"])
    assert "pitch/vc-seed" in plan.report("pitch") and "ASK THE USER" in plan.report("pitch/vc-seed")


def test_pitch_example_builds_clean():
    out = Path(tempfile.mkdtemp()) / "pitch.pptx"
    msg = render.build(ROOT / "examples/pitch/deck.md", out)
    assert "WARN" not in msg and "design=launch" in msg, msg
    assert qa.check(out) == []


def test_icons_draw_as_vector_shapes_and_unknown_names_warn():
    d = Path(tempfile.mkdtemp())
    (d / "deck.md").write_text("""---
design: corporate
---

# 세 가지 이유
pillars:
  - {icon: rocket, title: 빠름, desc: 설치 없이 2주}
  - {icon: shield-check, title: 안전, desc: 검증 내장}
  - {icon: rockett, title: 쉬움, desc: 오탈자 아이콘}
""", encoding="utf-8")
    msg = render.build(d / "deck.md")
    assert "unknown icon 'rockett'" in msg and "rocket" in msg.split("rockett")[1]
    shapes = [s for s in Presentation(d / "deck.pptx").slides[0].shapes if s.name.startswith("icon:")]
    assert [s.name for s in shapes] == ["icon:rocket", "icon:shield-check"]
    assert all(s._element.find(".//{http://schemas.openxmlformats.org/drawingml/2006/main}custGeom") is not None for s in shapes)


def test_report_visuals_waterfall_donut_progress_status():
    d = Path(tempfile.mkdtemp())
    (d / "deck.md").write_text("""---
design: corporate
---

# 증감
chart: waterfall
values: {2025: 100, 증가: 30, 감소: -10, 2026: "="}

# 구성
chart: donut
values: {A: 60, B: 40}

# 달성
pattern: progress
items:
  - {label: 서울, actual: 105, target: 100}
  - {label: 부산, actual: 80, target: 100}

# 상태
pattern: status-table
rows:
  - {item: 이관, owner: 팀, due: 9/30, status: red, note: 지연}
""", encoding="utf-8")
    msg = render.build(d / "deck.md")
    assert msg.startswith("OK 4 slides, 2 charts, 1 tables") and "WARN" not in msg, msg
    prs = Presentation(d / "deck.pptx")
    wf = next(s.chart for s in prs.slides[0].shapes if s.has_chart)
    tot = [s for s in wf.plots[0].series if s.name == "합계"][0]
    assert list(tot.values)[-1] == 120 and wf.value_axis.minimum_scale is not None
    texts = [s.text_frame.text for s in prs.slides[2].shapes if s.has_text_frame]
    assert "105% 달성" in texts and "80% 미달" in texts
    cells = [c.text for s in prs.slides[3].shapes if s.has_table for r in s.table.rows for c in r.cells]
    assert "● 지연" in cells
    assert [f for f in qa.check(d / "deck.pptx") if "sparse" not in f] == []  # one-row table is sparse by design


def test_bridge_gives_waterfall_values_and_missing_data_builds_a_placeholder():
    import pandas as pd
    df = pd.DataFrame({"r": list("abcd") * 2, "y": [2025] * 4 + [2026] * 4, "v": [10, 20, 30, 40, 15, 18, 31, 44]})
    items, chg = data.bridge(data.pivot(df, "r", "y", "v"), "2025", "2026", top=2)
    assert items == [("2025", 100.0), ("a", 5.0), ("d", 4.0), ("기타 2개", -1.0), ("2026", "=")] and chg == 8
    from pptkit import plan
    d = Path(tempfile.mkdtemp())
    (d / "deck.md").write_text(plan.skeleton("report/performance"), encoding="utf-8")
    msg = render.build(d / "deck.md")
    assert msg.startswith("OK 9 slides") and "data file 'TODO.csv' not found" in msg, msg
    assert any("데이터 대기" in s.text_frame.text for s in Presentation(d / "deck.pptx").slides[5].shapes
               if s.has_text_frame)


def test_category_chart_table_keeps_every_region_and_progress_keeps_the_miss_visible():
    import pandas as pd
    d = Path(tempfile.mkdtemp())
    regions = list("가나다라마바사아자차")
    pd.DataFrame({"r": regions * 2, "q": ["2025Q3"] * 10 + ["2026Q3"] * 10,
                  "v": [float(10 + i) for i in range(10)] + [11.5 + i for i in range(10)]}).to_csv(d / "q.csv", index=False)
    (d / "deck.md").write_text("""---
design: corporate
---

# 비교
pattern: chart-table
chart: column-trend
data: q.csv
x: r
y: v
series: q
growth: true

# 달성
pattern: progress
items:
  - {label: 대구, actual: 21.9, target: 22.0}
  - {label: 서울, actual: 107.9, target: 105}
callout: [대구 근접]
""", encoding="utf-8")
    render.build(d / "deck.md")
    prs = Presentation(d / "deck.pptx")
    ch = next(s.chart for s in prs.slides[0].shapes if s.has_chart)
    assert list(ch.plots[0].categories) == regions  # file order, not 가나다 sorted
    rows = [[c.text for c in r.cells] for s in prs.slides[0].shapes if s.has_table for r in s.table.rows]
    assert len(rows) == 11 and rows[0][-1] == "증감률" and rows[1][1] == "10.0"
    texts = [s.text_frame.text for s in prs.slides[1].shapes if s.has_text_frame]
    assert "99.5% 근접" in texts and "107.9 / 105.0" in texts
    assert qa.check(d / "deck.pptx") == []
    gs = data.growth_summary(pd.DataFrame({"v": [100.0, 110.0]}, index=["2025Q3", "2026Q3"]))
    assert gs[0] == "증감률 2025Q3→2026Q3" and round(float(gs[1]["v"]), 1) == 10.0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
