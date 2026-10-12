---
design: corporate
date: 2026-10-05
author: 영업기획팀
eyebrow: 영업 실적 월간 보고
source: 가상 예시 데이터 (팀별 월 매출·목표·계약)
labels: {month: 월, team: 팀, revenue_100m_krw: 매출, target_100m_krw: 목표}
vars:
  mon: {data: monthly.csv, col: month, at: latest}
  rev: {data: monthly.csv, val: revenue_100m_krw, where: {month: latest}, unit: 억 원}
  mom: {data: monthly.csv, val: revenue_100m_krw, growth: {month: [prev, latest]}}
  q3m: {data: monthly.csv, val: revenue_100m_krw, growth: {month: [latest-3, latest]}}
  ach: {data: monthly.csv, val: revenue_100m_krw, per: target_100m_krw, where: {month: latest}}
  gap: {data: monthly.csv, val: revenue_100m_krw, minus: target_100m_krw, where: {month: latest}, unit: 억 원}
  deals: {data: monthly.csv, val: deals, where: {month: latest}, unit: 건}
  dmom: {data: monthly.csv, val: deals, growth: {month: [prev, latest]}}
  yn: {data: monthly.csv, val: revenue_100m_krw, per: target_100m_krw, where: {month: latest, team: 영남팀}}
---

# $mon 영업 실적 월간 보고
pattern: cover
subtitle: 매출·목표 달성·계약 현황과 팀별 증감 요인

# $mon 매출 $rev, 전월 대비 $mom이나 목표 달성률은 $ach임
kpis:
  - {label: 월 매출, value: $rev, delta: $mom, icon: banknote, spark: {data: monthly.csv, x: month, y: revenue_100m_krw}}
  - {label: 목표 달성률, value: $ach, note: "목표 대비 $gap", icon: target, spark: {data: monthly.csv, x: month, y: revenue_100m_krw, per: target_100m_krw}}
  - {label: 신규 계약, value: $deals, delta: $dmom, icon: handshake, spark: {data: monthly.csv, x: month, y: deals}}
eyebrow: 핵심 지표

# 매출은 최근 3개월 $q3m 늘어 $mon $rev를 기록함
chart: column-trend
data: monthly.csv
x: month
y: revenue_100m_krw
highlight: latest
growth: true
unit: 억 원
eyebrow: 추이

# 영남팀만 목표를 넘었고($yn), 전체는 목표 대비 $gap임
pattern: progress
data: monthly.csv
where: {month: latest}
x: team
actual: revenue_100m_krw
target: target_100m_krw
unit: 억
callout: ["호남팀 달성률이 가장 낮아 거래처 이탈 원인 점검 필요"]
eyebrow: 목표 달성

# 최근 3개월 증가분 대부분은 영남·수도권 팀에서 나옴
chart: waterfall
data: monthly.csv
x: team
y: revenue_100m_krw
bridge: {month: [latest-3, latest]}
suffix: " 매출"
unit: 억 원
takeaways: ["영남팀 증가가 가장 큼", "중부팀만 소폭 감소"]
eyebrow: 증감 요인

# 요청 사항
ask: 호남팀 거래처 이탈 점검과 4분기 목표 재조정 승인
next:
  - {t: 호남팀 이탈 거래처 원인 분석, who: 영업기획팀, when: 10월 3주}
  - {t: 4분기 팀별 목표 재조정안 보고, who: 영업기획팀, when: 10월 말}
