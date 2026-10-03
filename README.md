# Awesome-PPT-SKILL

원하는 **내용 · 템플릿 · 톤앤매너**로 PowerPoint를 생성하는 Claude Code 스킬.
자주 쓰는 도표 양식을 카탈로그로 미리 정의해 두고, 통계 데이터와 피벗테이블을 네이티브 차트와 표로 보기 좋게 넣는다. 토큰 절감을 1급 목표로 둔다.

## 현재 상태: 1단계 (조사와 레퍼런스 확보)

- [`docs/research/landscape.md`](docs/research/landscape.md): 공개 PPT 스킬 9종 비교, 결론, 토큰 절감 설계 원칙
- [`references/`](references/README.md): MIT 레퍼런스 스킬 원본 (비활성, 컨텍스트 미사용)

## 로드맵

1. ~~조사와 레퍼런스 확보~~
2. 뼈대: `deck.md` 스펙 → Python 렌더러 (pptx-from-layouts 파이프라인 기반)
3. 톤앤매너 프리셋 (`tones/*.yaml`)과 내 템플릿 프로파일링
4. 차트 카탈로그 (`charts/*.yaml`, 네이티브 차트)와 피벗 표 렌더러
5. 통계 수집 (KOSIS / World Bank 등) → CSV → 차트 파이프라인
6. QA (검증 점수 + 실패 슬라이드만 렌더 확인)
