---
brief: brief.yaml
storyline: report/exec-report
source: "가상 예시 데이터, 2026년 6월 말 기준"
date: 2026-07-10
author: 인사팀
eyebrow: 2026년 상반기 인력 보고
labels: {quarter: 분기, half: 반기, dept: 부문, headcount: 인원, hires: 채용, exits: 퇴사, turnover_pct: 분기 이직률, tenure: 근속, hires_plan: 채용 계획, budget_mkrw: 예산}
---

# 2026년 상반기 인력 현황과 하반기 채용 계획
pattern: cover
subtitle: 연구개발 이직 대응과 하반기 채용 32명·리텐션 예산 승인 요청

# 연구개발 이직률 상승으로 하반기 32명 채용과 리텐션 예산 승인이 필요함
pattern: exec-summary
points:
- 상반기 퇴사 75명이 채용 55명을 넘어 6월 말 인원이 1,026명으로 감소함
- 연구개발 분기 이직률은 상반기 평균 6.2%로 전년 동기 3.0%에서 급등함
- 연구개발 퇴사 25명 중 56%가 1~3년차로 성장 단계 인력 이탈이 핵심임
- 하반기 채용 32명 중 연구개발에 14명을 우선 배정함
- 리텐션은 보상·성장 혼합안(C안, 예산 6.2억 원)을 권고함
numbers:
- {value: "1,026명", label: 6월 말 인원}
- {value: "6.2%", label: 연구개발 분기 이직률(상반기)}
- {value: "32명", label: 하반기 채용 계획}

# 상반기 인력 현황
pattern: section
number: 1
subtitle: 인원·이직률·근속 구조

# 6월 말 인원은 1,026명으로 줄고 분기 이직률은 3.9%까지 오름
pattern: kpi-tiles
kpis:
- {label: "총인원(6월 말, 명)", value: "1,026", delta: "-1.2%", note: 전 분기 대비, spark: [1046, 1050, 1048, 1046, 1038, 1026]}
- {label: "상반기 채용(명)", value: "55", delta: "-10명", note: 전 반기 대비, spark: [33, 35, 32, 33, 27, 28]}
- {label: "상반기 퇴사(명)", value: "75", delta: "+6명", good: down, note: 전 반기 대비, spark: [28, 31, 34, 35, 35, 40]}
- {label: "분기 이직률(2분기)", value: "3.9%", delta: "+0.5%p", good: down, note: 전 분기 대비, spark: [2.7, 3.0, 3.2, 3.3, 3.4, 3.9]}
callout_title: 시사점
callout:
- 채용 감소·퇴사 증가로 2분기 연속 인원 순감, 증가분 대부분이 연구개발임

# 연구개발 이직률이 6.2%로 가장 높아 인원 비중이 19.4%로 낮아짐
pattern: chart-pair
data: headcount.csv
charts:
- {subtitle: "부문별 분기 이직률 (2026년 상반기 평균, %)", chart: bar-ranked, x: dept, y: turnover_pct, agg: wmean, weight: headcount, where: {half: 2026H1}, highlight: 연구개발, unit: "%"}
- {subtitle: "부문별 인원 구성 추이", chart: stacked-share, x: quarter, y: headcount, series: dept}
notes: 분기 이직률 = 분기 퇴사자 ÷ 분기 말 인원. 연구개발 이직률은 2025년 상반기 3.0%, 하반기 4.4%, 2026년 상반기 6.2%로 상승함.

# 퇴사자 75명 중 41%가 1~3년차이며 연구개발은 이 구간에서만 14명이 이탈함
pattern: heatmap-table
message: 2026년 상반기 부문 × 근속 구간별 퇴사자 수 (명)
data: tenure.csv
rows: dept
cols: tenure
val: exits
unit: 명

# 하반기 채용·리텐션 계획
pattern: section
number: 2
subtitle: 채용 32명 배분, 리텐션 대안, 실행 일정

# 하반기 채용 32명 중 연구개발에 14명(44%)을 우선 배정함
pattern: chart-takeaway
chart: bar-ranked
data: hiring_plan.csv
x: dept
y: hires_plan
highlight: 연구개발
unit: 명
takeaways:
- 연구개발은 전장 SW 7명, 배터리 소재 5명, 시험평가 2명을 채용함
- 3분기와 4분기에 16명씩 나누어 채용함
- 생산 9명은 생산기술·설비보전 결원 보충임

# 리텐션 대응은 예산 6.2억 원의 C안(보상·성장 혼합)을 권고함
pattern: compare-table
corner: 구분
options: [A안 보상 중심, B안 성장 중심, C안 보상·성장 혼합]
recommend: 3
criteria:
- {label: 예산(백만 원), values: ["900", "400", "620"]}
- {label: 1~3년차 이탈 대응, values: [◐, ◐, ●]}
- {label: 핵심인재 유지, values: [●, ○, ●]}
- {label: 효과 발현 시점, values: [즉시, 6개월 이후, 3개월 이내]}
- {label: 효과 지속성, values: [○, ●, ◐]}
notes: C안 구성은 핵심인재 리텐션 보너스 260, 1~3년차 연봉 보정 190, 경력개발 트랙 110, 멘토링 60 (백만 원).

# 7월 말 승인 시 11월까지 채용을 마치고 12월에 이직률 효과를 점검함
pattern: gantt
data: hiring_schedule.csv

# 요청 사항
pattern: closing
ask: 하반기 채용 32명(연구개발 14명 우선)과 리텐션 예산 6.2억 원(C안) 승인 요청
support: 승인 시 8월 1일부터 채용 공고와 리텐션 제도 설계를 동시에 착수함
next:
- {t: "채용·예산 승인", who: "경영지원본부장", when: "7월 31일"}
- {t: "연구개발 1차 채용 공고", who: "인사팀·연구소", when: "8월 1일"}
- {t: "리텐션 보너스 기준 확정", who: "인사팀", when: "8월 31일"}
- {t: "이직률 효과 점검 보고", who: "인사팀", when: "12월 31일"}
