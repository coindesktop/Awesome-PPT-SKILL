---
name: corporate
description: 기업 내부 보고형. 흰 바탕, 남색 표지·섹션·표 머리, 파랑 강조와 제목 옆 강조 막대, 색을 입힌 차트.
formality: formal
use_for: [report, proposal, review]
colors:
  bg: "FFFFFF"
  dark: "0B2545"
  surface: "FFFFFF"
  ink: "111827"
  body: "3B4250"
  muted: "838B98"
  accent: "1F5EDC"
  card: "F1F4F9"
  line: "DDE3EC"
  neutral_series: "C5CCD8"
  positive: "0F8A5F"
  negative: "D93838"
series: ["1F5EDC", "F28C28", "13A89E", "8E5CD9"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 40, title: 24, eyebrow: 12, message: 15, body: 15, metric: 36, small: 10}
shape: {radius: 0.06, border_pt: 0}
cover: {bg: dark, decor: stripe}
section: dark
closing: dark
bullet: "▪"
style: {header: bar-rule, chart: tint, table_head: dark, callout: tint, kpi: strip}
---

# corporate

## 개요

국내 기업의 본부장·임원 보고서에서 자주 쓰는 구조를 기준으로 한 시스템이다. 흰 바탕에 남색으로 무게를 잡고(표지, 섹션,
결론, 표 머리), 파랑 하나로 강조한다. 제목 왼쪽의 강조 막대와 머리 아래 가는 선이 모든 장표에 같은 골격을 만든다.
차트는 회색 대신 강조색의 옅은 단계로 과거 값을 칠하고, 강조할 값만 진한 파랑으로 둔다.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `dark` | 표지, 섹션, 결론 바탕, 표 머리 행 |
| `accent` | 제목 막대, 강조 막대·숫자, 시사점 박스 테두리 |
| `card` | KPI 타일, 표 줄무늬, 시사점 박스 바탕(강조색 8% 혼합) |
| `series` | 여러 계열 차트: 파랑·주황·청록·보라. 인접 쌍 색각 이상 ΔE 13.8 이상(검증 스크립트 통과) |

## 스타일 스위치 (`style:`)

| 키 | 값 | 효과 |
|---|---|---|
| `header` | `bar-rule` | 제목 왼쪽 강조 막대 + 머리 아래 가는 선 |
| `chart` | `tint` | 단일 계열 차트에서 강조 외 막대를 회색 대신 강조색의 옅은 단계로 |
| `table_head` | `dark` | 표 머리 행 남색·흰 글자, 본문 줄무늬 |
| `callout` | `tint` | 시사점 박스를 옅은 강조색 바탕 + 왼쪽 강조 막대로 |
| `kpi` | `strip` | KPI 타일 위 강조 띠, 요약 장표 첫 숫자 카드를 강조색으로 채움 |

## 하지 말 것

- 주황·청록을 강조색으로 쓰지 않는다(계열색 전용).
- 차트 글자에 계열색을 입히지 않는다. 값과 범례 글자는 본문 색이다.
