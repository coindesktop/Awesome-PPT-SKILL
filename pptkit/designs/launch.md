---
name: launch
description: 스타트업 피칭형. 전 장 어두운 바탕, 큰 글자, 보라 강조 하나. 무대 화면과 투자자 미팅 화면에서 또렷하게 읽힘.
formality: neutral
use_for: [pitch, ir, demo-day]
colors:
  bg: "0E1015"
  dark: "0E1015"
  surface: "151821"
  ink: "F4F5F8"
  body: "B6BCC8"
  muted: "7C8494"
  accent: "8B7CFF"
  card: "181C26"
  line: "2A303D"
  neutral_series: "3A4150"
  positive: "3DDC97"
  negative: "FF6B6B"
series: ["8B7CFF", "3DDC97", "FFB547", "4FC3F7"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 50, title: 30, eyebrow: 13, message: 17, body: 17, metric: 48, small: 10}
shape: {radius: 0.12, border_pt: 0.75}  # radius in inches
cover: {bg: dark, decor: orb}
section: dark
closing: dark
bullet: "•"
style: {chart: tint, callout: tint, kpi: strip}
---

# launch

## 개요

Linear와 Vercel 같은 개발자 도구 회사의 발표 화면을 기준으로 한 피칭용 시스템이다. 모든 장표가 같은 어두운 바탕이라
무대 조명 아래에서도 눈이 편하고, 큰 숫자와 짧은 제목이 먼저 보인다. 강조색은 보라 하나만 쓰고, 차트 계열색은 어두운
바탕에서 대비를 확인한 네 가지를 쓴다.

출처: `references/design/web/linear.app.md`(awesome-design-md, MIT)의 어두운 표면 단계와 단일 강조색 원칙.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `bg` / `dark` | 모든 장표 바탕 |
| `surface` / `card` | 카드·표 바탕. 바탕보다 한 단계 밝게 해서 층을 만든다 |
| `ink` / `body` / `muted` | 제목, 본문, 보조 글자. 본문도 바탕 대비 9:1 이상 |
| `accent` | 숫자, 라벨, 강조 계열 하나 |

## 타이포그래피와 레이아웃

- 제목 30pt, 핵심 숫자 48pt 이상. 발표(present) 밀도가 기본이라 본문은 17pt.
- 표지는 오른쪽에 강조색 원을 겹친 빛무리(orb) 하나만 둔다.
- 카드 모서리 0.12in, 테두리는 가는 선(`line`)으로 층만 구분한다.

## 하지 말 것

- 밝은 바탕 장표를 섞지 않는다.
- 강조색을 넓은 면적에 채우지 않는다(배지·숫자·한 계열만).
