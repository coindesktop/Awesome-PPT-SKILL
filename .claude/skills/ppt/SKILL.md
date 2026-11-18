---
name: ppt
description: >-
  Create and revise PowerPoint decks with HTML-first visual design, browser previews,
  and editable native PowerPoint text, shapes, tables and charts. Use for presentations,
  proposals, reports, pitches, education and edits to .pptx files. Includes pptkit data
  analysis and a separate repeatable Markdown report workflow.
---

# ppt

목표는 **다른 사용자가 별도의 디자인 지시를 하지 않아도 읽기 좋고 편집 가능한 PPT를 얻는 것**이다.
새 자료는 **HTML 디자인 → 브라우저 검수 → 편집형 PPT 변환 → PPT 시각 검수**로 만든다.
구조 검사 통과와 디자인 품질은 다른 결과다. `QA OK`만 보고 완성됐다고 말하지 않는다.

## 작업 경로

- **새 자료·디자인 개선:** [Studio 디자인 시스템](references/studio-system.md)과 [디자인 방법](references/html-first-design.md)을 먼저 읽고 아래 흐름을 따른다.
- **수치만 갱신하는 반복 보고·기존 deck.md 유지:** [Markdown 보고 흐름](references/markdown-workflow.md).
- **기존 HTML 수정:** HTML을 수정하고 변환·검수를 반복한다. PPT만 고치고 원본을 방치하지 않는다.
- **외부 PPT 일부 수정:** `pptkit map` → `pptkit read` → `pptkit patch`. [편집 문법](references/editing.md).
  기존 구도를 보존하고 수정한 장표를 렌더해 확인한다.

## 준비

```bash
uv tool install --force "pptkit[html] @ git+https://github.com/coindesktop/Awesome-PPT-SKILL"
pptkit html setup
pptkit install-skill
```

개발 중에는 저장소에서 `uv pip install -e ".[html]"`로 설치한다. Chromium은 `html setup`이 준비한다.
PPT 렌더에는 Windows PowerPoint 또는 LibreOffice가 필요하다.
의존성이 없으면 설치 방법과 가능한 검수 범위를 알린다. 전체 장표 이미지로 우회하지 않는다.

## 새 자료 제작

### 1. 전달할 내용을 정한다

요청과 첨부 자료에서 목적, 독자, 핵심 주장, 분량, 발표용/배포용을 파악한다.
결과를 바꿀 만큼 중요한 정보만 묻는다. 샘플 요청이나 위임받은 작업은 가정을 짧게 밝히고 진행한다.
`pptkit profile`의 기존 선호와 `pptkit plan <purpose>`의 구성안을 참고한다.
사용자가 정한 구조를 우선한다. 임시로 추정한 직무·취향을 영구 프로필에 저장하지 않는다.
`brief.yaml`에 목적·독자·요청 행동·분량·문체를 기록하고 `pptkit tone --brief brief.yaml`을 참고한다.
실행 기획안이면 [운영 가능한 제안서](references/practical-proposals.md)를 읽고 대상·일정·물량·예산·담당·예외를 서로 맞춘다.

### 2. 디자인 방향과 에셋을 정한다

Studio의 세 방향 중 목적에 맞는 하나를 선택한다. 편집형 `editorial`은 사진·큰 문장·비대칭,
제품형 `product`는 사용자가 받거나 쓰는 것·사용 흐름·행동, 전략형 `strategy`는 지표·차트·비교·결정이 중심이다.
각 방향은 토큰·정보 밀도·대표 구도가 다르다. 색만 바꾼 같은 덱 세 개를 만들지 않는다.
사용자 브랜드에 맞게 의미 토큰과 에셋을 바꾸되, 구도의 비율과 읽는 순서는 유지한다.

HTML 작성 전에 `design.md`에 독자가 결정할 일, 서체·배경·강조색·정보 밀도,
장표별 주장·근거·구도, 필요한 에셋의 역할·출처·편집 여부를 짧게 기록한다.
사용자 레퍼런스에서는 크기 비율·정렬·여백·이미지 처리 방식을 추출한다.
문구와 브랜딩을 복제하지 않는다. 레퍼런스가 없어도 주제와 독자에 맞춰 방향을 정한다.
판단 기준과 에셋 제작 예시는 [디자인 방법](references/html-first-design.md)에 있다.
먼저 이용자가 실제로 받거나 쓰는 것, 또는 주장을 입증하는 근거를 찾는다.
서비스·교육·프로그램의 대표 비주얼은 [사용물 중심 에셋](references/working-artifacts.md)의 선택 기준을 따른다.
추상적인 장식보다 안내지·기록지·실물·화면처럼 내용을 설명하는 대상을 크게 보여준다.

