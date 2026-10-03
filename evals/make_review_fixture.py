"""Builds evals/data/review.pptx: a deck made without pptkit (plain python-pptx, default template),
with overlapping boxes on slide 3 and an outdated KPI chart on slide 5. Used by eval 3 (targeted edit)."""
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)


def slide(title):
    s = prs.slides.add_slide(prs.slide_layouts[5])
    s.shapes.title.text = title
    return s


def box(s, x, y, w, h, text, pt=18):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    tb.text_frame.text = text
    for p in tb.text_frame.paragraphs:
        for r in p.runs:
            r.font.size = Pt(pt)
    return tb


s = prs.slides.add_slide(prs.slide_layouts[0])
s.shapes.title.text = "3분기 서비스 리뷰"
s.placeholders[1].text = "그로스팀 · 2026년 10월"
s = slide("목차")
box(s, 1, 1.8, 8, 3, "1. 요약\n2. 이슈\n3. 지표\n4. 다음 분기 계획")
s = slide("3분기 주요 이슈")
box(s, 0.8, 1.8, 6.0, 1.2, "온보딩 개편 후 첫 주 이탈이 줄었지만 결제 전환은 기대보다 낮음")
box(s, 3.5, 2.6, 6.5, 1.4, "결제 페이지 오류가 9월 둘째 주에 집중 발생해 전환율을 끌어내림")
box(s, 0.8, 4.6, 9, 1.0, "다음 분기에는 결제 흐름 개선을 최우선으로 진행함", 16)
s = slide("분기 요약")
box(s, 0.8, 1.8, 11, 3, "MAU 성장세 유지\n유료 전환율 소폭 상승\nNPS 개선")
s = slide("MAU 추이 (천 명)")
cd = CategoryChartData()
cd.categories = ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1"]
cd.add_series("MAU", [446, 464, 489, 512, 540])
s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.8), Inches(1.6), Inches(11.5), Inches(5.2), cd)
s.notes_slide.notes_text_frame.text = "2026Q1까지의 수치입니다."
s = slide("다음 분기 계획")
box(s, 0.8, 1.8, 11, 3, "결제 흐름 개선\n온보딩 A/B 테스트 확대\n리텐션 캠페인")
out = Path(__file__).parent / "data" / "review.pptx"
prs.save(out)
print(out)
