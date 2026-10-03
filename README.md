# Awesome-PPT-SKILL

원하는 **내용 · 템플릿 · 톤앤매너**로 PowerPoint를 생성하는 Claude Code 스킬.
자주 쓰는 도표 양식을 카탈로그로 미리 정의해 두고, 통계 데이터와 피벗테이블을 네이티브 차트와 표로 보기 좋게 넣는다. 토큰 절감을 1급 목표로 둔다.

## 설치

```bash
git clone https://github.com/coindesktop/Awesome-PPT-SKILL.git && cd Awesome-PPT-SKILL
./scripts/setup.sh   # python-pptx, markitdown, pandas, pptxgenjs 등. 이미 있으면 건너뜀
```

이 폴더에서 `claude`를 실행하면 `.claude/skills/`의 스킬이 자동으로 로드된다.
Claude Code 클라우드 세션에서는 SessionStart 훅(`.claude/settings.json`)이 `setup.sh`를 자동으로 실행한다.

Anthropic 공식 `pptx` 스킬(네이티브 차트 규칙과 `validate.py`)도 함께 쓰려면 다음을 실행한다. 독점 라이선스라 레포에는 넣지 않았다.

```bash
claude plugin marketplace add anthropics/skills
claude plugin install document-skills@anthropic-agent-skills
```

## pptkit 빠른 사용

```bash
pip install -e .            # 또는: uv tool install git+https://github.com/coindesktop/Awesome-PPT-SKILL
pptkit install-skill        # ~/.claude/skills/ppt 로 스킬 복사 (전역 사용)

pptkit profile              # 나는 누구인가 (없으면 빈 항목만 질문 목록으로 출력)
pptkit tone --brief brief.yaml
pptkit data data.csv        # 원본 대신 요약만 출력
pptkit build deck.md --sample   # 톤 시안 2장
pptkit build deck.md && pptkit qa deck.pptx
```

예제: [`examples/sales-report/`](examples/sales-report/deck.md) (P0 패턴 15개를 모두 쓰는 17장 덱). 테스트: `python tests/test_pptkit.py`

## 설치된 것

| 구분 | 이름 | 용도 |
|---|---|---|
| 스킬 | `pptx-profile` | 내 .pptx 템플릿을 레이아웃 카탈로그와 `config.json`으로 변환 (템플릿당 1회) |
| 스킬 | `pptx-author` | `[HINT: 레이아웃]`이 붙은 `slides.md` 작성과 lint |
| 스킬 | `pptx-from-layouts` | `slides.md`를 템플릿 레이아웃에 채워 `.pptx`로 렌더하고 검증 |
| CLI | `markitdown` | `.pptx`/`.xlsx`를 텍스트로 추출 (토큰이 적은 읽기 방식) |
| Python | `python-pptx`, `pandas`, `openpyxl`, `matplotlib` | 렌더, 피벗, 차트 |
| Python | `wbgapi`, `PublicDataReader` | World Bank / KOSIS·공공데이터포털 통계 수집 |
| npm | `pptxgenjs` | 네이티브 차트 생성 (Anthropic pptx 스킬 방식) |
| 시스템 | `soffice`, `pdftoppm` | 렌더 QA (슬라이드 → 이미지) |

## 빠른 확인

```bash
python3 .claude/skills/pptx-from-layouts/scripts/generate.py examples/q1-strategy-outline.md -o out.pptx --validate
# → Score: 100/100 ✓ PASS
```

## 문서

- [`docs/plan/01-spec.md`](docs/plan/01-spec.md): 기획 v0.2 (결정 사항, 실행 흐름, CLI, 토큰 예산, 마일스톤)
- [`docs/plan/02-slide-patterns.md`](docs/plan/02-slide-patterns.md): 장표 패턴 카탈로그
- [`docs/plan/03-data-sources.md`](docs/plan/03-data-sources.md): 통계 데이터 연결 설계
- [`docs/plan/04-personalization.md`](docs/plan/04-personalization.md): 개인화 사전 조사 설계 (Profile → Brief → Tone)
- [`evals/`](evals/evals.json): 평가 케이스 5개와 가상 데이터
- [`docs/research/landscape.md`](docs/research/landscape.md): 공개 PPT 스킬 9종 비교와 토큰 절감 설계 원칙
- [`references/`](references/README.md): 참고용 MIT 스킬 원본 (비활성)

## 로드맵

1. ~~조사와 레퍼런스 확보~~
2. ~~기존 스킬과 CLI 설치~~
3. ~~M1: 개인화 사전 조사 + build(패턴 15개, 차트 3종, 피벗) + 톤 3종 + qa~~
4. M2: map / read / patch + Windows COM 실측
5. M3: P1 패턴, 기존 자료 스타일 추출, 사용자 템플릿
6. M4: 통계 fetch (키 없는 공개 API)
7. M5: 평가 루프, description 최적화, 패키징
