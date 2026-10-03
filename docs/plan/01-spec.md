# 기획 v0.1: PPT 생성 스킬 + CLI

> 상태: 초안. `skill-creator` 절차의 1단계(의도 정리, 인터뷰, 리서치) 결과물이다.
> 열린 질문은 맨 아래에 정리했다. 답변을 받으면 v0.2로 갱신한다.

## 1. 한 줄 정의

**원하는 내용·템플릿·톤앤매너로 PPT를 만들고 고치는 스킬.** 실제 작업은 Python CLI(`pptkit`)가 수행하고, 스킬(`SKILL.md`)은 Claude가 CLI를 올바른 순서로 호출하도록 안내하는 얇은 설명서 역할을 맡는다.

스킬과 CLI를 분리하는 이유는 다음과 같다.
- **토큰**: 렌더링, 피벗, 검증을 코드가 처리하므로 Claude는 짧은 스펙만 쓰고 짧은 결과만 읽으면 된다.
- **재사용**: 같은 CLI를 Claude 없이 터미널에서도 실행할 수 있다.
- **결정성**: 같은 입력에서 항상 같은 덱이 나오므로 평가(eval)와 회귀 테스트가 가능하다.

## 2. 대화에서 확정된 결정

| # | 결정 | 근거 |
|---|---|---|
| D1 | 토큰 절감을 1급 목표로 둔다 | 사용자 요구 |
| D2 | 사진은 삽입하지 않는다. 슬라이드는 텍스트, 도형, 차트, 표로만 구성한다 | 사용자 요구. 따라서 이미지 없이 구조 데이터만으로 판단할 수 있다 |
| D3 | 차트와 표는 **네이티브 객체**로 만든다. PowerPoint에서 "데이터 편집"이 가능해야 한다 | 통계·피벗 요구. Anthropic pptx 스킬의 원칙과 같다 |
| D4 | 읽기 방식은 **장표마다 스크립트가 결정**한다(L0~L3). Claude가 먼저 읽고 판단하지 않는다 | 3차 대화. 판단을 위해 읽으면 이미 토큰을 쓴 것이다 |
| D5 | markitdown은 내용 확인용으로만 쓴다. 위치·겹침·넘침은 별도 검사기가 판정한다 | 실측 결과 markitdown은 좌표를 출력하지 않는다 |
| D6 | 수정은 XML 재작성이 아니라 **패치 명령**으로 한다 | 출력 토큰은 입력보다 비싸고 느리다 |
| D7 | graphify는 **개발 도구**다. 산출물 스킬에는 들어가지 않는다 | 4차 대화 |
| D8 | 외부 코드는 MIT만 반입한다. Anthropic pptx(독점)는 플러그인으로 호출만 한다 | 라이선스 |

## 3. 재사용 판단 (graphify로 확인)

`pptx-from-layouts`를 AST 그래프로 분석했다(노드 1,648개, `dev/graphify/pptx-from-layouts/`).

- `scripts/generate_pptx.py`는 6,757줄짜리 단일 파일이다. `populate_slide()`가 레이아웃마다 `populate_*` 함수 20여 개로 분기하고, 대부분 데모 템플릿(Inner Chapter)의 레이아웃 이름에 맞춰져 있다.
- 차트를 그리는 경로가 없다. 표는 마크다운 표를 파싱하는 수준이다.

**판단**: 렌더러는 새로 작게 만들고, 검증된 부분만 가져온다.

| 가져옴 | 이유 |
|---|---|
| `pptx-profile/scripts/catalog.py`: 템플릿 → 레이아웃 카탈로그 | 내 템플릿 온보딩의 핵심이다. 레이아웃 이름에 의존하지 않는다 |
| `lib/inventory.py`의 겹침·이탈 검사 로직 | 테스트에서 겹침과 슬라이드 이탈을 정확히 잡았다 |
| `rules/visual-types.md`의 "시각 유형 결정 순서" | 내용 유형별 레이아웃 선택 규칙으로 쓸 수 있다 |
| Anthropic pptx의 차트 함정 목록 (문서로만 참고) | 파일이 깨지는 조건을 피하기 위해 |

