# 기획 v0.2: 개인화 PPT 스킬 + `pptkit` CLI

> 상태: v0.3. M1 구현을 마쳤다(2026-10-03). 구현 중에 바뀐 결정은 D13, D16, D17에 기록했다.
> 세부 문서: [02 장표 패턴](02-slide-patterns.md) · [03 통계 연결](03-data-sources.md) · [04 개인화](04-personalization.md)

## 1. 한 줄 정의

**사용자가 어떤 일을 하는 사람이고 무엇을 만들려는지 먼저 파악한 뒤, 그 사람에게 맞는 톤앤매너로 PPT를 만들고 고치는 스킬.**
실제 작업은 미리 만들어 둔 Python CLI(`pptkit`)가 수행한다. 스킬(`SKILL.md`)은 Claude가 CLI를 올바른 순서로 호출하도록 안내하는 짧은 설명서다.

## 2. 확정된 결정

| # | 결정 | 근거 |
|---|---|---|
| D1 | 토큰 절감을 1급 목표로 둔다 | 사용자 요구 |
| D2 | 사진은 삽입하지 않는다. 텍스트, 도형, 네이티브 차트, 네이티브 표로만 구성한다 | 사용자 요구 |
| D3 | 차트와 표는 PowerPoint에서 "데이터 편집"이 가능한 네이티브 객체로 만든다 | 통계·피벗 요구 |
| D4 | 읽기 깊이(L0~L3)는 장표마다 스크립트가 결정한다 | 판단하려고 먼저 읽으면 이미 토큰을 쓴 것이다 |
| D5 | markitdown은 내용 확인용으로만 쓴다. 위치·겹침·넘침은 별도 검사기가 판정한다 | 실측 결과 markitdown은 좌표를 출력하지 않는다 |
| D6 | 수정은 XML 재작성이 아니라 패치 명령으로 한다 | 출력 토큰은 입력보다 비싸고 느리다 |
| D7 | graphify는 개발 도구다. 산출물 스킬에 들어가지 않는다 | 사용자 지시 |
| D8 | 외부 코드는 MIT만 반입한다 | 라이선스 |
| **D9** | **실행 중에 Claude가 Python 코드를 작성하지 않는다.** Claude는 `brief.yaml`과 `deck.md`만 쓰고, 미리 만든 CLI가 나머지를 처리한다 | "코드를 짜서 실행하느라 토큰을 두 번 쓰지 말 것" |
| **D10** | **전역 설치**: CLI는 PATH에, 스킬은 사용자 수준(`~/.claude/skills/ppt`)에, Profile은 `~/.pptkit/`에 둔다 | 어느 폴더, 어느 대화에서든 재사용하고 다시 묻지 않기 위해 |
| **D11** | 주 실행 환경은 **로컬 Windows + PowerPoint**다. 클라우드나 Claude 앱에서는 결과 .pptx를 다운로드 파일로 전달한다 | 사용자 답변 1 |
| **D12** | Windows에서는 **PowerShell로 PowerPoint COM을 호출**해 글자 넘침을 실측한다. 선택 기능이며 추가 Python 의존성이 없다 | 정확한 QA, LibreOffice의 폰트 대체 문제 회피 |
| **D13** | 사용자 템플릿이 없으므로 기본 마스터와 장표 패턴 카탈로그를 제공한다. **(M1 변경)** 마스터는 .pptx 파일 3개로 두지 않고, 기본 템플릿을 16:9로 바꾼 뒤 톤의 색과 폰트를 테마에 써 넣어 생성한다. 관리할 바이너리 파일이 없고, PowerPoint에서 새 슬라이드를 추가해도 톤이 유지된다 | 사용자 답변 2, 4 |
| **D14** | **개인화 사전 조사(Profile → Brief → Tone → 톤 시안 2장)를 생성보다 먼저 수행한다** | 사용자 요구: "개인화된 톤앤매너가 핵심" |
| **D16** | 차트에 이중 축을 쓰지 않는다. `combo-bar-line`은 카탈로그에서 뺐다. 단위가 다른 두 지표는 두 장으로 나누거나 `kpi-tiles`로 표시한다 | `dataviz` 원칙 |
| **D17** | 구조색(제목, 도형)과 데이터색(차트 계열)을 분리한다. 브랜드 색은 구조색만 바꾸고, 차트 계열은 `validate_palette.js`를 통과한 팔레트를 쓴다 | `dataviz` 팔레트 검증에서 남색 계열이 실패함 |
| **D18** | 톤의 시각 요소는 디자인 하나당 DESIGN.md 파일 하나로 정의한다(`pptkit/designs/`). 머리말 토큰은 렌더러가 읽고 본문은 근거를 설명한다. 사용자 DESIGN.md(`~/.pptkit/designs/`)가 있으면 우선한다 | 평가 1회차 육안 비교 후 사용자 요청(레퍼런스 기반 고도화) |
| **D19** | 디자인 선택에 격식 수준(`brief.formality`)을 반영한다. friendly → forest, 공공 → public, IR·전략 → signal, 그 외 → executive | 평가 4에서 "딱딱하지 않게"를 반영하지 못함 |
| **D20** | 검증되지 않은 수치(기억, 웹 검색 조각)는 슬라이드에 넣지 않는다 | 평가 5에서 두 실행의 GDP 수치가 서로 다름 |
| **D15** | 통계는 키 없이 동작하게 준비만 한다. 키가 필요한 소스는 선택 사항이며, 키는 Claude를 거치지 않는다 | 사용자 답변 5 |

