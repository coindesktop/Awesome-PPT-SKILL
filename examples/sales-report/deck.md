---
brief: brief.yaml
source: "사내 판매 데이터(가상), 2026"
date: 2026-10-03
author: 사업기획팀
eyebrow: 사업본부 월간 보고
labels: {region: 지역, category: 품목, channel: 채널, year: 연도, revenue_100m_krw: 매출}
---

# 2026 지역별 매출 현황과 영업 인력 운영안
pattern: cover
subtitle: 지역·채널·품목 분석과 2027년 영업 인력 증원안

# 목차
items:
- 핵심 요약
- 매출 추이
- 지역별 현황
- 개선 방향
- 요청 사항

# 매출은 4년 연속 두 자릿수 성장을 이어감
points:
- 2026년 매출 1,321억 원으로 전년 대비 12.5% 증가함
- 수도권 비중 65%로 지역 편중이 지속됨
- 비수도권은 영업 인력 부족으로 성장 여력이 남아 있음
numbers:
- {value: "1,321억", label: 2026년 매출}
- {value: "+12.5%", label: 전년 대비 성장률}
- {value: "65%", label: 수도권 매출 비중}

# 매출 추이
pattern: section
number: 1

# 2026년 매출이 처음으로 1,300억 원을 넘어섬
message: 4년 누적 성장률 61%, 연평균 13% 성장
pattern: chart-table
chart: column-trend
data: ../../evals/data/sales.csv
x: year
y: revenue_100m_krw
highlight: 2026
growth: true
unit: 억 원
takeaways:
- 2026년 성장률 12.5%로 4년 연속 두 자릿수
- 2025년 성장률 15.5%로 최고치 기록

# 매출의 절반은 솔루션, 구독 비중은 34~35%로 안정적임
chart: stacked-share
data: ../../evals/data/sales.csv
x: year
y: revenue_100m_krw
series: category
takeaways:
- 구독 이익률 48%로 솔루션보다 15%p 높음
- 컨설팅 비중은 17%에서 정체

# 온라인 채널이 성장분의 대부분을 차지함
chart: line-trend
data: ../../evals/data/sales.csv
x: year
y: revenue_100m_krw
series: channel
unit: 억 원
takeaways:
- 온라인 매출은 4년간 2배 이상 증가함
- 오프라인은 정체 구간에 진입함

# 서울·경기가 매출 상위 2개 지역이고, 이익률은 품목 구성에 좌우됨
data: ../../evals/data/sales.csv
charts:
- {subtitle: "2026년 지역별 매출 (억 원)", chart: bar-ranked, x: region, y: revenue_100m_krw, where: {year: 2026}, highlight: 서울}
- {subtitle: "품목별 매출총이익률 추이", chart: line-trend, x: year, y: gross_margin, series: category, agg: wmean, weight: revenue_100m_krw, fmt: pct}

# 지역별로는 수도권 비중이 절반을 넘음
message: 연도별 지역 매출 피벗 (상위 6개 지역 + 기타)
pattern: heatmap-table
data: ../../evals/data/sales.csv
rows: region
cols: year
val: revenue_100m_krw
top: 6
unit: 억 원

# 품목별 매출 구성
pattern: pivot-table
data: ../../evals/data/sales.csv
rows: category
cols: channel
val: revenue_100m_krw
where: {year: 2026}
unit: 억 원

# 2026년 3분기 핵심 지표는 모두 개선됨
kpis:
- {label: MAU, value: "637천", delta: "+4.6%"}
- {label: 유료 전환율, value: "4.2%", delta: "+0.2%p"}
- {label: 이탈률, value: "4.4%", delta: "-0.2%p", good: down}
- {label: NPS, value: "32", delta: "+2"}

# 비수도권 성장을 막는 요인은 영업 커버리지 부족임
bullets:
- 비수도권 고객 1개사당 담당 인력이 수도권의 절반 수준임
- 부산·대구는 방문 상담 대기 기간이 평균 3주임
- 온라인 채널만으로는 엔터프라이즈 계약 전환이 어려움
callout:
- 인력 증원 시 연 40억 원 추가 매출 기대
- 회수 기간 1년 이내

# 증원안은 B안(2명, 부산·대구 거점)을 권고함
recommend: 2
columns:
- title: A안 현행 유지
  items: [추가 비용 없음, 비수도권 성장 정체 지속]
- title: B안 2명 증원
  items: [연 인건비 3억 원, 부산·대구 거점 운영, 1년 내 회수 가능]
- title: C안 대리점 위탁
  items: [고정비 낮음, 고객 경험 통제 어려움]

# 우선 추진 과제는 영향이 크고 실행이 쉬운 2개임
x_axis: 실행 용이성
y_axis: 기대 효과
quadrants: [단계적 추진, 우선 추진, 보류, 빠른 개선]
items:
- {label: 거점 영업 인력, x: 0.7, y: 0.85}
- {label: 온라인 상담 확대, x: 0.85, y: 0.6}
- {label: 대리점 위탁, x: 0.3, y: 0.4}
- {label: 지역 세미나, x: 0.75, y: 0.25}
callout:
- 우선 추진 2개 과제를 1분기 내 착수함

# 증원 후 6개월 안에 거점 운영을 안정화함
steps:
- {title: 채용, desc: 11월 중 2명 채용 완료}
- {title: 온보딩, desc: 수도권 동행 영업 4주}
- {title: 거점 개설, desc: 부산·대구 공유 오피스}
- {title: 성과 점검, desc: 분기별 매출 리뷰}
highlight: 3

# 일정
events:
- {when: 2026.11, label: 채용 완료}
- {when: 2026.12, label: 온보딩}
- {when: 2027.01, label: 거점 개설, now: true}
- {when: 2027.03, label: 1차 성과 점검}
- {when: 2027.06, label: 연간 계획 반영}

# 비수도권 성장은 지금 투자할 시점임
statement: 영업 인력 2명이면 비수도권 매출 성장률을 2배로 올릴 수 있음
support: 1년 내 투자 회수, 실패 시 대리점 위탁으로 전환 가능

# 요청 사항
ask: 비수도권 영업 인력 2명 증원 승인 (연 3억 원)
next:
- {t: 채용 공고 게시, who: 인사팀, when: 10월 3주}
- {t: 거점 오피스 계약, who: 총무팀, when: 11월}
