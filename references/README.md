# references/

외부 스킬 중 참고 가치가 있고 **MIT 라이선스**인 것만 원본 그대로 반입했다.
이 폴더의 파일은 `.claude/skills/` 밖에 있으므로 **활성 스킬이 아니다.** 세션 컨텍스트에 로드되지 않아 토큰을 쓰지 않는다.
우리 스킬을 만들 때 코드와 규칙을 가져다 쓰기 위한 원천이다.

| 폴더 | 출처 (commit) | 라이선스 | 가져온 것 | 쓸 곳 |
|---|---|---|---|---|
| `pptx-from-layouts/` | [tristan-mcinnis/pptx-from-layouts-skill](https://github.com/tristan-mcinnis/pptx-from-layouts-skill) @ `46e7c66` | MIT (`LICENSE`) | 스킬 3종(`pptx-profile`, `pptx-author`, `pptx-from-layouts`), 데모 템플릿, 예제 outline | 템플릿 프로파일링, 마크다운 → 레이아웃 렌더, 검증 파이프라인 |
| `academic-pptx/` | [Gabberflast/academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill) @ `9f2b703` | MIT (`LICENSE`) | `SKILL.md`, `slide_patterns.md`, `content_guidelines.md` | 액션 타이틀, 차트 주석과 출처 규칙 |
| `style-presets/` | [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) @ `9906a34` | MIT (`LICENSE`) | `STYLE_PRESETS.md` | 톤앤매너 프리셋 원안 (HTML/CSS → PPTX 토큰으로 변환 예정) |

## 반입하지 않은 것

| 스킬 | 이유 |
|---|---|
| anthropics/skills `pptx` | 독점 라이선스. 이 환경에 `anthropic-skills:pptx`로 이미 있으므로 호출해서 쓴다 |
| hugohe3/ppt-master | MIT지만 247MB에 문서가 2.1MB라 너무 무겁다. 차트 코드는 필요할 때 해당 파일만 참고한다 |
| chuspeeism/dashiAI-ppt-skill | AGPL-3.0이라 코드를 반입하지 않는다 |
| anyideaz/pptx-skills | 라이선스 표기가 없다 |
| PHY041 / danny0926 | LICENSE 파일이 없거나(README에만 MIT) 용도가 맞지 않는다 |

## 동작 확인

```bash
pip install python-pptx pydantic
cd references/pptx-from-layouts
python3 pptx-from-layouts/scripts/generate.py examples/outline.md -o /tmp/test.pptx \
  --template templates/inner-chapter.pptx --config templates/inner-chapter-config.json --validate
# → Score: 100/100 ✓ PASS, Errors: 0
```

바로 써 보고 싶다면 원하는 폴더를 `.claude/skills/`로 복사하면 활성화된다.