## 3. 토큰이 어디서 줄어드는가 (사용자 질문 1에 대한 답)

| 방식 | 덱 1개를 만들 때 Claude가 쓰는 출력 |
|---|---|
| 일반적인 방식 (Anthropic pptx 등) | 덱마다 생성 스크립트 수백 줄을 작성하고, 오류가 나면 다시 고친다 |
| 이 스킬 | `deck.md` 1개 (10장 기준 1,500토큰 이하). 코드는 0줄이다 |

재사용 효과는 세 겹으로 생긴다.

1. **같은 대화 안**: `SKILL.md`는 처음 한 번 로드된 뒤 컨텍스트에 남고, 프롬프트 캐시로 싸게 다시 읽힌다. 두 번째 덱부터는 스킬 로딩 비용이 거의 들지 않는다.
2. **다른 폴더, 다른 대화**: CLI와 스킬을 전역으로 설치하므로 설치나 설명을 반복할 필요가 없다.
3. **다음 세션**: Profile, 템플릿 분석 결과, 통계 캐시가 디스크에 남는다. 그래서 같은 질문을 다시 하지 않고, 같은 API를 다시 부르지 않는다.

## 4. 실행 흐름

```
[사전 조사]
 ① pptkit profile show          Profile이 없으면 온보딩 (기존 자료 추출 → 추론 → 질문 최대 5개)
 ② brief.yaml 작성              요청 문장에서 추출하고, 빠진 핵심(ask, mode)만 질문
 ③ pptkit tone resolve          Profile × Brief × 업종 관례 → tone.yaml (한 줄 요약만 읽음)
 ④ 데이터가 있으면 pptkit data   요약 약 100토큰
[톤 확인]
 ⑤ pptkit build --sample        표지 + 대표 본문 1장 → 사용자 확인
[생성]
 ⑥ deck.md 작성 → pptkit build  결과 한 줄
 ⑦ pptkit qa                    실패 항목만 출력 (Windows면 COM 실측)
[수정]
 ⑧ pptkit map → read → patch    필요한 장만, 필요한 깊이로
```

## 5. 구조

