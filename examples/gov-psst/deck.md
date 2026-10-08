---
brief: brief.yaml
storyline: pitch/gov-psst
source: "가상 예시 데이터"
date: 2027-03
author: 팜닥터 대표 정하늘
labels: {revenue_m_krw: 매출 목표, channel: 판로, year: 연도, days_to_diagnosis: 진단 소요일, amount_10k_krw: 사업비}
---

# 팜닥터
pattern: cover
subtitle: "사진 한 장으로 작물 병해충을 진단하고 방제법까지 알려주는 AI 앱"
eyebrow: 2027년 예비창업패키지 발표평가

# 병해충 발견 후 진단까지 평균 8.5일, 그 사이 수확량 12% 손실
pattern: big-number
figure: 8.5일
label: 원예 농가가 병해충을 발견한 뒤 정확한 진단을 받기까지 걸리는 시간
support: "원예 농가 160곳 설문, 응답 수 가중 평균 (가상 예시 데이터)"
points:
  - {title: 진단 창구 부족, desc: "농업기술센터 방문·전화 상담 위주로 대기가 길어짐"}
  - {title: 초기 방제 시기 놓침, desc: "진단 지연 기간 동안 피해 확산, 평균 손실률 12.3%"}
  - {title: 고추 피해 최대, desc: "고추 손실률 14.2%, 사과 진단 소요 11.2일로 최장"}
eyebrow: 1. 문제 인식

# 전문가 판독에 의존하던 진단을 현장 즉시 진단으로 전환
pattern: problem-solution
problem_title: 현재 농가의 진단 방식
solution_title: 팜닥터의 해결 방안
problems:
  - 증상 사진을 지인·온라인 커뮤니티에 올려 추측에 의존함
  - 농업기술센터 방문 진단은 농번기 대기 1주 이상 소요
  - 오진에 따른 농약 과다 살포로 비용·잔류 문제 발생
  - 진단 이력이 남지 않아 다음 작기 예방 관리 불가
solutions:
  - 잎·열매 사진 1장으로 병해충 판별 및 확신도 제시
  - 작물·생육 단계별 등록 농약과 방제 시기 안내
  - 확신도가 낮은 사례는 제휴 전문가 원격 판독으로 연결
  - 필지별 진단 이력 저장, 재발 시기 사전 알림 제공
eyebrow: 1. 문제 인식

# 국내 원예 작물 진단 시장 3,200억 원 중 3년 내 30.5억 원 확보 목표
pattern: market-size
tam: {value: "3,200억 원", label: "국내 원예 농가 병해충 진단·방제 컨설팅 (가정)"}
sam: {value: 780억 원, label: "스마트폰 사용 시설원예 농가 6개 작물 (가정)"}
som: {value: 30.5억 원, label: "2029년 매출 목표 기준 (가정)"}
source: "시장 규모는 가정치, 가상 예시 데이터"
eyebrow: 1. 문제 인식

# 데이터·시제품 확보 완료, 협약 기간 내 실증과 사업화에 집중
message: "시제품 단계까지 자체 자금으로 완료, 정부지원사업비는 실증·사업화 단계에 투입"
pattern: process
steps:
  - {title: "데이터 확보 (완료)", desc: "작물 6종 병해충 이미지 4만 장 수집·라벨링, 농업기술센터 판독 사례 활용"}
  - {title: "시제품 (완료)", desc: "진단 모델 v1과 안드로이드 시제품 앱 개발, 내부 검증 데이터로 성능 점검"}
  - {title: "실증 (협약 기간)", desc: "시설원예 농가 100곳 베타 테스트, 현장 오진 사례 재학습으로 정확도 보완"}
  - {title: "사업화 (협약 기간)", desc: "월 9,900원 유료 구독 출시, 농협·지자체 단체 이용권 시범 공급"}
highlight: 3
eyebrow: 2. 실현 가능성

# 즉시 진단과 방제 처방을 한 번에 제공하는 국내 유일 서비스
pattern: compare-table
options: [기술센터 방문, 해외 진단 앱, 농업 커뮤니티, 팜닥터]
criteria:
  - {label: 진단 소요 시간, values: [1주 이상, 즉시, 수일, 즉시]}
  - {label: 국내 작물·병해충 적합도, values: [●, ◐, ◐, ●]}
  - {label: 등록 농약 처방 안내, values: [●, ○, ○, ●]}
  - {label: 전문가 판독 연계, values: [●, ○, ○, ●]}
  - {label: 농가 비용, values: [무료, 월 1만 원+, 무료, "월 9,900원"]}
recommend: 4
eyebrow: 2. 실현 가능성

# 협약 기간 8개월 내 진단 모델 고도화부터 유료 출시까지 완료
pattern: gantt
data: schedule.csv
eyebrow: 3. 성장 전략

# 3년 매출 목표 30.5억 원, B2C 구독과 B2G 공급이 양대 축
pattern: chart-table
chart: stacked
data: sales_target.csv
x: year
y: revenue_m_krw
series: channel
unit: 백만 원
growth: true
takeaways:
  - "2027년 3억 원에서 2029년 30.5억 원으로 10.2배 성장"
  - "초기에는 농협·지자체 B2G 공급이 매출의 60% 차지"
  - "2029년 B2C 구독 비중 45.2%로 최대 판로 전환"
  - "수출은 2028년 동남아 시설원예 시장 진입 후 13.8%까지 확대"
eyebrow: 3. 성장 전략

# 정부지원사업비 1억 원 중 65%를 외주용역과 인건비에 집중 투입
pattern: funding-ask
amount: 1억 원
round: 정부지원사업비 (협약 기간 8개월)
use:
  - {label: 외주용역비, pct: 35}
  - {label: 인건비, pct: 30}
  - {label: 광고선전비, pct: 15}
  - {label: 재료비, pct: 10}
  - {label: 지급수수료, pct: 10}
milestones:
  - 진단 정확도 고도화 및 앱 개발 외주
  - 개발자 2명 채용, 실증 농가 100곳 운영
  - 유료 구독 출시 및 농협 시범 공급 계약
eyebrow: 3. 성장 전략

# 농학·AI·농업 유통 경험을 갖춘 3인 팀, 협약 기간 내 2명 추가 채용
pattern: team
members:
  - {name: 정하늘, role: 대표, bio: [농학 석사, 농업기술센터 병해충 상담 6년], note: 현장 진단 문제를 직접 겪은 사람}
  - {name: 한도윤, role: CTO, bio: [컴퓨터비전 연구 7년, 이미지 분류 모델 상용화 2건]}
  - {name: 오세린, role: 사업개발, bio: [지역 농협 유통 담당 5년, 지자체 농업 사업 수행 경험]}
  - {name: 신규 채용, role: 개발 2명, bio: [앱 개발자 2027년 7월 채용, 데이터 라벨러 2027년 8월 채용]}
advisors: [국립 농업 연구기관 식물병리 연구원 (기술 자문), 지역 농협 스마트농업팀 (실증 협력)]
eyebrow: 4. 팀 구성

# 요청 사항
pattern: closing
ask: "예비창업패키지 선정 시 협약 기간 내 실증 농가 100곳·유료 구독 출시 달성"
support: "3년 매출 30.5억 원, 협약 기간 내 신규 고용 2명, 농약 오남용 감소 기대"
next:
  - {t: 개발자·라벨러 2명 채용, who: 대표, when: 2027년 8월}
  - {t: 실증 농가 100곳 베타 테스트, who: 사업개발, when: 2027년 10월}
  - {t: 유료 구독 정식 출시, who: 전원, when: 2027년 12월}
eyebrow: 4. 팀 구성
