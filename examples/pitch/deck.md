---
brief: brief.yaml
storyline: pitch/vc-seed
date: 2026-10
author: 리포트봇 · 김대표
labels: {arr_100m_krw: ARR, customers: 고객사}
---

# 리포트봇
pattern: cover
subtitle: 엑셀만 올리면 경영 보고서가 완성되는 AI 보고 자동화
eyebrow: Seed Round 2026

# 중견기업 기획팀은 매달 40시간을 보고서 복붙에 씁니다
figure: 40시간
label: 기획·재무팀 1인이 매달 보고서 작성에 쓰는 시간
support: 고객 인터뷰 32곳 평균입니다.
points:
  - {icon: refresh-cw, title: 같은 표를 매달 다시 만듭니다, desc: "ERP·엑셀·메일에서 숫자를 모아 붙이는 데 대부분의 시간이 갑니다"}
  - {icon: triangle-alert, title: 숫자 하나가 틀리면 처음부터, desc: "원천과 보고서 숫자를 대조할 방법이 없어 검토가 반복됩니다"}
  - {icon: hourglass, title: 정작 분석할 시간이 없습니다, desc: "해석과 판단에 써야 할 시간이 복사·붙여넣기로 사라집니다"}
eyebrow: 문제

# 데이터 연결부터 보고서까지, 사람은 검토만 합니다
pillars:
  - {icon: plug, title: 한 번 연결, desc: "ERP·엑셀·구글 시트를 한 번 연결하면 매달 자동으로 갱신됩니다"}
  - {icon: file-text, title: 한국식 보고서, desc: "개조식 문장, 결론 먼저, 회사 양식 그대로 초안을 만듭니다"}
  - {icon: shield-check, title: 숫자 검증, desc: "원천 데이터와 보고서 숫자를 대조해 틀린 값을 먼저 잡습니다", note: "파일럿 기관 오류 0건"}
eyebrow: 해결

# 지금 가능해진 이유: 모델, 데이터, 규제가 동시에 바뀌었습니다
pillars:
  - {figure: "10배", title: 한국어 문서 생성 품질, desc: "2024년 대비 장문 한국어 보고서 정확도가 크게 올랐습니다"}
  - {figure: "78%", title: 클라우드 ERP 전환, desc: "중견기업 ERP의 클라우드 전환으로 API 연결이 쉬워졌습니다"}
  - {figure: "2026", title: 공시·ESG 보고 의무, desc: "보고 빈도와 항목이 늘어 자동화 수요가 커졌습니다"}
eyebrow: 왜 지금

# 국내 보고 자동화 시장은 1.2조 원, 첫 목표는 2,400억 원입니다
tam: {value: 1.2조 원, label: 국내 기업 보고·문서 자동화}
sam: {value: "2,400억 원", label: "직원 300~2,000명 중견기업 기획·재무 부서"}
som: {value: 120억 원, label: "3년 내 1,000개사 확보 시"}
source: 가상 예시 데이터
eyebrow: 시장

# 12개월 만에 ARR 12.8억 원, 고객사 171곳으로 성장했습니다
metrics:
  - {value: 12.8억, label: ARR (2026년 9월)}
  - {value: 10.7배, label: 12개월 ARR 성장}
  - {value: 171곳, label: 유료 고객사}
chart: column-trend
data: traction.csv
x: month
y: arr_100m_krw
highlight: 2026-09
unit: 억 원
source: 가상 예시 데이터
eyebrow: 트랙션

# 팀 단위 구독으로 팔고, 엔터프라이즈로 확장합니다
tiers:
  - {name: 팀, price: 49만 원, unit: /월, for: 기획·재무 1개 팀, features: [사용자 10명, 표준 템플릿 30종, 엑셀·구글 시트 연결]}
  - {name: 비즈니스, price: 149만 원, unit: /월, for: 여러 부서, features: [사용자 50명, 회사 양식 학습, ERP 연결, 숫자 검증], highlight: true}
  - {name: 엔터프라이즈, price: 별도 협의, for: 전사 도입, features: [사용자 무제한, 사내 설치, 전담 매니저]}
eyebrow: 비즈니스 모델

# 설치 없이 2주, 한국식 보고서를 그대로 만드는 곳은 우리뿐입니다
options: [엑셀 수작업, BI 도구, 외주 보고서, 리포트봇]
criteria:
  - {label: 도입 기간, values: [즉시, 3개월, 건별 계약, 2주]}
  - {label: 작성 시간 절감, values: [○, ◐, ●, ●]}
  - {label: 한국식 보고서 양식, values: [◐, ○, ◐, ●]}
  - {label: 숫자 오류 방지, values: [○, ●, ◐, ●]}
  - {label: 월 비용, values: [인건비, 300만 원+, 500만 원+, 49만 원~]}
recommend: 4
eyebrow: 경쟁

# 기업 보고 업무를 직접 해 본 사람들이 만듭니다
members:
  - {name: 김도윤, role: CEO, bio: [전 대기업 경영기획팀 8년, 월간 경영 보고 120회 작성], note: 문제를 직접 겪은 사람}
  - {name: 이서연, role: CTO, bio: [전 핀테크 데이터 플랫폼 리드, 문서 생성 모델 연구 5년]}
  - {name: 박준호, role: 사업 총괄, bio: [전 B2B SaaS 영업 이사, 중견기업 고객 200곳 영업]}
advisors: [최민정 (회계사, 전 Big4 감사), 정우석 (전 ERP 기업 CPO)]
eyebrow: 팀

# 시드 20억 원으로 18개월 안에 ARR 60억 원을 만들겠습니다
round: Seed · 2026년 4분기
amount: 20억 원
use:
  - {label: 제품 개발 (ERP 연결·검증 엔진), pct: 45}
  - {label: 영업·마케팅, pct: 35}
  - {label: 운영·인프라, pct: 20}
milestones: ["ARR 60억 원, 고객사 800곳", "ERP 5종 공식 연동", "시리즈 A 준비 (2028년 상반기)"]
eyebrow: 투자 요청
