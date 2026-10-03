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

- [`docs/research/landscape.md`](docs/research/landscape.md): 공개 PPT 스킬 9종 비교와 토큰 절감 설계 원칙
- [`references/`](references/README.md): 참고용 MIT 스킬 원본 (비활성)

## 로드맵

1. ~~조사와 레퍼런스 확보~~
2. ~~기존 스킬과 CLI 설치~~
3. 톤앤매너 프리셋 (`tones/*.yaml`)과 내 템플릿 프로파일링
4. 차트 카탈로그 (`charts/*.yaml`, 네이티브 차트)와 피벗 표 렌더러
5. 통계 수집 → CSV → 차트 파이프라인
6. QA (검증 점수 + 실패 슬라이드만 렌더 확인)
