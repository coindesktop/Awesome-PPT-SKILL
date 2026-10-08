---
name: bold
description: 밝은 피칭형. 흰 바탕, 검은 큰 제목, 선명한 파랑 표지. 인쇄·메일 공유용 IR과 데모데이 겸용.
formality: neutral
use_for: [pitch, ir, sales]
colors:
  bg: "FFFFFF"
  dark: "0B0D12"
  surface: "FFFFFF"
  ink: "0B0D12"
  body: "3D4450"
  muted: "8A919E"
  accent: "2B50FF"
  card: "F3F5F9"
  line: "E3E7EE"
  neutral_series: "C9D0DB"
  positive: "0F9D58"
  negative: "E5484D"
series: ["2B50FF", "FF7A1A", "12B886", "9C6ADE"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 50, title: 30, eyebrow: 13, message: 17, body: 17, metric: 48, small: 10}
shape: {radius: 0.14, border_pt: 0}
cover: {bg: accent, decor: orb}
section: accent
closing: dark
bullet: "•"
style: {header: bar, chart: tint, table_head: dark, callout: tint, kpi: strip}
---

# bold

## 개요

Stripe의 밝은 화면처럼 흰 바탕과 검은 큰 제목, 선명한 파랑 하나로 만든 피칭 시스템이다. 표지와 섹션은 파랑 전면,
본문은 흰 바탕에 테두리 없는 옅은 회색 카드를 쓴다. 인쇄나 PDF 공유에서도 깨끗하게 보인다.

출처: `references/design/web/stripe.md`(awesome-design-md, MIT)의 흰 바탕·단일 채도 강조 원칙.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `accent` | 표지·섹션 전면 바탕, 숫자, 강조 계열 |
| `card` | 테두리 없는 카드 바탕 |
| `dark` | 결론 장표 바탕 |

## 하지 말 것

- 파랑 외의 채도 높은 색을 강조에 쓰지 않는다(차트 계열은 예외).
- 본문 장표 바탕을 파랑으로 칠하지 않는다.