| 가져오지 않음 | 이유 |
|---|---|
| `generate_pptx.py` 본체 | 특정 템플릿에 하드코딩돼 있고, 차트를 추가하려면 6,700줄을 이해해야 한다 |
| html2pptx 방식 (구버전 Anthropic pptx) | 20KB 문서를 매번 전부 읽어야 해서 토큰 목표와 반대다 |

## 4. 구조

```
.claude/skills/ppt/                 ← 산출물 스킬 (짧게 유지)
├── SKILL.md                        라우팅 표 + 작업 흐름. 목표 150줄 이하
├── references/                     필요할 때 파일 하나만 읽는다
│   ├── deck-spec.md                deck.md 문법
│   ├── charts.md                   차트 카탈로그 (ID, 용도, 데이터 형태)
│   ├── tones.md                    톤 프리셋 목록
│   └── editing.md                  읽기 단계(L0~L3)와 패치 명령
└── pptkit/                         ← CLI (Python, python-pptx + pandas)
    ├── catalogs/charts/*.yaml      차트 양식 기본값
    ├── catalogs/tones/*.yaml       색·폰트·밀도·문체
    └── ...
```

### CLI 명령

| 명령 | 입력 | 출력 (Claude가 읽는 양) |
|---|---|---|
| `pptkit profile tpl.pptx` | 템플릿 | 레이아웃 카탈로그. 템플릿당 1회만 실행하고 캐시한다 |
| `pptkit data file.csv` | CSV / xlsx | 컬럼·타입·행 수·상위 값 요약 (약 100토큰). 원본은 읽지 않는다 |
| `pptkit pivot file.csv --rows .. --cols .. --val .. --agg ..` | 데이터 | 피벗 CSV와 요약. 계산은 pandas가 한다 |
| `pptkit build deck.md -o out.pptx` | 스펙 | 덱과 한 줄 결과 (`OK 12 slides, 4 charts, 2 tables` 또는 실패 목록) |
| `pptkit map out.pptx` | 덱 | 장당 한 줄 맵과 권장 읽기 단계 |
| `pptkit read out.pptx -s 3,5 -l L1` | 덱 | 지정한 슬라이드만, 지정한 깊이로 |
| `pptkit patch out.pptx ops.yaml` | 패치 명령 | 적용 결과와 바뀐 슬라이드 검사 결과 |
| `pptkit qa out.pptx` | 덱 | 실패 항목만 (`S4 b1 overflow 0.3in`). 통과하면 `OK` 한 줄 |
| `pptkit fetch wb|kosis ...` | 지표 코드 | CSV와 출처 메타데이터 (M4, 네트워크 허용 후) |

### deck.md 예시

LLM이 쓰는 것은 이 파일뿐이다. 숫자는 파일에 쓰지 않고 데이터 파일을 참조한다.

```markdown
---
template: corp.pptx        # 없으면 기본 템플릿
tone: consulting-navy
source: "통계청 KOSIS, 2026"
---

# 매출은 3년 연속 두 자릿수로 성장했다
chart: column-trend
data: sales.csv
x: year
y: [revenue]
highlight: 2026

# 지역별로는 수도권 비중이 절반을 넘는다
pivot: sales.csv
rows: region
cols: year
val: revenue
agg: sum
style: heatmap-total
top: 8               # 상위 8개 + 기타

# 시사점
- 수도권 의존도 완화가 다음 과제다
- 비수도권 성장률은 수도권보다 4%p 높다
```

## 5. 카탈로그 (초안)

### 차트 (`dataviz` 스킬의 형태 선택 기준을 따름)

