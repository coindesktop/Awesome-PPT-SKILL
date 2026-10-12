---
brief: brief.yaml
storyline: report/scr
source: "가상 예시 데이터, 2026년 9월 말 기준"
date: 2026-10-05
author: ERP 고도화 PMO
eyebrow: ERP 고도화 PMO 월간 보고
labels: {month: 월, kind: 구분, amount_100m_krw: 금액, area: 영역, week: 주차, new: 신규 이슈}
---

# ERP 고도화 프로젝트 9월 진척 보고
pattern: cover
subtitle: 데이터 이관 지연 대응을 위한 전담 인력 투입·오픈 일정 조정 승인 요청

# 진척률 65.5%로 계획 대비 2주 지연, 예산 집행은 정상 범위임
eyebrow: 상황
message: 지연은 데이터 이관 한 영역에 집중되고, 비용·타 영역은 계획 수준을 유지함
kpis:
  - {label: 전체 진척률, value: "65.5%", note: "계획 71.0%"}
  - {label: 예산 집행률, value: "98.7%", note: "60.2억 / 61.0억 원"}
  - {label: 오픈 이슈, value: "36건", note: "데이터 이관 23건 (63.9%)"}
  - {label: 일정 편차, value: "2주", note: "오픈 11/30 → 12/14"}
callout:
  - 이관 실적 38%(계획 60%), 오픈 이슈 20건 → 36건으로 증가함
callout_title: 시사점

# 9개 과제 중 데이터 이관만 지연, 인터페이스는 주의 단계임
pattern: status-table
rows:
  - {item: 요구사항 정의, owner: PMO·현업, due: 5/31, status: done, note: 승인 완료}
  - {item: To-Be 설계, owner: 컨설팅팀, due: 6/30, status: done, note: 승인 완료}
  - {item: "개발(FI/CO)", owner: 재무개발팀, due: 9/30, status: done, note: 단위 테스트 완료}
  - {item: "개발(MM/SD)", owner: 물류개발팀, due: 10/10, status: green, note: 계획대로 진행}
  - {item: 인터페이스 개발, owner: IF팀, due: 10/15, status: amber, note: 외부 API 사양 확정 대기}
  - {item: 데이터 이관, owner: 이관팀, due: 10/31, status: red, note: "2주 지연, 전담 인력 투입 요청"}
  - {item: 통합 테스트, owner: QA팀, due: 11/27, status: green, note: 이관 일정에 연동}
  - {item: 사용자 교육, owner: 변화관리팀, due: 12/04, status: green, note: 교육 계획 수립}
  - {item: "오픈(Go-Live)", owner: PMO, due: 12/14, status: amber, note: 11/30에서 조정안}
eyebrow: 상황
source: 가상 예시 데이터

# 데이터 이관 2주 지연이 통합 테스트·교육·오픈으로 전이됨
eyebrow: 상황
message: 조정안 기준 일정 (오픈 11/30 → 12/14, 안정화 종료일 12/31은 유지)
pattern: gantt
data: tasks.csv

# 예산은 계획 대비 98.7% 집행으로 정상 범위임
eyebrow: 상황
message: 9월 누적 집행 60.2억 원 / 계획 61.0억 원 (총예산 96.0억 원)
chart: line-trend
data: budget.csv
x: month
y: amount_100m_krw
series: kind
unit: 억 원
pattern: chart-takeaway
takeaways:
  - 월별 집행은 계획 대비 96.7~102.5% 범위에서 안정적임
  - 2주 조정에 따른 추가 비용은 예비비 범위 내 검토 필요

# 9월 신규 이슈 88건 중 41건(46.6%)이 데이터 이관에서 발생함
eyebrow: 문제
message: 데이터 이관 신규 이슈는 주 6건에서 14건으로 늘고, 타 영역은 주 1~5건 수준 유지
pattern: heatmap-table
data: issues.csv
rows: area
cols: week
val: new
unit: 건

