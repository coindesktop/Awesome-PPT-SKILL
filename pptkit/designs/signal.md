---
name: signal
description: 전략 브리핑·IR형. 짙은 남색 표지·섹션과 크림색 본문, 금색 강조. 장문 잡지와 정보 브리핑의 절제.
formality: formal
use_for: [pitch, ir, strategy, report]
colors:
  bg: "F3F0E8"
  dark: "1C2644"
  ink: "1A2030"
  body: "4A5262"
  muted: "8A919C"
  accent: "A9772F"
  card: "EAE4D6"
  line: "D8CFBB"
  neutral_series: "C8C2B4"
  positive: "2E7D5B"
  negative: "B8432F"
series: ["2A6FD6", "C9852C", "1BAF7A", "9B59B6"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 40, title: 26, eyebrow: 12, message: 15, body: 15, metric: 36, small: 10}
shape: {radius: 0.03, border_pt: 0.75}  # radius in inches
cover: {bg: dark, decor: rule}
section: dark
closing: dark
bullet: "–"
---

# signal

## 개요

The Economist의 절제와 비공개 정보 브리핑의 긴장감을 섞은 시스템이다. 표지, 섹션, 결론은 짙은 남색 바탕으로 무게를 주고, 본문은 크림색 종이 위에 둔다. 금색은 강조 순간에만 쓴다. 모서리는 거의 각지게 두어 문서처럼 보이게 한다.

출처: `references/design/slides/signal.md`(frontend-slides, MIT).

## 색 역할

| 토큰 | 역할 |
|---|---|
| `dark` | 표지, 섹션, 결론 바탕 |
| `bg` | 본문 바탕 (크림) |
| `accent` | 섹션 라벨, 숫자, 강조. 크림 위 글자 대비를 위해 원본 금색(C8A870)보다 어둡게 조정했다 |
| `card` / `line` | 종이 질감의 카드와 가는 구분선 |

## 타이포그래피와 레이아웃

executive와 같은 크기 체계를 쓴다. 차이는 다음과 같다.

- 불릿 기호는 줄표(–)를 쓴다.
- 카드 모서리는 거의 직각, 테두리는 0.75pt.
- 표지는 남색 바탕에 크림색 제목, 제목 위에 금색 가는 선 하나를 둔다(장식은 이것 하나).

## 하지 말 것

- 남색 바탕을 본문 장표에 쓰지 않는다. 읽는 장표는 크림 바탕이다.
- 금색을 넓은 면적에 채우지 않는다.
