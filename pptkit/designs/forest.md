---
name: forest
description: 고객 제안·서비스 소개형. 짙은 숲색과 크림, 따뜻한 산호색 강조. 신뢰감은 지키면서 딱딱하지 않은 톤.
formality: friendly
use_for: [pitch, proposal, sales, education]
colors:
  bg: "F5F2EA"
  dark: "1F3326"
  ink: "1E2820"
  body: "4F584F"
  muted: "8C9389"
  accent: "D9603B"
  card: "EBE6D9"
  line: "D9D2C0"
  neutral_series: "C5C9BE"
  positive: "1F8A5B"
  negative: "C0392B"
series: ["1F9D6B", "E2683C", "2A78D6", "E0A100"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 40, title: 26, eyebrow: 12, message: 15, body: 15, metric: 38, small: 10}
shape: {radius: 0.22, border_pt: 0}    # radius in inches
cover: {bg: dark, decor: circles}
section: dark
closing: dark
bullet: "•"
---

# forest

## 개요

고급 제품 소개 페이지 같은 따뜻한 재질감을 슬라이드로 옮겼다. 짙은 숲색이 표지와 결론을 감싸고, 본문은 크림 바탕이다. 산호색 하나가 숫자와 핵심 단어를 맡는다. 카드는 테두리 없이 둥근 색면으로만 구분해서 부드럽게 보인다. "너무 딱딱하지 않게"라는 요청에 맞는 기본 디자인이다.

출처: `references/design/slides/grove.md`, `references/design/slides/mat.md`(frontend-slides, MIT). 평가 1회차 기준선(평가 4)의 친근한 배색도 참고했다.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `dark` | 표지, 섹션, 결론 바탕 |
| `bg` | 본문 바탕 |
| `accent` | 숫자, 섹션 라벨, 단계 번호, 추천 표시 |
| `card` | 테두리 없는 둥근 카드 |

## 컴포넌트

- 카드는 둥근 모서리(큰 반경), 테두리 없음.
- 단계와 번호는 산호색 원 안에 흰 숫자.
- 문체는 경어체나 해요체와 어울린다. 개조식과도 쓸 수 있지만 제목은 대화체 결론 문장이 잘 맞는다.

## 하지 말 것

- 산호색을 제목 전체에 쓰지 않는다.
- 카드에 테두리와 그림자를 함께 넣지 않는다.
