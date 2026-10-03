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
    assert friendly["name"] == "forest" and friendly["voice"] == "formal" and "notes:" in s2


def test_weighted_mean_matches_manual():
    df = data.load(ROOT / "evals/data/sales.csv")
    pv = data.pivot(df, "category", "year", "gross_margin", "wmean", weight="revenue_100m_krw")
    d = df[(df.category == "구독") & (df.year == 2026)]
    assert abs(pv.loc["구독", 2026] - (d.gross_margin * d.revenue_100m_krw).sum() / d.revenue_100m_krw.sum()) < 1e-9


def test_example_deck_builds_native_and_passes_qa():
    out = Path(tempfile.mkdtemp()) / "deck.pptx"
    report = render.build(ROOT / "examples/sales-report/deck.md", out)
    assert report.startswith("OK 18 slides, 5 charts, 3 tables") and "WARN" not in report, report
    prs = Presentation(out)
    assert sum(s.has_chart for sl in prs.slides for s in sl.shapes) == 5
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


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
