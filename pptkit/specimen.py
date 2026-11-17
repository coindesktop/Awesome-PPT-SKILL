"""`pptkit design show <name>`: a specimen deck of one design - its tokens on a slide, then every main
component - so a look can be judged (and a user design debugged) before any real deck is written."""
import tempfile
from pathlib import Path

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN

from .render import KEYS, PATTERNS, box, build, card, content_slide, dark_color, mix, on_color, text

ROLES = [("bg", "바탕"), ("surface", "카드·표"), ("card", "낮은 면"), ("line", "선"), ("ink", "제목"), ("body", "본문"),
         ("muted", "보조"), ("accent", "강조"), ("dark", "어두운 면"), ("positive", "증가"), ("negative", "감소")]

DECK = """---
design: {name}
date: 2026-11-17
author: 사업기획팀
eyebrow: {name} 디자인 견본
source: 가상 예시 데이터
---

# 2026 지역별 매출 현황과 영업 인력 운영안
pattern: cover
subtitle: 지역·채널 분석과 2027년 영업 인력 증원안

# {name}: {description}
pattern: design-tokens

# 매출은 4년 연속 두 자릿수 성장을 이어감
points: ["2026년 매출 1,321억 원으로 전년 대비 12.5% 증가함", "수도권 비중 65%로 지역 편중이 지속됨", "비수도권은 영업 인력 부족으로 성장 여력이 남아 있음"]
numbers:
  - {{value: "1,321억", label: 2026년 매출}}
  - {{value: "+12.5%", label: 전년 대비 성장률}}
  - {{value: "65%", label: 수도권 매출 비중}}

# 현황 분석
pattern: section
number: 1
subtitle: 매출 추이와 지역 구조

# 2026년 3분기 핵심 지표는 모두 개선됨
kpis:
  - {{label: MAU, value: 637천, delta: "+4.6%", icon: users, spark: [499, 527, 568, 609, 637]}}
  - {{label: 유료 전환율, value: 4.2%, delta: "+0.2%p", icon: percent, spark: [3.6, 3.8, 3.9, 4.0, 4.2]}}
  - {{label: 이탈률, value: 4.4%, delta: "-0.2%p", good: down, icon: trending-down, spark: [5.1, 4.9, 4.8, 4.6, 4.4]}}
  - {{label: NPS, value: "32", delta: "+2", icon: star, spark: [25, 27, 26, 30, 32]}}

# 2026년 매출이 처음으로 1,300억 원을 넘어섬
pattern: chart-table
chart: column-trend
values: {{2022: 818.8, 2023: 914.3, 2024: 1017.0, 2025: 1174.2, 2026: 1321.1}}
y: 매출
highlight: 2026
growth: true
unit: 억 원
takeaways: ["4년 누적 성장률 61%, 연평균 13% 성장", "2025년 성장률 15.5%로 최고치 기록"]

# 채널 네 곳 가운데 온라인이 성장분의 대부분을 차지함
chart: line-trend
values:
  온라인: {{2022: 460.1, 2023: 541.5, 2024: 642.1, 2025: 798.3, 2026: 941.9}}
  직영점: {{2022: 190.2, 2023: 196.4, 2024: 198.0, 2025: 197.1, 2026: 199.5}}
  대리점: {{2022: 112.4, 2023: 118.9, 2024: 121.3, 2025: 124.6, 2026: 126.8}}
  제휴: {{2022: 56.1, 2023: 57.5, 2024: 55.6, 2025: 54.2, 2026: 52.9}}
unit: 억 원
takeaways: ["온라인 매출은 4년간 2배 이상 증가함", "직영점·대리점은 정체 구간에 진입함"]

# 증원안은 B안(2명, 부산·대구 거점)을 권고함
options: [A안 현행 유지, B안 2명 증원, C안 대리점 위탁]
criteria:
  - {{label: 연 비용, values: [0원, 3억 원, 1.5억 원]}}
  - {{label: 비수도권 커버리지, values: [○, ●, ◐]}}
  - {{label: 고객 경험 통제, values: [●, ●, ○]}}
  - {{label: 회수 기간, values: ["-", 1년 내, 2년]}}
recommend: 2

# 증원 후 6개월 안에 거점 운영을 안정화함
steps:
  - {{title: 채용, desc: 11월 중 2명 채용 완료, icon: user-plus}}
  - {{title: 온보딩, desc: 수도권 동행 영업 4주, icon: graduation-cap}}
  - {{title: 거점 개설, desc: 부산·대구 공유 오피스, icon: building}}
  - {{title: 성과 점검, desc: 분기별 매출 리뷰, icon: chart-line}}

# 지역별 목표 달성률은 영남이 가장 높음
pattern: progress
items:
  - {{label: 수도권, actual: 48.8, target: 51.3}}
  - {{label: 영남, actual: 34.9, target: 34.2}}
  - {{label: 호남, actual: 19.3, target: 22.4}}
unit: 억
callout: ["영남만 목표 달성, 호남은 원인 점검 필요"]

# 요청 사항
ask: 비수도권 영업 인력 2명 증원 승인 (연 3억 원)
support: 승인 시 11월 채용을 시작해 내년 1분기에 거점을 개설합니다
next:
  - {{t: 채용 공고 게시, who: 인사팀, when: 11월 3주}}
  - {{t: 거점 오피스 계약, who: 총무팀, when: 11월 말}}
"""


