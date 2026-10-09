---
brief: brief.yaml
storyline: sales/problem-led
source: "가상 예시 데이터, 2025"
date: 2026-10-08
author: 클라우드 WMS 영업팀(가상)
eyebrow: 이천 물류센터 WMS 제안
labels: {month: 월, uph: 시간당 처리량, picking_error_pct: 피킹 오류율}
---

# 이천 센터의 피킹 오류, 8주 파일럿으로 먼저 줄이겠습니다
pattern: cover
subtitle: 한빛물류(가상) 이천 물류센터 클라우드 WMS 도입 제안
notes: 오늘은 이천 센터의 출고 품질 문제를 함께 정의하고, 8주 파일럿으로 검증하는 방안을 말씀드리겠습니다. 결론부터 말씀드리면 1개 센터 파일럿 계약을 요청드립니다.

# 피킹 오류와 수기 실사가 출고 속도를 붙잡고 있습니다
pattern: problem-solution
message: 세 문제 모두 종이와 사람의 기억에 의존하는 작업 방식에서 나옵니다
problem_title: 이천 센터의 현재
solution_title: 클라우드 WMS 도입 후
problems:
  - 피킹 오류율 1.8%로 재작업과 클레임이 반복됩니다
  - 종이 지시서 출고로 리드타임이 길어집니다
  - 재고 실사에 매월 3일 출고가 멈춥니다
solutions:
  - 바코드 스캔 검수로 오피킹을 즉시 막습니다
  - 웨이브·동선 최적화로 출고를 앞당깁니다
  - 순환 실사로 멈춤 없이 재고를 맞춥니다
eyebrow: 문제
notes: 본부장님께서 말씀하신 세 가지 문제를 정리했습니다. 세 문제 모두 사람의 기억과 종이에 의존하는 작업 방식에서 나옵니다. 오른쪽은 WMS가 각 문제를 어떻게 바꾸는지입니다.

# 종이 지시서를 스캔 지시로 바꾸면 오류를 출고 전에 잡습니다
pattern: before-after
before:
  title: 지금의 작업 흐름
  items:
    - 출력한 피킹 리스트를 보고 작업합니다
    - 오류는 고객 클레임으로 뒤늦게 알게 됩니다
    - 월말에 출고를 멈추고 전수 실사합니다
    - 숙련자의 기억에 로케이션을 의존합니다
after:
  title: WMS 도입 후 작업 흐름
  items:
    - PDA가 다음 로케이션과 수량을 지시합니다
    - 스캔이 맞지 않으면 그 자리에서 멈춥니다
    - 작업 중 빈 로케이션부터 순환 실사합니다
    - 신규 인력도 당일 현장에 투입됩니다
eyebrow: 작동 방식
notes: 현장 작업자 입장에서 하루가 어떻게 달라지는지 보여 드립니다. 핵심은 오류를 출고 뒤가 아니라 피킹하는 순간에 잡는다는 점입니다.

# 8주 파일럿은 진단부터 성과 검증까지 4단계로 진행합니다
pattern: process
message: 현행 시스템과 병행하므로 파일럿 기간에도 출고는 멈추지 않습니다
steps:
  - {icon: search, title: "1~2주 현행 진단", desc: "출고 동선·로케이션 실측, 기준 KPI 확정"}
  - {icon: plug, title: "3~4주 연동·설정", desc: "ERP 주문 연동, 로케이션 마스터 등록"}
  - {icon: scan, title: "5~6주 시범 운영", desc: "1개 존부터 시작해 전 존으로 확대"}
  - {icon: badge-check, title: "7~8주 성과 검증", desc: "기준 KPI 대비 결과 보고, 본계약 판단"}
highlight: 4
eyebrow: 작동 방식
notes: 파일럿은 8주이며 현행 시스템을 끄지 않고 병행합니다. 1~2주 차에 오류율과 리드타임 기준값을 함께 확정하고, 8주 차에 그 기준으로 성과를 판단합니다.

# 도입 고객 3곳의 피킹 오류율이 평균 82% 줄었습니다
pattern: big-number
figure: "-82.1%"
label: 피킹 오류율 1.87% → 0.33%
support: 레퍼런스 3개사 평균, 2024년 12월과 2025년 6월 측정
points:
  - {title: "시간당 처리량 +31.9%", desc: "116 UPH에서 153 UPH로 늘었습니다"}
  - {title: "출고 리드타임 -43.0%", desc: "26.3시간에서 15.0시간으로 줄었습니다"}
  - {title: "재고 실사 일수 -80.0%", desc: "월 3.3일에서 0.7일로 줄었습니다"}