# 지연 원인은 데이터 품질·이관 역량·일정 구조 세 갈래로 분해됨
eyebrow: 원인
message: 근본 원인은 이관 전담 인력 부재로, 품질 정제와 검증이 개발 업무에 밀림
pattern: logic-tree
root: ERP 오픈 2주 지연
branches:
  - {label: 데이터 품질, leaves: [레거시 마스터 중복·누락 다수, 정제 기준에 대한 현업 합의 지연]}
  - {label: 이관 역량, leaves: [이관 전담 인력 부재(개발 겸직), 이관 리허설 일정 미확보]}
  - {label: 일정 구조, leaves: [이관 완료 후 통합 테스트 착수, 오픈 전 일정 버퍼 부재]}

# 전담 인력 3명 투입과 2주 조정이 품질·혼선 리스크가 가장 낮은 대안임
eyebrow: 대안
message: 현 일정 고수는 품질 리스크, 단계 오픈은 이중 운영 부담이 큼
pattern: compare-table
corner: 기준
options: [현 일정 고수, 단계 오픈(범위 축소), 전담 3명 + 2주 조정]
criteria:
  - {label: 오픈 일정, values: [11/30 유지, 일부 모듈 12월, 12/14 오픈]}
  - {label: 데이터 품질 리스크, values: [○, ◐, ●]}
  - {label: 현업 업무 혼선, values: [◐, ○, ●]}
  - {label: 추가 투입 자원, values: [●, ◐, ◐]}
  - {label: 종합 평가, values: [○, ◐, ●]}
recommend: 3

# 10월 전담 인력 투입 후 11월 이관 리허설로 12/14 오픈을 확보함
eyebrow: 실행
message: 매주 이관 지표를 보고하고, 11월 말 오픈 판정 회의(Go/No-Go)에서 최종 확정
pattern: roadmap
phases: [10월, 11월, 12월]
lanes:
  - {name: 데이터 이관, cells: [전담 3명 투입·정제 기준 확정, 2·3차 이관 리허설, 최종 이관·검증]}
  - {name: 테스트, cells: [단위 테스트 마감, 통합 테스트(~11/27), 사용자 인수 테스트]}
  - {name: 오픈 준비, cells: [교육 계획 수립, 사용자 교육(11/16~), 12/14 오픈·안정화]}
  - {name: 관리, cells: [주간 이관 지표 보고, 오픈 판정 회의, 운영 전환]}
now: 1

# 이관 품질 미달과 테스트 결함 급증을 최우선 리스크로 관리함
eyebrow: 리스크
message: 전담 인력 투입으로 두 리스크의 발생 가능성을 낮추는 것이 핵심임
pattern: matrix-2x2
x_axis: 발생 가능성
y_axis: 영향도
quadrants: [대응 계획 수립, 즉시 대응, 모니터링, 일상 관리]
items:
  - {label: 이관 데이터 품질 미달, x: 0.85, y: 0.88}
  - {label: 통합 테스트 결함 급증, x: 0.76, y: 0.62}
  - {label: 전담 인력 확보 지연, x: 0.12, y: 0.72}
  - {label: 대외 인터페이스 지연, x: 0.2, y: 0.45}
  - {label: 현업 교육 참여 저조, x: 0.8, y: 0.3}
  - {label: 인프라 성능 저하, x: 0.1, y: 0.1}
callout:
  - 품질 미달은 오픈 판정 회의의 필수 판정 항목으로 지정함
  - 인력 확보 지연 시 협력사 예비 인력으로 대체함

# 요청 사항
pattern: closing
ask: 데이터 이관 전담 인력 3명 투입과 오픈 일정 2주 조정(11/30 → 12/14) 승인 요청
support: 예산 집행은 정상 범위로, 일정 조정 외 범위·품질 기준은 변경 없음
next:
  - {t: 전담 인력 3명 투입 확정, who: PMO·인사팀, when: 10/12}
  - {t: 조정 일정 현업·협력사 공지, who: PMO, when: 10/14}
  - {t: 2차 이관 리허설, who: 이관팀, when: 11/06}
  - {t: 오픈 판정 회의, who: CIO·PMO, when: 11/30}