def p_design_tokens(ctx, spec):
    """The design on one slide: colour roles, chart series, type scale, card style."""
    slide, (x, y, w, h) = content_slide(ctx, spec)
    c, ty, sh = ctx.c, ctx.ty, ctx.tone["shape"]
    lw = w * 0.56
    text(ctx, slide, x, y, lw, 0.3, ["색 역할"], 12, c["accent"], bold=True)
    sw, gap = (lw - 5 * 0.14) / 6, 0.14
    for i, (k, role) in enumerate(ROLES):
        cx, cy = x + (i % 6) * (sw + gap), y + 0.4 + (i // 6) * 1.25
        b = box(slide, cx, cy, sw, 0.62, fill=c[k], line=c["line"], radius=min(sh["radius"], 0.08) or None)
        text(ctx, slide, 0, 0, sw, 0.62, [c[k].upper()], 9, on_color(c[k]) if dark_color(c[k]) else c["body"],
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
        text(ctx, slide, cx, cy + 0.66, sw, 0.5, [k, role], 10, c["body"], gap=0, min_pt=8)
    sy = y + 0.4 + 2 * 1.25 + 0.1
    text(ctx, slide, x, sy, lw, 0.3, ["차트 계열 (검증된 순서)"], 12, c["accent"], bold=True)
    series = list(ctx.tone["series"]) + [c["neutral_series"]]
    bw = (lw - (len(series) - 1) * gap) / len(series)
    for i, col in enumerate(series):
        b = box(slide, x + i * (bw + gap), sy + 0.4, bw, 0.5, fill=col, radius=0.06)
        text(ctx, slide, 0, 0, bw, 0.5, [col.upper() if i < len(series) - 1 else "neutral"], 9, on_color(col),
             align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, shape=b)
    rx, rw = x + lw + 0.5, w - lw - 0.5
    text(ctx, slide, rx, y, rw, 0.3, ["글자 크기"], 12, c["accent"], bold=True)
    rows = [("제목", ty["title"], c["ink"], True), ("메시지·본문", ty["body"], c["body"], False),
            ("라벨", ty["eyebrow"], c["accent"], True), ("출처·쪽번호", ty["small"], c["muted"], False)]
    ry = y + 0.4
    for name, pt, col, bold in rows:
        rh = max(0.36, pt / 72 * 1.5)
        text(ctx, slide, rx, ry, rw, rh, [f"{name} {pt}pt"], pt, col, bold=bold, anchor=MSO_ANCHOR.MIDDLE, min_pt=pt)
        ry += rh + 0.05
    mh = max(0.75, ty["metric"] / 72 * 1.55)
    text(ctx, slide, rx, ry, rw, mh, ["1,321억"], ty["metric"], c["accent"], bold=True, anchor=MSO_ANCHOR.MIDDLE,
         min_pt=ty["metric"])
    cy = ry + mh + 0.2
    text(ctx, slide, rx, cy, rw, 0.3, ["카드"], 12, c["accent"], bold=True)
    ch = max(0.9, y + h - (cy + 0.4))
    card(ctx, slide, rx, cy + 0.4, rw, ch)
    style = ctx.st
    text(ctx, slide, rx + 0.25, cy + 0.5, rw - 0.5, ch - 0.2,
         [f"card: {sh.get('card', 'fill')} · radius {sh['radius']}in",
          f"header: {style['header']} · table: {style['table_head']} · chart: {style['chart']}"], 11, c["body"],
         anchor=MSO_ANCHOR.MIDDLE, gap=3, min_pt=9)


PATTERNS["design-tokens"], KEYS["design-tokens"] = p_design_tokens, set()


def show(name, out=None):
    from . import persona
    d = persona.load_design(name)  # unknown names stop here with the list of designs
    out = Path(out or f"{name}.specimen.pptx").resolve()
    tmp = Path(tempfile.mkdtemp())
    desc = str(d.get("description", "")).split(".")[0][:40].replace('"', "'")
    (tmp / "deck.md").write_text(DECK.format(name=name, description=desc), encoding="utf-8")
    msg = build(tmp / "deck.md", out)
    return msg.replace(str(out), out.name) if out.parent == Path.cwd() else msg
