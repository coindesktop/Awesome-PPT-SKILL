# Awesome-PPT-SKILL

**사람을 먼저 파악하고, 그 사람에게 맞는 톤앤매너로 PPT를 만들고 고치는 Claude 스킬 + CLI(`pptkit`).**

- Claude는 짧은 텍스트 파일(`brief.yaml`, `deck.md`, `ops.yaml`)만 씁니다. 렌더링, 피벗, 검증, 편집은 미리 만든 CLI가 합니다. 그래서 토큰이 적게 들고, 같은 입력에서 같은 덱이 나옵니다.
- 차트와 표는 PowerPoint 네이티브 객체라서 "데이터 편집"으로 숫자를 고칠 수 있습니다. 사진은 넣지 않습니다.
- 덱 구성은 지어내지 않습니다. 목적(피칭, 고객 제안, 보고, 기획안, 교육)을 묻고, 검증된 구성안(VC 시드, Sequoia, 트랙션 우선, 데모데이, 정부지원사업 PSST 등)을 보여 주고, 사용자가 고른 구성으로 만듭니다.
- 디자인은 DESIGN.md 파일 하나로 정의합니다. 기본 9종(기업 보고 corporate, executive, signal, forest, public, 피칭용 launch·bold, 흑백 mono, 카드형 soft)이 있고, `pptkit design show <이름>`으로 견본 덱을 만들어 볼 수 있습니다. 예전에 만든 덱에서 개인 디자인을 추출할 수도 있습니다. [디자인 갤러리](docs/designs.md)

## 설치 (Windows · macOS · Linux)

```bash
uv tool install git+https://github.com/coindesktop/Awesome-PPT-SKILL   # Python이 없어도 uv가 준비합니다
pptkit install-skill                                                  # ~/.claude/skills/ppt 에 스킬 복사
```

개발용: `git clone` 후 `./scripts/setup.sh` (의존성, `pip install -e .`, 렌더 확인용 LibreOffice·한국어 폰트).

## 쓰는 법

Claude Code에서 "이 CSV로 본부장 보고용 PPT 8장 만들어줘"처럼 요청하면 `ppt` 스킬이 아래 순서로 진행합니다.

| 단계 | 명령 | Claude가 읽는 양 |
|---|---|---|
| 사람 파악 (한 번만) | `pptkit profile` / `pptkit style extract old.pptx` | 한 줄 또는 빈 항목 목록 |
| 목적 → 구성안 선택 | `pptkit plan` → `pptkit plan pitch` → `pptkit plan pitch/vc-seed -o deck.md` | 구성안 목록, 뼈대와 내용 질문 |
| 이번 덱 파악 | `brief.yaml` 작성 → `pptkit tone --brief brief.yaml` | 디자인·문체·규칙 3줄 |
| 데이터 | `pptkit data a.csv b.csv` / `pptkit pivot ... [--bridge 2025,2026]` / `pptkit fetch wb ...` | 파일당 요약 약 100토큰 |
| 덱 문법 | `pptkit spec progress waterfall` | 쓰는 패턴의 키만 |
| 톤 시안 | `pptkit build deck.md --sample` | 한 줄 |
| 생성·점검 | `pptkit build deck.md` (qa 포함, Windows는 `pptkit qa --com`) | 한 줄, 문제만 |
| 기존 덱 수정 | `pptkit map` → `pptkit read -s 3,5` → `pptkit patch deck.pptx ops.yaml` | 장당 한 줄 + 필요한 장만 |

전체 명령: `pptkit -h`. 스킬 문서: [`.claude/skills/ppt/SKILL.md`](.claude/skills/ppt/SKILL.md), 덱 문법: [`deck-spec.md`](.claude/skills/ppt/references/deck-spec.md), 편집 문법: [`editing.md`](.claude/skills/ppt/references/editing.md).

## 들어 있는 것

