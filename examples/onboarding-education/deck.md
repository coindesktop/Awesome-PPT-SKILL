---
brief: brief.yaml
storyline: education/lecture
design: forest
source: "가상 예시 데이터"
date: 2026-10-08
author: 인재개발팀
eyebrow: 신입사원 온보딩
labels: {month: 월, channel: 채널, sales: 매출, store: 매장, size: 규모, revenue: 매출, margin: 이익률}
---

# 신입사원 데이터 리터러시 첫걸음
pattern: cover
subtitle: "90분 동안 지표 고르기부터 보고서 한 장까지 함께 익혀요"
notes: "반가워요, 오늘은 숫자를 읽고 쓰는 첫걸음을 같이 떼 봅니다. 어려운 통계는 하나도 없으니 편하게 들어 주세요."

# 오늘 90분 동안 이렇게 진행해요
pattern: agenda
items:
- 좋은 지표 고르기 (20분)
- 평균의 함정과 가중 평균 (20분)
- 질문에 맞는 차트 고르기 (15분)
- 보고서 한 장 쓰는 법 (25분)
- 정리와 이번 주 과제 (10분)
notes: "크게 세 파트로 나눠 진행해요. 파트마다 실제 예시 데이터를 같이 보면서 연습합니다."

# 좋은 지표 고르기
pattern: section
number: 1
subtitle: "무엇을 셀지 정하는 게 분석의 절반이에요"
notes: "첫 번째 파트는 지표 고르기예요. 숫자를 보기 전에 무엇을 볼지부터 정해 봅니다."

# 좋은 지표는 보고 나면 할 일이 떠오르는 숫자예요
pattern: compare
recommend: 1
columns:
- title: 좋은 지표
  items:
  - 숫자가 바뀌면 할 일도 바뀌어요
  - 비율·단위가 있어 서로 비교돼요
  - 기준 기간이 분명해요
  - 정의를 한 줄로 설명할 수 있어요
- title: 나쁜 지표
  items:
  - 보기만 좋고 할 일이 없어요
  - 누적값이라 늘 오르기만 해요
  - 사람마다 정의가 달라요
  - 기간 없이 숫자만 있어요
notes: "누적 가입자 수처럼 계속 오르기만 하는 숫자는 기분은 좋지만 할 일을 알려 주지 않아요. 지표를 고를 때는 이 숫자가 떨어지면 나는 뭘 할지 먼저 떠올려 보세요."

# 평균의 함정과 차트 고르기
pattern: section
number: 2
subtitle: "같은 데이터도 계산과 그림에 따라 다르게 읽혀요"
notes: "두 번째 파트예요. 평균 하나, 차트 하나만 바꿔도 결론이 달라지는 걸 직접 확인해 봅니다."

# 이익률 평균은 16%가 아니라 9.4%예요
pattern: key-message
statement: "매장 5곳 이익률을 그냥 평균 내면 16%, 매출로 가중하면 9.4%예요"
support: "매출의 80.8%를 내는 대형 매장 이익률이 6.9%라서, 작은 매장의 높은 이익률이 단순 평균을 부풀려요"
source: "가상 예시 데이터 (매장 5곳)"
notes: "연남점처럼 매출이 작은 매장도 평균에서는 한 표를 똑같이 가져가요. 비율을 평균 낼 때는 늘 무엇으로 가중할지 먼저 물어보세요."

# 온라인 비중이 28.6%에서 44.4%로 커진 건 100% 누적 차트에서 잘 보여요
message: "추세가 궁금하면 선 그래프, 비중이 궁금하면 100% 누적 막대를 쓰면 돼요"
data: monthly_sales.csv
unit: 백만 원
charts:
- {subtitle: "추세를 볼 때 · 채널별 월 매출", chart: line-trend, x: month, y: sales, series: channel}
- {subtitle: "비중을 볼 때 · 채널별 매출 구성비", chart: stacked-share, x: month, y: sales, series: channel}
notes: "왼쪽과 오른쪽은 완전히 같은 데이터예요. 왼쪽에서는 온라인이 늘었다는 것만 보이지만, 오른쪽에서는 비중이 절반 가까이 왔다는 게 한눈에 보여요."

# 보고서 한 장 쓰는 법
pattern: section
number: 3
subtitle: "읽는 사람이 30초 안에 결론을 알게 써요"
notes: "마지막 파트예요. 오늘 배운 지표와 차트를 보고서 한 장에 담는 방법을 연습합니다."

# 보고서 한 장은 결론부터 쓰고 근거로 받쳐요
pattern: process
highlight: 1
steps:
- {icon: target, title: 결론 한 문장, desc: "제목에 하고 싶은 말을 써요"}
- {icon: chart-column, title: 근거 숫자 3개, desc: "결론을 받치는 숫자만 골라요"}
- {icon: chart-line, title: 차트 하나, desc: "질문에 맞는 차트를 골라요"}
- {icon: arrow-right, title: 다음 행동, desc: "누가 언제 무엇을 할지 써요"}
notes: "많은 분들이 데이터부터 나열하는데, 읽는 사람은 결론부터 알고 싶어 해요. 제목 한 줄만 읽어도 무슨 이야기인지 알 수 있게 써 보세요."

# 제목만 바꿔도 보고서가 결론을 말하기 시작해요
pattern: before-after
before:
  title: 나쁜 제목 (주제만 있어요)
  items:
  - 매장별 이익률 현황
  - 월별 채널 매출 추이
  - 채널별 매출 비중 분석
after:
  title: 좋은 제목 (결론이 있어요)
  items:
  - 대형 매장 이익률 6.9%가 평균을 끌어내려요
  - 12월 온라인 매출이 1월보다 91.7% 늘었어요
  - 온라인 비중이 44.4%까지 커졌어요
notes: "왼쪽 제목은 무엇을 봤는지만 말하고, 오른쪽 제목은 무엇을 알게 됐는지 말해요. 숫자 하나를 넣으면 제목이 훨씬 단단해집니다."

# 오늘 배운 네 가지만 기억하면 돼요
pattern: exec-summary
points:
- 좋은 지표는 할 일을 바꾸는 숫자예요
- 비율의 평균은 가중 평균으로 확인해요
- 차트는 질문(추세·비중)에 맞춰 골라요
- 보고서 제목은 결론 한 문장으로 써요
numbers:
- {value: "9.4%", label: "매출 가중 평균 이익률 (단순 평균 16%)"}
- {value: "44.4%", label: "12월 온라인 매출 비중"}
- {value: "4단계", label: "보고서 한 장 쓰는 순서"}
source: "가상 예시 데이터"
notes: "오늘 내용을 네 줄로 정리했어요. 오른쪽 숫자들은 모두 오늘 같이 본 예시 데이터에서 나왔습니다."

# 이번 주 과제
pattern: closing
ask: "보고서 한 장을 4단계로 써서 금요일까지 공유해 주세요"
support: "다음 주 월요일에 멘토와 함께 피드백해 드려요"
next:
- {t: 내 업무 지표 하나 고르기, who: 각자, when: 수요일}
- {t: 보고서 한 장 초안 공유, who: 각자, when: 금요일}
- {t: 피드백 세션, who: 교육담당·멘토, when: 다음 주 월요일}
notes: "거창하지 않아도 괜찮아요. 오늘 배운 4단계만 지켜서 한 장을 써 보는 게 이번 주 목표예요."
