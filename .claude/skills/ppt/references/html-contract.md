# 편집형 HTML 변환 규칙 v1

`pptkit html`의 실제 지원 범위다. 일반 웹페이지를 임의로 완벽하게 변환하는 도구는 아니다.
디자인은 HTML/CSS로 조정하되 전달할 요소를 명시한다.

```html
<section class="slide">
  <div data-pptx="shape" style="position:absolute;left:64px;top:120px;width:8px;height:240px;background:#315EF5"></div>
  <h1 data-pptx="text" style="position:absolute;left:96px;top:120px;width:1080px;font-size:48px">이 장의 핵심 주장</h1>
  <p data-pptx="text" style="position:absolute;left:96px;top:220px;width:1020px;font-size:28px">근거를 보여주는 <strong>중요한 문구</strong></p>
  <aside data-notes>화면에는 표시하지 않는 발표자 노트</aside>
</section>
```

공통 CSS는 `*{box-sizing:border-box}`, `.slide{width:1280px;height:720px;position:relative;overflow:hidden}`,
`[data-notes]{display:none}`를 포함한다. 여러 `section.slide`를 순서대로 둔다.
컨테이너·flex·grid를 사용할 수 있지만 슬라이드를 transform으로 축소하지 않는다.
요소는 독립적으로 표시하고 DOM 순서대로 그린다.

| 표시 | 지원 내용 | 주의 |
|---|---|---|
| `data-pptx="text"` | text box. 서체·크기·굵기·색·정렬·줄간격·자간·padding | 내부는 span/b/strong/i/em/u/br만. 블록 단락은 별도 요소 |
| `data-pptx="shape"` | 단색 면, 실선 테두리, 같은 반경의 둥근 사각형, 원·타원 | 색면·테두리는 이 요소에. 자식 글자는 별도 text |
| `data-pptx="image"` | 로컬 img 또는 base64 이미지, object-fit:contain/cover/fill | 중앙 크롭을 native crop으로 반영. 다른 object-position은 미지원. 이미지 속 글자는 편집 불가 |
| `data-pptx="table"` | table → native table | 병합 없는 셀. 글자·색·폭·높이·padding·정렬·테두리 반영 |
| `data-pptx="chart"` | JSON column/bar/line → native chart | data-source로 JSON script id 지정. 같은 데이터로 HTML 시안 작성 |

## 차트

아래 값은 **변환 문법 설명용 가상 데이터**다. 실제 자료는 사용자 데이터 또는 pptkit 계산값을 쓴다.

```html
<div data-pptx="chart" data-source="chart-data" style="position:absolute;left:64px;top:210px;width:800px;height:350px">
  <!-- 같은 JSON으로 HTML 차트를 그린다. 내부는 native chart로 교체된다. -->
</div>
<script id="chart-data" type="application/json">
{"type":"column","categories":["A","B"],"series":[{"name":"검증용","values":[10,20],"color":"315EF5"}],"source":"변환 문법 설명용 가상 데이터","font":"Malgun Gothic"}
</script>
```

출처는 화면에도 표시한다. 데이터 편집은 유지되지만 브라우저 차트의 임의 CSS까지 옮기지는 않는다.
축·라벨·색은 PPT 렌더에서 검수한다. waterfall 등은 기존 Markdown 경로를 사용하거나 지원 제약을 설명한다.
그림으로 바꾸고 데이터 편집이 된다고 말하지 않는다.

Studio는 로컬 Chart.js와 `charts.js`로 같은 JSON의 브라우저 차트를 그린다.
`font`, `fontSize`, `labelColor`, `gridColor`, `maxValue`, `majorUnit`, `numberFormat`, `showValues`로
PPT의 폰트·축·라벨을 조정한다. 자동 제목은 끄고 별도의 편집형 텍스트로 제목과 단위를 표시한다.
`window.pptkitReady`가 있으면 렌더 완료를 기다린 후 측정한다.

## 중단하는 표현

gradient·background image·box-shadow·filter·mask·clip-path·transform·z-index·pseudo-element,
직접 SVG/canvas/video/iframe, 표시 없는 본문은 오류로 처리한다.
본문을 이미지로 바꾸지 않는다. 사진은 img, 관계도는 기본 도형, 복잡한 장식은 단순한 구도로 바꾼다.
텍스트 `letter-spacing`은 native 자간으로 지원한다. `text-transform`·`white-space` 변경은 미지원이다.
문구와 br을 직접 작성한다.
전체 장표 이미지로의 자동 대체는 없다.

로컬 CSS·폰트를 사용한다. 원격 HTTP 리소스는 브라우저에서 차단하므로 필요한 파일을 먼저 저장한다.
사용자가 제공한 HTML은 스크립트를 확인하고 신뢰할 수 있는 로컬 자료로 정리한다.

## 명령과 결과

```bash
pptkit html init deck.html
pptkit html preview deck.html
pptkit html build deck.html -o deck.pptx
pptkit html render deck.pptx
pptkit qa deck.pptx --com
```

- `preview`: 구조 검사 + HTML PNG + contact sheet. 디자인은 직접 확인한다.
- `build`: native 요소 생성 + 저장된 텍스트 대조. 실패하면 기존 PPT를 대체하지 않는다.
- `deck.editable.json`: 요소 수와 텍스트 보존 결과. `visual_review: pending`은 의도적이다.
- `render`: Windows PowerPoint 또는 다른 OS의 LibreOffice로 PNG 생성. 미적 통과를 뜻하지 않는다.
- HTML은 그대로 유지한다. HTML 수정 후 재변환하며 이전 감사용 사본을 몰래 재사용하지 않는다.
