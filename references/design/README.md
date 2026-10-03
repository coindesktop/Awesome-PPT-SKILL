# references/design

pptkit 디자인(`pptkit/designs/*.md`)을 만들 때 참고한 DESIGN.md 원본이다. 활성 스킬이 아니므로 세션 토큰을 쓰지 않는다.

| 폴더 | 출처 (commit) | 라이선스 | 내용 | 반영한 곳 |
|---|---|---|---|---|
| `slides/` | [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides) `bold-template-pack` @ `9906a34` | MIT (`slides/LICENSE`) | 슬라이드 전용 DESIGN.md 4종: blue-professional, signal, grove, mat | executive ← blue-professional, signal ← signal, forest ← grove + mat |
| `web/` | [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) @ `f696123` | MIT (`web/LICENSE`) | 웹 UI용 브랜드 DESIGN.md 4종: ibm, notion, linear.app, stripe | DESIGN.md 형식(색 역할, 타이포 위계, Do/Don't)의 예시. 사용자가 자기 회사 DESIGN.md를 만들 때 견본 |

## 원칙 (레퍼런스에서 추출)

1. 강조색은 하나만 쓴다. 제목은 거의 검은색, 강조색은 라벨·숫자·강조 막대에만 쓴다.
2. 모든 본문 장표는 같은 리듬을 따른다: 섹션 라벨 → 제목 → 메시지 → 본문 → 출처.
3. 층은 그림자가 아니라 색조 카드와 가는 테두리로 만든다.
4. 본문은 회색 계열로 한 단계 낮추고, 숫자는 크게 강조색으로 쓴다.
5. 장식은 표지와 결론에만 둔다.
6. 정보 칸이 적으면 오히려 빈약해 보이므로 장표당 3~6칸을 기준으로 삼는다.

브랜드 DESIGN.md(`web/`)는 실제 회사의 시각 정체성을 묘사한다. 그 회사를 흉내 내는 덱을 만드는 용도로 쓰지 않고, 형식과 원리를 배우는 용도로만 쓴다.
