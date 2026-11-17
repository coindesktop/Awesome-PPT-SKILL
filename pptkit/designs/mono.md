---
name: mono
description: 흑백 에디토리얼. 흰 바탕에 검정 글자와 가는 선만 쓰고, 카드는 채우지 않고 외곽선으로 구분. 색은 여러 계열 차트에만.
formality: formal
use_for: [report, proposal, strategy, review]
colors:
  bg: "FFFFFF"
  dark: "111111"
  surface: "FFFFFF"
  ink: "0A0A0A"
  body: "3D3D3D"
  muted: "8C8C8C"
  accent: "111111"
  card: "F4F4F4"
  line: "D4D4D4"
  neutral_series: "CFCFCF"
  positive: "0F8A5F"
  negative: "D93838"
series: ["1F5EDC", "F28C28", "13A89E", "8E5CD9"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 46, title: 26, eyebrow: 12, message: 15, body: 15, metric: 40, small: 10}
shape: {radius: 0, border_pt: 1, card: outline}
cover: {bg: light, decor: rule}
section: dark
closing: dark
bullet: "•"
style: {header: rule, chart: neutral, table_head: plain, callout: card, kpi: plain}
---

# mono

## 개요

인쇄물 같은 흑백 시스템이다. 색으로 꾸미지 않고 글자 크기, 굵기, 여백, 가는 선으로 위계를 만든다. 카드는 바탕을
채우지 않고 1pt 외곽선으로만 구분하고(`shape.card: outline`), 모서리는 둥글리지 않는다. 표 머리는 채우지 않고
굵은 밑줄 하나로 구분한다. 강조는 검정 채움 하나뿐이다(요약 첫 숫자 카드, 강조 막대).

## 색 역할

| 토큰 | 역할 |
|---|---|
| `accent` | 검정. 라벨, 큰 숫자, 강조 막대, 강조 카드 채움 |
| `line` | 카드 외곽선, 표 행 구분선, 제목 아래 선 |
| `neutral_series` | 단일 계열 차트에서 강조하지 않는 막대 |
| `series` | 여러 계열 차트에만 색을 쓴다: 파랑·주황·청록·보라(corporate와 같은 검증된 조합) |

## 스타일 스위치

| 키 | 값 | 효과 |
|---|---|---|
| `shape.card` | `outline` | 카드 바탕 없음, 1pt 외곽선 |
| `header` | `rule` | 제목 아래 가는 선 |
| `table_head` | `plain` | 표 머리 채움 없음, 굵은 밑줄 |
| `chart` | `neutral` | 강조 외 막대는 회색 |

## 하지 말 것

- 강조색을 추가하지 않는다. 색이 필요한 곳은 여러 계열 차트와 증감(▲▼) 표시뿐이다.
- 카드에 그림자나 채움을 넣지 않는다.