```
~/.claude/skills/ppt/               산출물 스킬 (전역)
├── SKILL.md                        흐름 + 라우팅 표. 목표 150줄 이하
└── references/                     필요할 때 파일 하나만 읽는다
    ├── deck-spec.md                deck.md 문법
    ├── patterns.md                 장표 패턴 ID와 슬롯 (02 문서 요약)
    ├── charts.md                   차트 ID와 데이터 형태
    ├── editing.md                  읽기 단계(L0~L3)와 패치 명령
    └── onboarding.md               Profile·Brief 질문 목록과 기본값

pptkit (PATH에 설치되는 CLI, Python + python-pptx + pandas)
├── catalogs/tones/*.yaml           톤 프리셋 3종
├── catalogs/patterns/*.yaml        장표 패턴 슬롯 정의
├── catalogs/conventions/*.yaml     업종 관례 팩
├── masters/*.pptx                  기본 마스터 3종
├── sources/*.py                    통계 어댑터 (T0, T1, T2)
└── win/measure.ps1                 PowerPoint COM 실측 (Windows 전용, 선택)

~/.pptkit/                          사용자 데이터 (전역)
├── profile.yaml
├── templates/                      템플릿 분석 캐시
└── cache/                          통계 응답 캐시
```

설치는 `uv tool install`로 한다. uv가 Python까지 관리하므로 Windows에 Python을 따로 설치하지 않아도 된다.

### CLI 명령

| 명령 | 출력 (Claude가 읽는 양) |
|---|---|
| `pptkit profile show / init / set` | Profile 요약 또는 빈 항목 목록 |
| `pptkit style extract old.pptx` | 색·폰트·밀도·문체 통계 (약 100토큰) |
| `pptkit tone resolve` | tone.yaml 생성 + 한 줄 요약 |
| `pptkit data file.csv` | 컬럼·타입·행 수·상위 값 요약 |
| `pptkit pivot file.csv --rows .. --cols .. --val .. --agg ..` | 피벗 CSV + 요약 |
| `pptkit build deck.md [--sample]` | `OK 12 slides, 4 charts, 2 tables` 또는 실패 목록 |
| `pptkit map / read / patch` | 장당 한 줄 맵 / 지정한 장만 / 적용 결과 |
| `pptkit qa [--com]` | 실패 항목만, 통과하면 `OK` |
| `pptkit fetch / key / sources` | 03 문서 참고 |
| `pptkit template add corp.pptx` | 사용자 템플릿 분석 (나중에 템플릿이 생기면) |

### deck.md 예시

```markdown
---
brief: brief.yaml
tone: tone.yaml
source: "사내 판매 데이터, 2026"
---

# 매출은 3년 연속 두 자릿수로 성장했다
pattern: chart-takeaway
chart: column-trend
data: sales.csv
x: year
y: revenue
highlight: 2026
takeaways:
- 2026년 성장률 14%로 목표를 2%p 초과함
- 온라인 채널이 성장분의 70%를 차지함

# 지역별로는 수도권 비중이 절반을 넘는다
pattern: heatmap-table
data: sales.csv
rows: region
cols: year
val: revenue
agg: sum
top: 6
```

## 6. 재사용 판단 (graphify 분석 결과)

- `pptx-from-layouts/scripts/generate_pptx.py`는 6,757줄짜리 단일 파일이다. 레이아웃마다 하드코딩된 `populate_*` 함수가 20여 개 있고, 차트를 그리는 경로가 없다. 그래서 렌더러는 새로 작게 만든다.
- 가져오는 것: 템플릿 분석(`catalog.py`), 겹침·이탈 검사 로직(`lib/inventory.py`), 시각 유형 결정 순서(`rules/visual-types.md`).
- 문서로만 참고하는 것: Anthropic pptx의 차트 함정 목록.

## 7. 토큰 예산 (목표)

