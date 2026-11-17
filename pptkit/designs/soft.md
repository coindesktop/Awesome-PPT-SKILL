---
name: soft
description: 부드러운 제품형. 옅은 회색 바탕 위에 흰 카드를 그림자로 띄우고, 큰 둥근 모서리와 인디고 강조를 쓴다.
formality: friendly
use_for: [sales, education, report, product]
colors:
  bg: "F3F5F9"
  dark: "1E1B4B"
  surface: "FFFFFF"
  ink: "1A2233"
  body: "465064"
  muted: "8D97A8"
  accent: "4F46E5"
  card: "E9ECF5"
  line: "DFE3EC"
  neutral_series: "C9CEDA"
  positive: "0E9F6E"
  negative: "E0484D"
series: ["4F46E5", "F28C28", "13A89E", "B5479F"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 40, title: 24, eyebrow: 12, message: 15, body: 15, metric: 36, small: 10}
shape: {radius: 0.16, border_pt: 0, card: elevated, shadow: {blur: 18, dist: 5, alpha: 10}}
cover: {bg: light, decor: orb}
section: accent
closing: dark
bullet: "•"
style: {header: plain, chart: tint, table_head: card, callout: card, kpi: plain}
---

# soft

## 개요

제품 대시보드에서 온 시스템이다. 바탕을 옅은 회색으로 낮추고 내용은 흰 카드에 올린 뒤, 카드에 부드러운 그림자를
주어 띄운다(`shape.card: elevated`). 모서리를 크게 둥글리고 선은 거의 쓰지 않는다. 강조는 인디고 하나이며, 섹션
장표는 인디고로 가득 채운다.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `bg` | 옅은 회색 바탕. 흰 카드가 떠 보이게 한다 |
| `surface` | 카드, 표 바탕(흰색) |
| `accent` | 라벨, 큰 숫자, 강조 막대, 섹션 장표 바탕 |
| `card` | 표 머리, 진척 막대의 빈 구간처럼 카드 안에서 한 단계 낮은 면 |
| `series` | 인디고·주황·청록·자주. 흰 바탕과 회색 바탕 모두에서 검증 통과(색각 이상 인접 쌍 ΔE 8.8 이상) |

## 스타일 스위치

| 키 | 값 | 효과 |
|---|---|---|
| `shape.card` | `elevated` | 흰 카드 + 그림자(`shape.shadow`: blur 18pt, 아래로 5pt, 불투명도 10%) |
| `shape.radius` | `0.16` | 큰 둥근 모서리 |
| `chart` | `tint` | 강조 외 막대는 인디고의 옅은 단계 |

## 하지 말 것

- 카드에 외곽선을 더하지 않는다. 그림자와 선을 함께 쓰면 무거워진다.
- 바탕을 흰색으로 바꾸지 않는다. 카드가 바탕과 구분되지 않는다.
