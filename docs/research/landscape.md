# PPT 생성 스킬 조사 (2026-10)

목표: **원하는 내용 · 원하는 템플릿 · 원하는 톤앤매너**로 PPT를 만드는 스킬/CLI.
자주 쓰는 도표 양식을 미리 정의해 두고 골라 쓰게 하며, 통계 데이터와 피벗테이블을 보기 좋게 넣고, 토큰을 적게 쓴다.

## 요구사항

| ID | 요구사항 |
|---|---|
| R1 | 원하는 내용: 개요/브리프 → 슬라이드 |
| R2 | 원하는 템플릿: 내 회사 .pptx 마스터/레이아웃을 그대로 사용 |
| R3 | 원하는 톤앤매너: 색·폰트·밀도·문체 프리셋 |
| R4 | 도표 양식 카탈로그: 자주 쓰는 양식을 미리 정의해 두고 골라 씀 |
| R5 | 통계 데이터 → 적절한 **네이티브(편집 가능) 차트** |
| R6 | 피벗테이블 가독성: 합계·조건부 서식·숫자 포맷·긴 표 분할 |
| R7 | 토큰 절감: LLM이 쓰는 양과 읽는 양을 최소화 |

## 비교

✓ 충족 · △ 일부 · ✗ 없음

| 스킬 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | 라이선스 | 비고 |
|---|---|---|---|---|---|---|---|---|---|
| [anthropics/skills `pptx`](https://github.com/anthropics/skills/tree/main/skills/pptx) | ✓ | △ | △ | ✗ | ✓ | ✗ | ✗ | Proprietary | 이 환경에 `anthropic-skills:pptx`로 이미 설치됨. pptxgenjs 차트 함정 목록과 `validate.py`가 핵심 자산. 매 덱마다 LLM이 생성 코드를 직접 작성하므로 토큰 소모가 큼 |
| [tristan-mcinnis/pptx-from-layouts-skill](https://github.com/tristan-mcinnis/pptx-from-layouts-skill) | ✓ | ✓✓ | △ | ✓ | ✗ | △ | ✓✓ | MIT | **구조가 가장 근접.** 템플릿 프로파일링 → `[HINT:]`/`**Visual:**` 마크다운 → 스크립트 렌더 → 100점 검증. LLM은 마크다운만 쓴다. 네이티브 차트 없음 |
| [Gabberflast/academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill) | ✓ | ✗ | △ | △ | △ | ✗ | △ | MIT | 액션 타이틀, "슬라이드당 차트 1개 + 핵심값 주석", 출처 표기 규칙 |
| [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | △ | MIT | HTML 슬라이드. 톤앤매너 프리셋 12종과 "AI 티 나는 패턴 금지" 목록만 참고 |
| [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master) | ✓ | ✓ | ✓ | ✓ | ✓ | △ | ✗✗ | MIT | 기능은 가장 많음(네이티브 차트/표, 템플릿, 애니메이션). 대신 문서만 2.1MB, 레포 247MB, 단계마다 사용자 확인 게이트, attribution guard가 있어 토큰 목적과 정반대. `scripts/svg_to_pptx/native_objects/chart_*.py`만 참고 가치 |
| [chuspeeism/dashiAI-ppt-skill](https://github.com/chuspeeism/dashiAI-ppt-skill) | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | **AGPL-3.0** | HTML 우선, 12테마, 레이아웃 1020개. 페이지마다 3+1안을 생성해 토큰 소모가 큼. AGPL이라 코드 반입 금지, 아이디어만 참고 |
| [anyideaz/pptx-skills](https://github.com/anyideaz/pptx-skills) | ✓ | ✓ | △ | △ | △ | ✗ | △ | 표기 없음 | 템플릿 분석 → `guideline.md` + `sample_code.js` 생성 후 재사용하는 아이디어. 라이선스가 없어 링크만 둠 |
| [PHY041/claude-skill-academic-ppt](https://github.com/PHY041/claude-skill-academic-ppt) | ✓ | ✗ | △ | △ | △ | ✗ | △ | MIT(README) | python-pptx `BaseTemplate` 클래스로 장면별 템플릿을 정의하는 방식 |
| [danny0926/ppt-skills](https://github.com/danny0926/ppt-skills) | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | △ | MIT(README) | 손그림(rough.js) 스타일 전용이라 용도가 맞지 않음 |

## 결론

**요구사항을 전부 충족하는 스킬은 없다.** 그래서 그대로 쓸 수 있는 `pptx-from-layouts` 3종만 `.claude/skills/`에 활성화하고, 나머지 MIT 레퍼런스는 `references/`에 비활성 상태로 두었다(컨텍스트를 쓰지 않음).

- 뼈대: `pptx-from-layouts`의 *프로파일 → 마크다운 작성 → 스크립트 렌더 → 검증* 파이프라인 (R2, R4, R7)
- 차트: `anthropic pptx`의 네이티브 차트 규칙 + `ppt-master`의 chart data 접근 (R5)
- 내용 규칙: `academic-pptx`의 액션 타이틀과 exhibit discipline (R1, R5)
- 톤앤매너: `frontend-slides` 프리셋을 PPTX 토큰(색·폰트·밀도)으로 옮김 (R3)
- **새로 만들 부분**: 차트·피벗 카탈로그, 통계 수집 → CSV → 차트 파이프라인, 피벗 표 렌더러 (R4, R5, R6)

## 토큰 절감 설계 원칙 (튜닝 단계에서 적용)

1. **LLM은 스펙만, 렌더는 스크립트가.** 슬라이드마다 코드를 생성하지 않는다. LLM은 짧은 `deck.md`(슬라이드별 `layout`/`chart`/`data` 참조)만 쓰고 Python 렌더러가 나머지를 처리한다.
2. **데이터는 LLM을 거치지 않는다.** 원본 CSV와 xlsx는 스크립트가 읽고, LLM에는 `data_profile.py`의 요약(컬럼, 행 수, 상위 값)만 보낸다. 피벗 계산은 pandas가 한다.
3. **점진적 로딩.** `SKILL.md`는 라우팅 표만 담고 짧게 유지한다. 차트 카탈로그, 톤 프리셋, 템플릿 카탈로그는 필요할 때만 해당 파일 하나를 읽는다.
4. **카탈로그는 ID로 참조한다.** `chart: bar-ranked`, `tone: corporate-navy`처럼 ID만 쓰고 세부 옵션은 YAML 기본값에 둔다.
5. **템플릿 프로파일링은 한 번만.** 결과(`config.json`, `catalog.md`)를 캐시하고 재사용한다.
6. **QA는 스크립트 점수부터.** 렌더 이미지는 실패하거나 경고가 난 슬라이드만 확인한다.