### 3. HTML을 만든다

```bash
pptkit html designs
pptkit html init deck.html --design editorial
```

생성된 파일은 선택한 디자인 시스템의 6장 견본이다. 함께 복사된 `deck.assets/layouts.json`에서
주장에 맞는 구도를 고르고 견본의 문구·가상 데이터·이미지를 사용자 자료로 바꾼다.
견본의 타이포 비율·여백·대비는 기준으로 삼고 장수·순서는 내용에 맞춰 구성한다.
`deck.assets/components/working-artifacts.html`에는 안내지·기록지, 교육 검토지, 실행 조건표의 편집형 예제 3장이 있다.
필요한 장표의 구조를 가져오고 내용·색·서체는 현재 덱에 맞춘다. 모든 덱에 사용물을 억지로 만들지는 않는다.
브라우저용 Pretendard 서체가 포함된다. PPT를 여는 PC에는 같은 서체를 설치해야 한다.
각 `section.slide`는 1280×720px 고정 크기다. 공통 색·서체는 CSS 변수로 관리하고,
[HTML 변환 규칙](references/html-contract.md)에 맞춰 `data-pptx`를 표시한다.
HTML/CSS와 로컬 에셋을 직접 작성할 수 있다.

본문·기본 도형·관계도는 편집 가능한 요소로 유지한다. 사진·일러스트·화면은 이미지로 넣는다.
이미지에 제목·데이터 라벨을 함께 굳히지 않는다. 변환을 방해하는 장식은 표현을 단순화한다.
수치는 사용자 자료 또는 `pptkit data/pivot/fetch` 결과에서 가져온다. 빈 공간을 채우려고 수치를 만들지 않는다.
출처·단위·기간을 표시한다. 목업과 검증용 가상 자료는 명확히 구분한다.

### 4. HTML을 눈으로 검수한다

```bash
pptkit html preview deck.html
```

표지·핵심 근거·가장 복잡한 장표를 먼저 만든 뒤 실제 PNG를 열어 본다. 방향을 다듬고 나머지를 확장한다.
사용자 선택이 필요한 경우만 의견을 묻는다. 모든 작업에 별도 시안 승인을 강제하지 않는다.
전체 contact sheet로 구도 반복과 정보 밀도를 보고, 개별 장표로 한글 줄바꿈·작은 글자·정렬·누락을 본다.
주장, 먼저 보이는 요소, 이를 뒷받침하는 근거가 명확해야 한다. DOM 검사만으로 이 단계를 대신하지 않는다.

### 5. 편집 가능한 PPT로 변환한다

```bash
pptkit html build deck.html -o deck.pptx
pptkit html render deck.pptx
```

텍스트는 text box, 단색 면·선·원은 native shape, 표는 native table이다.
지원되는 데이터 차트는 embedded workbook을 가진 native chart다.
미지원 표현은 오류로 알리며 전체 장표 이미지로 대체하지 않는다.
`deck.editable.json`의 텍스트 보존 결과와 이미지 개수를 확인한다.

### 6. PPT 결과까지 확인하고 전달한다

- 같은 장표의 HTML과 PPT 렌더를 비교한다. 누락·줄바꿈·깨진 한글·겹침·시각적 위계 변화를 고친다.
- 요구한 편집성이 남았는지 확인한다. 벡터 그림과 데이터 편집 가능한 차트는 구분한다.
- Windows에서는 `pptkit qa deck.pptx --com`으로 실제 글자 높이도 확인한다.
- 여백 경고는 시각적으로 판단한다. 여백을 없애려고 불필요한 내용을 추가하지 않는다.
- 수정은 HTML에 반영하고 다시 변환·렌더한다. 미지원 표현은 지원 범위 안에서 재설계한다.
- 렌더를 실행할 수 없으면 `시각 검수 미완료`라고 전달한다.

최종 `.pptx`, 편집 원본 `.html`, 사용 에셋, 미리보기 경로를 제공한다.
직접 확인한 범위와 실제 남은 제약을 짧게 적는다.

사용자 선호와 업무 맥락을 존중한다. 모든 자료를 같은 색·사진 스타일로 만들지 않는다.
HTML은 디자인 원본이며, 같은 원본을 재변환하면 수정 사항이 반영되어야 한다.
정확성·시각적 전달력·편집성을 각각 확인한다.
