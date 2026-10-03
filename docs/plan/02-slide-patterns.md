# 장표 패턴 카탈로그 (초안)

> 출처: SlideModel 카테고리(Process Flow, Tree, Funnel, Timeline, Roadmap, Gantt, Dashboard, Comparison Table, 2×2 Matrix 등), Figma Slides 커뮤니티 템플릿, 비즈니스 슬라이드 유형 가이드, 국내 컨설팅 보고서 관행.
> 이 카탈로그는 **구조(레이아웃 원형)만** 정리한 것이다. 특정 템플릿의 디자인이나 에셋은 복제하지 않는다. 모든 패턴은 PowerPoint 기본 도형, 네이티브 차트, 네이티브 표로 그려서 사용자가 편집할 수 있게 한다. 사진은 쓰지 않는다.

## 공통 프레임: `kr-report`

국내 보고서에서 가장 많이 쓰는 본문 장표의 틀이다. 본문 패턴은 모두 이 프레임 안에 들어간다.

```
┌────────────────────────────────────────────┐
│ 제목: 결론 문장 (액션 타이틀)                  │
│ 거버닝 메시지: 제목을 뒷받침하는 1~2줄           │
├────────────────────────────────────────────┤
│                                            │
│              본문 패턴 영역                  │
│                                            │
├────────────────────────────────────────────┤
│ 시사점 박스 (선택)                            │
│ 출처: 통계청 KOSIS, 2026          페이지 번호  │
└────────────────────────────────────────────┘
```

`tone.frame`을 `plain`으로 바꾸면 거버닝 메시지와 시사점 박스가 빠진다. 피치나 교육용 덱에서 쓴다.

## 패턴 목록

우선순위: **P0**는 첫 구현(M1)에 포함하고, **P1**은 평가에서 필요가 확인되면 추가하고, **P2**는 요청이 있을 때 만든다.

### A. 구조 장표

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `cover` | 표지 | 제목, 부제, 날짜·작성자 | P0 |
| `agenda` | 목차 | 항목 3~6개 (번호 + 제목) | P0 |
| `section` | 섹션 구분 | 섹션 번호, 섹션 제목 | P0 |
| `exec-summary` | 요약 (보고서 1쪽) | 핵심 메시지 3~5개, 숫자 강조 1~3개 | P0 |
| `closing` | 결론과 다음 단계 | 요청 사항(`brief.ask`), 다음 단계 2~4개, 일정 | P0 |
| `appendix` | 부록 구분 | 제목 | P2 |

### B. 메시지 장표

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `key-message` | 한 문장 강조 | 문장 1개 (100자 이하), 보조 문장 1개 | P0 |
| `bullets-callout` | 본문 + 시사점 | 왼쪽 불릿 3~5개, 오른쪽 시사점 박스 | P0 |
| `two-column` | 두 갈래 설명 | 소제목 + 불릿 × 2 | P1 |
| `quote` | 인용·VOC | 인용문, 화자 | P2 |

### C. 비교와 구조화

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `compare-2` / `compare-3` | A안 vs B안 비교 | 열 제목 + 항목 3~5개 × 2~3열, 추천안 강조 | P0 |
| `compare-table` | 기능·조건 비교표 | 행 = 기준, 열 = 대안, 셀 = ●/◐/○ 또는 값 | P1 |
| `before-after` | 개선 전후 | 전 / 후 두 칸, 가운데 화살표 | P1 |
| `matrix-2x2` | 우선순위, 포지셔닝 | 축 이름 2개, 사분면 이름, 항목 점 배치 | P0 |
| `swot` | 내외부 분석 | 4칸 × 불릿 2~4개 | P1 |
| `pyramid` | 계층, 단계적 목표 | 층 3~5개 | P2 |
| `venn` | 교집합 | 원 2~3개 + 교집합 라벨 | P2 |
| `logic-tree` | 이슈 트리, 원인 분해 | 루트 1 → 가지 2~4 → 잎 2~3 | P1 |
| `org-chart` | 조직, 역할 | 노드 최대 3단계 | P2 |