source: "가상 예시 데이터, 레퍼런스 3개사(3PL·유통·이커머스) 평균"
eyebrow: 근거
notes: 3PL, 유통, 이커머스 고객사 세 곳의 도입 전후 평균입니다. 세 곳 모두 피킹 오류율이 80% 이상 줄었고, 처리량과 리드타임도 함께 개선됐습니다.

# 고객사 A는 첫 달 적응 후 처리량이 29% 늘었습니다
pattern: traction
metrics:
  - {value: "152 UPH", label: "2025년 6월 시간당 처리량"}
  - {value: "+28.8%", label: "도입 전(1월) 대비"}
  - {value: "-5.1%", label: "가동 첫 달(2월) 적응 구간"}
  - {value: "+17.0%", label: "가동 2개월 차(3월) 반등"}
chart: column-trend
highlight: 2025-06
data: rollout_ramp.csv
x: month
y: uph
unit: UPH
source: "가상 예시 데이터, 고객사 A(3PL) 월별 실적"
eyebrow: 근거
notes: 실제 전환 과정에서는 가동 첫 달 처리량이 5% 정도 떨어지는 적응 구간이 있습니다. 파일럿 일정에 이 구간을 미리 반영해 두었고, 고객사 A는 두 달 차부터 도입 전 수준을 넘었습니다.

# 구축형보다 빠르고, 현행 유지보다 확실하게 오류를 줄입니다
pattern: compare-table
corner: 비교 기준
options: [현행 유지(ERP 재고), 구축형 WMS, 클라우드 WMS(제안)]
criteria:
  - {label: "피킹 스캔 검수", values: [○, ●, ●]}
  - {label: "순환 실사", values: [○, ◐, ●]}
  - {label: "도입 기간", values: ["-", "장기 구축", "8주 파일럿"]}
  - {label: "초기 투자", values: ["없음", "큼", "구독형"]}
  - {label: "기능 업데이트", values: [○, ◐, "자동"]}
recommend: 3
eyebrow: 비교
notes: 검토하실 수 있는 대안 세 가지를 나란히 놓았습니다. 구축형은 기능은 충분하지만 기간과 초기 투자가 큽니다. 클라우드 WMS는 8주 안에 효과를 확인하고 결정하실 수 있습니다.

# 파일럿 비용은 본계약 전환 시 이용료에서 차감합니다
pattern: pricing
message: 8주 파일럿으로 효과를 확인한 뒤 본계약 여부를 결정하실 수 있습니다
tiers:
  - name: 파일럿
    price: "1,600만 원"
    unit: /8주
    for: 1개 센터 효과 검증
    features: [현행 진단·KPI 설계, ERP 주문 연동, PDA 20대 대여, 성과 보고서]
    highlight: true
    badge: 제안
  - name: 스탠다드
    price: "450만 원"
    unit: /센터·월
    for: 본계약 전환 후
    features: [WMS 전 기능, 순환 실사, 대시보드, 업무 시간 지원]
  - name: 엔터프라이즈
    price: 별도 협의
    unit: ""
    for: 3개 센터 이상
    features: [다센터 재고 통합, TMS 연동, 전담 매니저, 24시간 지원]
source: "가상 예시 요금제"
eyebrow: 가격
notes: 이번에 요청드리는 것은 왼쪽의 파일럿입니다. 본계약으로 전환하시면 파일럿 비용은 스탠다드 이용료에서 차감합니다.

# 요청 사항
pattern: closing
ask: 이천 물류센터 8주 파일럿 계약을 10월 중 확정해 주십시오
support: 11월 첫 주 현장 진단을 시작하면 12월 말 성과 보고가 가능합니다
next:
  - {t: "파일럿 계약 검토·확정", who: "한빛물류 구매팀", when: "10월 4주"}
  - {t: "현장 진단 킥오프", who: "당사 컨설턴트", when: "11월 1주"}
  - {t: "시범 운영 중간 점검", who: "양사 공동", when: "12월 1주"}
  - {t: "성과 보고·본계약 판단", who: "양사 공동", when: "12월 4주"}
notes: 10월 중 계약을 확정해 주시면 11월 첫 주에 바로 현장 진단을 시작하겠습니다. 성과 보고는 연말 전에 드릴 수 있습니다.