| 작업 | 목표 |
|---|---|
| 첫 실행 온보딩 | 질문 5개 이하, 기존 자료가 있으면 2개 이하 |
| 두 번째 실행부터 사전 조사 | Profile 질문 0개, Brief 질문 2개 이하 |
| 10장 새 덱: Claude 출력 | brief + deck.md 합계 1,800토큰 이하 |
| 10장 새 덱: 도구 결과 입력 | 1,000토큰 이하 |
| 30장 중 2장 수정: 입력 / 출력 | 1,100토큰 이하 / 200토큰 이하 |
| 이미지 확인 | 기본 0장 |

## 8. 개발 과정에서 쓰는 스킬

| 스킬 | 쓰는 곳 |
|---|---|
| `skill-creator` | 평가 케이스, with/without 비교, 리뷰 뷰어, description 최적화, 패키징 |
| `graphify` | 재사용 코드와 우리 CLI 코드 탐색 (`dev/graphify/`, git 제외) |
| `ponytail` | CLI 코드 작성 원칙: 표준 라이브러리와 python-pptx 기본 기능 우선, 불필요한 추상화 금지 |
| `dataviz` | 차트 형태 선택 규칙, 팔레트 검증 |
| `theme-factory` | 톤 프리셋 초안 |
| `content-research-writer` | 업종 관례 팩 조사 |
| `xlsx` | 피벗 결과 교차 검증 |
| `anthropic-skills:pptx` | 차트 함정 목록, `validate.py`로 파일 무결성 검사 |

## 9. 평가 케이스

`evals/evals.json`과 가상 데이터(`evals/data/`)를 만들었다. 요약은 다음과 같다.

| # | 상황 | 확인할 것 |
|---|---|---|
| 1 | 첫 실행, Profile 없음. 사업기획 과장이 판매 데이터로 본부장 보고 8장 | 온보딩 질문 수, ask·mode 질문, 톤 시안 단계, 네이티브 차트·피벗, qa 통과 |
| 2 | 같은 데이터, 다른 Profile(공공기관 사무관) | 문체(개조식)·밀도·색·구성이 1번과 달라짐 |
| 3 | 기존 덱의 특정 장 수치 교체와 겹침 정리 | 다른 장 불변, 겹침 0건, 입력 토큰 |
| 4 | 템플릿 없이 신규 서비스 소개 6장 (메모만 제공) | 패턴 다양성, placeholder 잔여 0건 |
| 5 | "최근 5년 한국 GDP 성장률을 넣어 줘" | 키 없이 T1로 처리하거나, 네트워크가 없으면 T0 방법을 한 줄로 안내 |

## 10. 마일스톤

| 단계 | 내용 | 완료 기준 |
|---|---|---|
| M0 | 기획 확정, 평가 케이스, 가상 데이터 | 이 문서 v0.2 ✓ |
| M1 ✓ | 사전 조사(`profile`, `tone`) + `build`(P0 패턴 15개, 차트 3종, 피벗·히트맵) + 톤 3종 + 기본 qa | 예제 17장 덱 qa OK, 테스트 5개 통과. 측정값: deck.md 17장 약 1,390토큰, 도구 결과 합계 약 250토큰 |
| M2 | `map` / `read` / `patch` / `qa` + Windows COM 실측 | 평가 3 토큰 목표 달성 |
| M3 | P1 패턴, `style extract`, `template add` | 평가 4 통과 |
| M4 | `fetch` T1 어댑터, `key` 관리, T2 인터페이스 | 평가 5 통과 |
| M5 | `SKILL.md` 다듬기, description 최적화, 전역 설치 패키징 | 트리거 평가의 test 세트 점수 |

## 11. 환경 이슈

- LibreOffice가 .pptx를 열지 못한 원인은 Impress 모듈 누락이었다. `setup.sh`가 `libreoffice-impress`와 `fonts-nanum`을 설치하도록 고쳤다.
- 통계 API 도메인은 이 컨테이너의 네트워크 정책으로 막혀 있다. 어댑터는 저장해 둔 응답으로 테스트한다.

## 12. 남은 질문

없음. M1 구현 중에 생기는 판단은 이 문서에 결정으로 추가한다.
