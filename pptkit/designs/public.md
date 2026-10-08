---
name: public
description: 공공기관 보고형. 흰 바탕, 남색 머리와 하늘색 보조, □/○ 개조식 기호, 보고 요지 박스.
formality: formal
use_for: [report, review]
colors:
  bg: "FFFFFF"
  dark: "1F3864"
  ink: "1F2A44"
  body: "333B48"
  muted: "7A818C"
  accent: "2E75B6"
  card: "EAF1FA"
  line: "C9D6E8"
  neutral_series: "BFC7D3"
  positive: "1F7A4D"
  negative: "C0392B"
series: ["2E75B6", "ED7D31", "1BAF7A", "EDA100"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 36, title: 24, eyebrow: 12, message: 15, body: 14, metric: 32, small: 10}
shape: {radius: 0, border_pt: 0.75}     # radius in inches
cover: {bg: light, decor: none}
section: tint
closing: light
bullet: "○"
message_box: true
section_numerals: roman
style: {header: rule, chart: tint, table_head: dark, callout: card, kpi: strip}
---

# public

## 개요

국내 공공기관 내부 보고서의 관행을 그대로 따른다. 장식은 최소로 두고, 정보는 촘촘하게 넣는다. 평가 1회차에서 기준선(평가 2)이 이 관행을 잘 살려서 높은 완성도를 보였고, 그 관찰을 토큰으로 옮겼다.

## 관행

- **보고 요지 박스**: 제목 아래 거버닝 메시지를 연한 하늘색 박스에 넣는다(`message_box: true`).
- **기호 위계**: 큰 항목은 □, 세부 항목은 ○. 본문 불릿 기호는 ○를 쓰고, 소제목에는 □를 앞에 붙여 쓴다.
- **섹션 번호**: Ⅰ, Ⅱ, Ⅲ 로마 숫자(`section_numerals: roman`).
- **출처와 단위**: "자료: 기관명(기준 시점)" 형식, 단위는 표·차트 오른쪽 위.
- **잠정치 표기**: 확정되지 않은 연도는 "(잠정)"을 붙인다.
- 각진 모서리, 남색 머리 행의 표.

## 하지 말 것

- 표지 외에는 어두운 바탕을 쓰지 않는다.
- 장식용 도형, 아이콘을 넣지 않는다.