| 구분 | 내용 |
|---|---|
| 개인화 | Profile(사람) × Brief(이번 덱) → 디자인·문체·밀도·업종 관례. 프로필은 `~/.pptkit/`에 저장되어 다시 묻지 않음 |
| 디자인 | `pptkit/designs/*.md` 9종 + 사용자 DESIGN.md(`~/.pptkit/designs/`), 카드 표현 토큰(채움·외곽선·그림자), `pptkit design show`(토큰 장표가 든 견본), 회사 템플릿 위 렌더링(마스터·로고 유지) |
| 구성안 | `pptkit/storylines.yaml`: 목적 5종 × 구성안 14개, 장표별 내용 질문 |
| 아이콘 | Lucide 선 아이콘 136종을 편집 가능한 벡터 도형으로(`icon: rocket`), 사진 없음 |
| 장표 패턴 | 36종: 피칭(pillars, traction, team, pricing, product-shot, funding-ask) 외 구조(표지·목차·섹션·요약·결론), 메시지, 비교(compare, compare-table, before-after, swot, matrix-2x2, logic-tree), 흐름(process, timeline, roadmap, gantt, funnel), 진척(progress, status-table), 데이터(chart-takeaway, chart-table, chart-pair, pivot, heatmap, kpi-tiles, big-number, market-size) |
| 차트 | column-trend, line-trend, bar-ranked, stacked, stacked-share, waterfall(증감 요인), donut(구성비) (검증된 팔레트, 단일 강조색, 이중 축 없음) |
| 데이터 | CSV/XLSX, KOSIS 다운로드 형식 자동 정리, 피벗(합계·상위 N+기타·가중 평균) |
| 통계 | World Bank(키 없음), KOSIS(사용자 키, 터미널에서 직접 등록), 캐시와 출처 자동 각주 |
| 반복 보고 | `vars:`로 숫자를 데이터에 연결(`$rev`), `latest`/`prev` 기간 단어: 새 달 데이터를 넣고 다시 빌드하면 제목·KPI·차트가 함께 갱신되고 바뀐 숫자를 알려 줌 |
| 편집 | 아무 .pptx나 map/read/patch: 텍스트·위치·차트 데이터·표·일괄 치환·겹침 정리·노트 |
| 점검 | 겹침·넘침·이탈·잔여 placeholder, Windows에서는 PowerPoint로 글자 높이 실측(`--com`) |

## 예제

[`docs/gallery.md`](docs/gallery.md): 목적·디자인별 예제 10종의 미리보기와 원본(deck.md·CSV·pptx).

![매출 보고 예제](docs/gallery/sales-report.jpg)

## 검증

- 테스트: `python tests/test_pptkit.py`
- 평가: [`evals/evals.json`](evals/evals.json) 5개 시나리오, 채점 [`evals/grade.py`](evals/grade.py), 결과 [`docs/evals/`](docs/evals/)

## 문서

- 기획: [`docs/plan/01-spec.md`](docs/plan/01-spec.md), [장표 패턴](docs/plan/02-slide-patterns.md), [통계 연결](docs/plan/03-data-sources.md), [개인화](docs/plan/04-personalization.md)
- 조사: [`docs/research/landscape.md`](docs/research/landscape.md), 레퍼런스: [`references/`](references/README.md)

## 저장소 구성

```
pptkit/                CLI (render, patterns_p1, edit, qa, data, persona, style, sources) + designs/ + catalog.yaml
.claude/skills/ppt/    배포되는 스킬 (pptkit install-skill 이 복사)
examples/              예제 덱 11종: 보고(매출·월간·마케팅·인사·프로젝트), 제안(신사업·고객), 피칭(VC·PSST), 교육, 패턴 모음
evals/                 평가 시나리오, 가상 데이터, 채점기
references/            참고한 MIT 스킬·DESIGN.md 원본 (비활성)
.claude/skills/        개발 세션용 스킬들 (ppt 외에는 개발 보조용)
```
