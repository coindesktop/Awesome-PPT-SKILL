---
name: executive
description: 경영 보고·컨설팅형. 아주 연한 웜 그레이 바탕에 코발트 강조색 하나만 쓰는 절제된 시스템.
formality: formal
use_for: [report, proposal, review]
colors:
  bg: "F8F7F2"        # 본문 장표 바탕 (순백 금지)
  dark: "151A2E"      # 섹션 장표 바탕
  ink: "141414"       # 제목
  body: "4A4F57"      # 본문
  muted: "8A9099"     # 메타, 각주, 축 라벨
  accent: "2F54EB"    # 유일한 강조색: 라벨, 숫자, 강조 막대
  card: "EDEFF8"      # 카드 바탕 (강조색 약 5%)
  line: "D5DAF0"      # 카드 테두리, 구분선 (강조색 약 20%)
  neutral_series: "C9CEDB"
  positive: "0F8A5F"
  negative: "D93838"
series: ["2F54EB", "EB6834", "1BAF7A", "EDA100"]
fonts: {title: "맑은 고딕", body: "맑은 고딕"}
type: {cover: 40, title: 26, eyebrow: 12, message: 15, body: 15, metric: 36, small: 10}
shape: {radius: 0.12, border_pt: 1}   # radius in inches
cover: {bg: light, decor: circles}
section: dark
closing: dark
bullet: "•"
---

# executive

## 개요

절제와 단 하나의 강한 선택이 이 시스템의 전부다. 바탕은 아주 연한 웜 그레이, 강조색은 코발트 하나다. 코발트는 모든 강조 순간(섹션 라벨, 숫자, 차트의 강조 막대, 추천 표시)을 맡고, 제목은 거의 검은색으로 둔다. 제목까지 강조색으로 칠하면 위계가 무너진다.

출처: `references/design/slides/blue-professional.md`(frontend-slides, MIT)의 원칙을 PowerPoint와 한국어 보고서에 맞게 옮겼다.

## 색 역할

| 토큰 | 역할 |
|---|---|
| `bg` | 모든 본문 장표의 바탕 |
| `ink` | 제목, 표의 핵심 값 |
| `body` | 본문 문단, 불릿 |
| `muted` | 각주, 출처, 축 라벨, 페이지 번호 |
| `accent` | 섹션 라벨(eyebrow), 지표 숫자, 강조 막대, 불릿 기호, 추천 표시 |
| `card` / `line` | 카드 바탕과 테두리. 그림자 대신 색조와 테두리로 층을 만든다 |
| `positive` / `negative` | 증감 표시 글자색에만 쓴다. 채우기에는 쓰지 않는다 |

두 번째 강조색은 없다. 범주 구분은 위치, 크기, 라벨로 한다. 차트에서 계열이 여러 개일 때만 `series`의 검증된 색을 순서대로 쓴다.

## 타이포그래피

| 토큰 | pt | 용도 |
|---|---|---|
| `cover` | 40 | 표지 제목 |
| `title` | 26 | 본문 장표 제목 (결론 문장) |
| `eyebrow` | 12 | 제목 위 섹션 라벨, 강조색, 굵게 |
| `message` | 15 | 거버닝 메시지, `body` 색 |
| `body` | 15 | 본문 (밀도 설정으로 조정) |
| `metric` | 36 | KPI 숫자, 강조색 |
| `small` | 10 | 출처, 페이지 번호 |

굵기는 제목과 숫자만 굵게, 본문은 보통으로 둔다. 기울임과 밑줄은 쓰지 않는다.

## 레이아웃

- 모든 본문 장표는 같은 리듬을 따른다: 섹션 라벨 → 제목 → 거버닝 메시지 → 본문 영역 → 출처와 페이지 번호.
- 좌우 여백 0.6인치, 카드 사이 간격 0.25~0.3인치.
- 정보 칸이 3~6개일 때 가장 좋아 보인다. 내용이 적으면 칸을 키우지 말고 장표를 합친다.

## 컴포넌트

- **카드**: `card` 바탕 + `line` 1pt 테두리 + 둥근 모서리. 그림자 없음.
- **KPI 타일**: 라벨(`muted`, 12pt) → 숫자(`accent`, 36pt) → 증감(▲▼ + `positive`/`negative`) → 설명(`muted`).
- **차트**: 강조할 값 하나만 `accent`, 나머지는 `neutral_series`. 격자선은 `line`, 축 글자는 `muted`. 값 라벨을 직접 단다.
- **표**: 머리 행은 `card` 바탕에 굵은 `ink`, 행 구분은 `line` 가는 선, 합계 행은 굵게.
- **표지·결론**: 장식(동심원)은 표지에만 쓴다. 결론 장표는 `dark` 바탕에 요청 사항을 크게 쓴다.

## 하지 말 것

- 제목을 강조색으로 칠하지 않는다.
- 제목 아래 강조 밑줄, 장표 가장자리 색 띠를 넣지 않는다.
- 카드에 그림자를 넣지 않는다.
- 강조색 외의 색을 장식에 쓰지 않는다.
