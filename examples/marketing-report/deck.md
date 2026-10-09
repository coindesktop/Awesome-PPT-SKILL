---
brief: brief.yaml
storyline: report/exec-report
design: corporate
source: "가상 예시 데이터 (채널별 월간 마케팅 실적, 2026.1~9)"
date: 2026-10-08
author: 마케팅팀
eyebrow: 3분기 마케팅 성과 보고
labels: {month: 월, quarter: 분기, channel: 채널, spend_10k_krw: 집행액, revenue_10k_krw: 기여 매출, leads: 리드, mql: MQL, sql: SQL, deals: 계약}
---

# 2026년 3분기 디지털 마케팅 캠페인 성과 보고
pattern: cover
subtitle: 채널별 성과 분석과 4분기 예산 재배분안

# 3분기 기여 매출 10.2% 증가, 성과는 검색광고·웨비나에 집중됨
pattern: exec-summary
eyebrow: 요약
points:
- 3분기 기여 매출 13.2억 원, 전분기 대비 10.2% 증가함
- 집행액 증가는 3.4%에 그쳐 ROAS 2.9배→3.1배로 개선됨
- 검색광고·웨비나가 예산 45.6%로 매출 74.2%를 창출함
- SNS·디스플레이는 예산 40.3%, 매출 8.0%로 효율 저조함
- 4분기 예산을 검색광고·웨비나로 재배분 승인 요청함
numbers:
- {value: "13.2억 원", label: 3분기 기여 매출}
- {value: "3.1배", label: 3분기 ROAS}
- {value: "74.2%", label: 검색광고·웨비나 매출 비중}

# 매출·계약은 10% 성장, 집행 효율 지표도 함께 개선됨
pattern: kpi-tiles
eyebrow: 핵심 지표
message: 집행액은 3.4% 증가에 그쳤으나 매출·계약은 10% 이상 성장함
kpis:
- {icon: banknote, label: 기여 매출 (원), value: "13.2억", delta: "+10.2%", note: "전분기 12.0억 원", spark: [33790, 35250, 41910, 36810, 39450, 43670, 41660, 43940, 46600]}
- {icon: handshake, label: 신규 계약, value: "127건", delta: "+10.4%", note: "전분기 115건", spark: [34, 34, 40, 34, 38, 43, 41, 41, 45]}
- {icon: trending-up, label: ROAS, value: "3.1배", note: "전분기 2.9배", spark: [2.6, 2.6, 3.1, 2.7, 2.9, 3.2, 2.9, 3.1, 3.3]}
- {icon: target, label: 계약당 CAC (원), value: "336만", good: down, note: "전분기 359만 원", spark: [389.4, 398.8, 340.8, 402.6, 362.4, 322.1, 345.9, 349.3, 315.6]}

# 월 기여 매출은 9월 4.66억 원으로 연중 최고치를 기록함
pattern: chart-table
eyebrow: 추이
message: 1월 대비 1.4배, 월평균 4.1% 복리 성장
chart: column-trend
data: campaign_2026.csv
x: month
y: revenue_10k_krw
highlight: 2026-09
growth: true
unit: 만 원
takeaways:
- 3월·6월 분기 말 계약 집중으로 상승 폭 큼
- 3분기는 7월 일시 감소 후 2개월 연속 증가함

# 3분기 리드 6,158건 중 127건이 계약으로 전환됨
pattern: funnel
eyebrow: 전환 퍼널
message: SNS는 리드 비중 30.5%에 매출 6.0%, 웨비나는 리드 10.1%에 매출 32.8%
stages:
- {label: 리드, value: 6158}
- {label: MQL, value: 1403}
- {label: SQL, value: 531}
- {label: 계약, value: 127}

# SNS·디스플레이는 예산의 40.3%를 쓰고 매출은 8.0%만 기여함
pattern: chart-pair
eyebrow: 채널 구조
message: 3분기 채널별 집행액과 기여 매출 비교
data: campaign_2026.csv
unit: 만 원
charts:
- {subtitle: "3분기 채널별 집행액", chart: bar-ranked, x: channel, y: spend_10k_krw, where: {quarter: 2026-Q3}, highlight: SNS}
- {subtitle: "3분기 채널별 기여 매출", chart: bar-ranked, x: channel, y: revenue_10k_krw, where: {quarter: 2026-Q3}, highlight: SNS}

# 검색광고·웨비나·제휴는 분기 10% 이상 성장, 디스플레이는 역성장함
pattern: heatmap-table
eyebrow: 채널 상세
message: "채널 × 분기 기여 매출 (분기 복리 성장률: 검색광고 12.9%, 디스플레이 -15.2%)"
data: campaign_2026.csv
rows: channel
cols: quarter
val: revenue_10k_krw
unit: 만 원

# 채널 간 효율 격차가 커 예산 재배분 여지가 큼
pattern: bullets-callout
eyebrow: 시사점
bullets:
- 3분기 ROAS 웨비나 6.9배, 검색광고 4.1배로 평균 3.1배 상회
- SNS 0.8배, 디스플레이 0.4배로 집행액 대비 매출 미달
- 계약당 CAC 웨비나 149만 원, 디스플레이 2,513만 원
- 디스플레이 매출은 3분기 27.4% 감소해 하락세 지속
callout_title: 대응 방향
callout:
- SNS·디스플레이 예산 일부를 검색광고·웨비나로 이동
- 총 예산은 동결, 브랜드 노출 최소 예산은 유지

# 4분기는 총액 동결 하에 B안(부분 재배분)을 권고함
pattern: compare
eyebrow: 재배분안
recommend: 2
columns:
- title: A안 현행 유지
  items: [추가 검토 부담 없음, 저효율 채널 비중 40% 유지, 4분기 ROAS 개선 제한적]
- title: B안 부분 재배분
  items: [SNS·디스플레이 예산 절반을 이동, 검색광고 키워드 확장·웨비나 월 2회, 브랜드 노출 최소 예산 유지]
- title: C안 전면 재배분
  items: [SNS·디스플레이 집행 중단, 단기 효율은 최대, 신규 리드 유입 공백 우려]

# 요청 사항
pattern: closing
ask: 4분기 예산의 검색광고·웨비나 재배분(B안) 승인 요청
support: 총 예산 동결, 11월 말 중간 점검 후 추가 조정
next:
- {t: "채널별 재배분 예산안 확정", who: "마케팅팀", when: "10월 3주"}
- {t: "검색광고 키워드 확장 집행", who: "퍼포먼스 파트", when: "10월 4주"}
- {t: "웨비나 월 2회로 확대 편성", who: "콘텐츠 파트", when: "11월부터"}
- {t: "재배분 효과 중간 점검 보고", who: "마케팅팀", when: "11월 말"}
