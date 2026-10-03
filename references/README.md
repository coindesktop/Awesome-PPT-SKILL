# references/

외부 스킬 중 참고 가치가 있고 **MIT 라이선스**인 것만 원본 그대로 반입했다.
이 폴더의 파일은 `.claude/skills/` 밖에 있으므로 **활성 스킬이 아니다.** 세션 컨텍스트에 로드되지 않아 토큰을 쓰지 않는다.
우리 스킬을 만들 때 코드와 규칙을 가져다 쓰기 위한 원천이다.

| 폴더 | 출처 (commit) | 라이선스 | 가져온 것 | 쓸 곳 |
|---|---|---|---|---|
| `academic-pptx/` | [Gabberflast/academic-pptx-skill](https://github.com/Gabberflast/academic-pptx-skill) @ `9f2b703` | MIT (`LICENSE`) | `SKILL.md`, `slide_patterns.md`, `content_guidelines.md` | 액션 타이틀, 차트 주석과 출처 규칙 |
| `design/` | 아래 [design/README.md](design/README.md) 참고 | MIT | 슬라이드·웹 DESIGN.md 8종 | pptkit 디자인 4종의 원본 |
| `style-presets/` | [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) @ `9906a34` | MIT (`LICENSE`) | `STYLE_PRESETS.md` | 톤앤매너 프리셋 원안 (HTML/CSS → PPTX 토큰으로 변환 예정) |

## 반입하지 않은 것

| 스킬 | 이유 |
|---|---|
| anthropics/skills `pptx` | 독점 라이선스. 이 환경에 `anthropic-skills:pptx`로 이미 있으므로 호출해서 쓴다 |
| hugohe3/ppt-master | MIT지만 247MB에 문서가 2.1MB라 너무 무겁다. 차트 코드는 필요할 때 해당 파일만 참고한다 |
| chuspeeism/dashiAI-ppt-skill | AGPL-3.0이라 코드를 반입하지 않는다 |
| anyideaz/pptx-skills | 라이선스 표기가 없다 |
| PHY041 / danny0926 | LICENSE 파일이 없거나(README에만 MIT) 용도가 맞지 않는다 |

## 활성화한 스킬

[tristan-mcinnis/pptx-from-layouts-skill](https://github.com/tristan-mcinnis/pptx-from-layouts-skill) @ `46e7c66` (MIT)은 그대로 쓸 수 있어서 `.claude/skills/`로 옮겨 활성화했다.
스킬은 `pptx-profile`, `pptx-author`, `pptx-from-layouts` 3종이고, 데모 템플릿은 `templates/`, 예제는 `examples/`에 있다.
각 스킬 폴더와 `templates/LICENSE-inner-chapter`에 원본 LICENSE를 두었다.
