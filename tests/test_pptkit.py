"""Smallest checks that fail if the core logic breaks. Run: python -m pytest tests -q  (or python tests/test_pptkit.py)"""
import os
import tempfile
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
os.environ["PPTKIT_HOME"] = tempfile.mkdtemp()

from pptkit import data, persona, qa, render  # noqa: E402


def test_kosis_download_is_normalized_to_long():
    df = data.load(ROOT / "evals/data/kosis_style_population.csv")
    assert list(df.columns) == ["행정구역별", "성별", "year", "총인구"]
    assert len(df) == 4 * 3 * 5 and df["총인구"].dtype.kind in "if"


def test_pivot_totals_and_other_row():
    pv = data.pivot(data.load(ROOT / "evals/data/sales.csv"), "region", "year", "revenue_100m_krw", top=6)
    assert list(pv.index[-2:]) == ["기타", "합계"] and len(pv) == 8
    assert abs(pv.loc["합계", "합계"] - pv.drop("합계").drop(columns="합계").values.sum()) < 1e-6


def test_profile_then_tone_personalizes():
    assert persona.profile_report().startswith("PROFILE MISSING")
    persona.set_profile(["role=사무관", "industry=public", "org_culture=gaejosik", "audiences=과장", "brand=none"])
    tone, summary = persona.resolve_tone({"purpose": "report", "ask": "승인", "mode": "handout"})
    assert tone["name"] == "corporate-clean" and tone["density"]["max_bullets"] == 6 and "출처" in summary
    persona.set_profile(["industry=startup"])
    assert persona.resolve_tone({"purpose": "pitch", "ask": "투자", "mode": "present"})[0]["name"] == "pitch-bold"


def test_example_deck_builds_native_and_passes_qa():
    out = Path(tempfile.mkdtemp()) / "deck.pptx"
    report = render.build(ROOT / "examples/sales-report/deck.md", out)
    assert report.startswith("OK 17 slides, 3 charts, 2 tables") and "WARN" not in report, report
    prs = Presentation(out)
    assert sum(s.has_chart for sl in prs.slides for s in sl.shapes) == 3
    assert qa.check(out) == []
    sample = render.build(ROOT / "examples/sales-report/deck.md", out.with_name("s.pptx"), sample=True)
    assert sample.startswith("OK 2 slides, 1 charts"), sample


def test_lint_flags_wrong_voice_and_density():
    md = Path(tempfile.mkdtemp()) / "d.md"
    md.write_text("---\ntone: consulting-navy\n---\n# t\n- 첫째 문장입니다.\n- b\n- c\n- d\n- e\n- f\n", encoding="utf-8")
    rep = render.build(md)
    assert "bullets 6>5" in rep and "voice" in rep, rep


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