| ID | 용도 | 데이터 형태 |
|---|---|---|
| `bar-ranked` | 항목 간 순위 비교 | 범주 1 + 값 1 |
| `column-trend` | 시간에 따른 변화 (기간 12개 이하) | 시간 + 값 1~3 |
| `line-trend` | 긴 시계열이나 여러 계열의 추이 | 시간 + 값 N |
| `stacked-share` | 구성비 변화 (100% 누적) | 시간 + 범주 + 값 |
| `waterfall` | 증감 요인 분해 | 단계 + 증감값 (투명 기준 계열로 구현) |
| `combo-bar-line` | 금액과 비율을 함께 표시 | 시간 + 값 + 비율 (보조축). python-pptx가 직접 지원하지 않아 XML을 보정해야 한다 |
| `scatter` | 두 지표의 관계 | 값 x, 값 y (+라벨) |
| `kpi-tiles` | 핵심 숫자 3~4개 | 지표명 + 값 + 증감 |

공통 규칙: 슬라이드당 차트 1개를 둔다. 제목은 결론 문장(액션 타이틀)으로 쓴다. 핵심값은 강조 색으로 표시하고 나머지 계열은 무채색으로 둔다. 출처는 각주로 넣는다.

### 표·피벗

| ID | 용도 |
|---|---|
| `table-plain` | 일반 표. 숫자는 오른쪽 정렬하고 천 단위 구분 기호를 넣는다 |
| `pivot-total` | 행·열 합계를 굵게 표시한다 |
| `heatmap-total` | 셀을 값의 크기에 따라 음영 처리하고 합계를 함께 표시한다 |
| 공통 동작 | 상위 N개 + "기타"로 자르기. 행이 많으면 자동으로 다음 슬라이드에 나눠 싣고 머리글을 반복한다. 단위는 표 머리에 한 번만 쓴다 |

### 톤

- 출발점: `theme-factory` 10종, `references/style-presets` 12종
- PPTX용으로 바꿀 항목: Office 기본 폰트 매핑(한글은 맑은 고딕), 본문 밀도(장당 단어 수 상한), 문체(보고서체 / 발표체)
- 초기 후보 3종: `consulting-navy`, `corporate-clean`, `pitch-bold`

## 6. 토큰 예산 (목표)

실측 기준선은 예제 5장 덱에서 측정했다. markitdown은 약 370토큰, inventory 전체는 약 2,100토큰, 슬라이드 XML은 약 4,300토큰, 렌더 이미지는 약 8,000토큰이었다.

| 작업 | 목표 |
|---|---|
| 10장 새 덱 생성: Claude 출력 | `deck.md` 1개, 1,500토큰 이하 |
| 10장 새 덱 생성: Claude 입력(도구 결과) | 1,000토큰 이하 (데이터 요약 + build 결과 + qa 결과) |
| 30장 덱 중 2장 수정: 입력 | 맵 약 450 + 대상 2장 L1/L2 약 600 = 1,100토큰 이하 |
| 30장 덱 중 2장 수정: 출력 | 패치 명령 200토큰 이하 |
| 이미지 확인 | 기본 0장. qa에서 실패한 슬라이드만 저해상도로 확인 |

## 7. 개발 과정에서 쓰는 스킬

| 스킬 | 언제, 어떻게 |
|---|---|
| `skill-creator` | 지금 단계(기획) → 평가 케이스 작성 → with/without 스킬 비교 → 리뷰 뷰어 → description 최적화 |
| `graphify` | 재사용할 코드와 우리 CLI 코드를 그래프로 만들어 탐색한다. 코드를 바꾼 뒤에는 `graphify update`(LLM 비용 없음)를 실행한다. 결과는 `dev/graphify/`에 둔다 |
| `ponytail` | CLI 코드를 작성할 때. 표준 라이브러리와 python-pptx 기본 기능을 먼저 쓰고, 필요하지 않은 추상화는 만들지 않는다 |
| `dataviz` | 차트 카탈로그의 형태 선택 규칙과 색 팔레트 검증 |
| `theme-factory` | 톤 프리셋 초안 |
| `xlsx` | 피벗 결과가 엑셀 피벗과 일치하는지 교차 검증 |
| `anthropic-skills:pptx` | 네이티브 차트 함정 목록, `validate.py`로 파일 무결성 검사 |
| `fluent-korean` | 스킬 문서와 사용자 안내 문구 |