### D. 흐름과 시간

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `process` | 단계 흐름 | 단계 3~5개 (쉐브론 + 설명 50자 이하) | P0 |
| `timeline` | 일정·마일스톤 | 시점 4~7개 + 라벨 | P0 |
| `roadmap` | 단계 × 과제 | 행 = 워크스트림, 열 = 단계, 셀 = 과제 | P1 |
| `gantt` | 세부 일정 | 작업명, 시작, 종료 (데이터 파일에서 읽음) | P1 |
| `funnel` | 전환 단계 | 단계 3~5개 + 값·전환율 | P1 |
| `cycle` | 순환 구조 | 요소 3~6개 | P2 |

### E. 숫자와 데이터

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `kpi-tiles` | 핵심 지표 | 지표명, 값, 증감, 기준 시점 × 3~4개 | P0 |
| `big-number` | 숫자 하나 강조 | 숫자, 단위, 설명 1줄 | P1 |
| `chart-takeaway` | 차트 + 해석 | 차트 1개 (`charts` 카탈로그), 오른쪽 시사점 2~3개 | P0 |
| `chart-pair` | 두 차트 비교 | 차트 2개, 공통 축 단위 | P1 |
| `pivot-table` | 피벗 표 | 행·열·값·집계, 합계, 상위 N + 기타 | P0 |
| `heatmap-table` | 음영 피벗 | `pivot-table` + 값 크기에 따른 셀 음영 | P0 |
| `dashboard` | 미니 차트 묶음 | 작은 차트 또는 KPI 4개 (2×2) | P2 |

### F. 사업·피치

| ID | 용도 | 슬롯 | 우선 |
|---|---|---|---|
| `problem-solution` | 문제와 해법 | 문제 2~3개 → 해법 2~3개 | P1 |
| `market-size` | TAM·SAM·SOM | 동심원 3개 + 값 | P1 |
| `pricing` | 요금제 | 플랜 2~4개 (가격, 포함 기능, 추천 표시) | P2 |
| `team` | 팀 소개 | 이름, 역할, 한 줄 경력 × 3~6 (사진 없이 이니셜 원) | P2 |
| `traction` | 성장 지표 | `chart-takeaway`나 `kpi-tiles`를 재사용 | P2 |

## 목적별 기본 구성 (Brief의 `purpose`에 따라 자동 제안)

| 목적 | 기본 순서 |
|---|---|
| 보고 | cover → exec-summary → (chart-takeaway / pivot-table / bullets-callout) × N → closing |
| 제안 | cover → key-message(문제) → logic-tree → compare-3 → roadmap → closing |
| 피치·IR | cover → problem-solution → market-size → (process 또는 compare-table) → traction → team → closing |
| 교육 | cover → agenda → (section → key-message → process) × N → exec-summary |
| 회고 | cover → kpi-tiles → before-after → bullets-callout → timeline(다음 분기) |

## 패턴 선택 규칙 (내용 유형 → 패턴)

`pptx-from-layouts`의 "시각 유형 결정 순서"를 확장했다. 위에서부터 차례로 확인하고, 처음 맞는 패턴을 쓴다.

1. 순서가 있는가? → `process`, 날짜가 있으면 `timeline`
2. 대안을 비교하는가? → `compare-N`, 기준이 많으면 `compare-table`
3. 두 축으로 평가하는가? → `matrix-2x2`
4. 데이터 파일이 있는가? → 시계열이면 `chart-takeaway`, 범주 × 범주면 `pivot-table` / `heatmap-table`
5. 핵심 숫자가 3~4개인가? → `kpi-tiles`
6. 원인이나 구성 요소를 분해하는가? → `logic-tree`
7. 문장 하나가 전부인가? → `key-message`
8. 그 외 → `bullets-callout` (최후의 선택)

## 기본 템플릿

사용자에게 템플릿이 없으므로, 톤 3종(`consulting-navy`, `corporate-clean`, `pitch-bold`)마다 슬라이드 마스터를 하나씩 만들어 기본으로 제공한다. 마스터에는 위 패턴이 쓰는 레이아웃(제목만, 제목+본문, 빈 화면, 섹션, 표지)만 넣는다. 패턴 자체는 렌더러가 도형으로 그린다. 그래서 나중에 사용자가 자기 템플릿을 가져와도 같은 패턴을 그대로 쓸 수 있다.