## 8. 평가 케이스 (초안, `skill-creator` 형식)

| # | 프롬프트 (사용자가 실제로 할 말) | 확인할 것 |
|---|---|---|
| 1 | "첨부한 sales.csv로 경영진 보고용 8장짜리 PPT 만들어줘. 지역별 피벗이랑 연도별 추이 꼭 넣고, 컨설팅 보고서 느낌으로." | 네이티브 차트 2개 이상, 피벗 표 1개 이상, qa 통과, Claude 출력 토큰 |
| 2 | "q3_review.pptx 12번 슬라이드 숫자를 새 데이터로 바꾸고, 7번 슬라이드 겹친 박스 정리해줘." | 다른 슬라이드는 바이트 단위로 변하지 않음, 겹침 0건, 입력 토큰 |
| 3 | "우리 회사 템플릿(corp.pptx)으로 신규 서비스 소개 6장 만들어줘. 내용은 아래 메모 참고." | 템플릿 레이아웃 사용 여부, 남은 placeholder 문구 0건, 글자 넘침 0건 |

각 케이스는 스킬을 쓴 실행과 쓰지 않은 실행(기준선)을 함께 돌려 품질과 토큰을 비교한다.

## 9. 마일스톤

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| M0 | 기획 확정, 평가 케이스 확정 | 이 문서 v0.2 |
| M1 | `build`: deck.md → 텍스트·차트 3종·피벗 표 | 평가 1이 qa를 통과한다 |
| M2 | `map` / `read` / `patch` / `qa` | 평가 2의 토큰 목표를 달성한다 |
| M3 | 톤 3종, `profile`로 내 템플릿 온보딩 | 평가 3을 통과한다 |
| M4 | `fetch` (World Bank, KOSIS) | 네트워크 허용 후 진행한다 |
| M5 | `SKILL.md` 다듬기, description 최적화, 패키징 | 트리거 평가 20개 중 test 세트 점수 기준 |

`ponytail` 원칙에 따라 M1에서는 차트 3종(`bar-ranked`, `column-trend`, `line-trend`)과 피벗 1종(`heatmap-total`)만 만든다. 나머지는 평가에서 필요가 확인될 때 추가한다.

## 10. 환경 이슈

- 이 클라우드 컨테이너에는 한국어 폰트가 없다(IPA 일본어 폰트만 있음). 렌더 점검과 글자 넘침 측정을 하려면 `fonts-nanum` 같은 한국어 폰트 설치를 `setup.sh`에 넣어야 한다.
- 이 컨테이너의 LibreOffice는 현재 어떤 .pptx도 열지 못한다. M2 전에 원인을 확인한다. 실패하면 글자 넘침은 폰트 실측(PIL)으로만 판정한다.
- 통계 API 도메인(`api.worldbank.org`, `kosis.kr`)은 네트워크 정책으로 막혀 있다.

## 11. 열린 질문

1. **작업 환경**: 실제 사용은 로컬 Windows와 PowerPoint 환경인가? 그렇다면 COM으로 글자 넘침을 정확히 측정하는 기능을 선택 기능으로 넣는다.
2. **템플릿**: 실제로 쓸 회사·개인 .pptx 템플릿이 있는가? 평가 3에 필요하다.
3. **톤**: 초기 3종(`consulting-navy`, `corporate-clean`, `pitch-bold`)이 맞는가? 아니면 원하는 톤을 알려 달라.
4. **차트 양식**: 표 5의 8종 외에 자주 쓰는 양식이 있는가? 예를 들어 간트, 매트릭스(2×2), 퍼널 같은 양식이다.
5. **데이터 출처 우선순위**: KOSIS, e-나라지표, World Bank, OECD 중 어디를 먼저 붙일까?
6. **평가 데이터**: 평가 1에 쓸 실제 CSV 예시가 있는가? 없으면 가상 데이터를 만든다.
