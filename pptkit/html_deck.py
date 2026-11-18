"""HTML contract v1: Chromium layout -> native PowerPoint objects.

Only explicitly supported elements are exported. Unsupported visible content fails
before writing a PPTX; no full-slide screenshot fallback is used.
"""
import base64
from collections import Counter
from io import BytesIO
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlparse
from urllib.request import url2pathname

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_TICK_MARK, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

HERE = Path(__file__).parent / "html_runtime"
WIDTH, HEIGHT = 1280, 720


def _playwright():
    try:
        from playwright.sync_api import sync_playwright
        return sync_playwright
    except ImportError as exc:
        raise RuntimeError('HTML 의존성이 없습니다. pptkit[html]을 설치하고 pptkit html setup을 실행하세요.') from exc


def _measure(source, previews=None):
    source = Path(source).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    with _playwright()() as pw:
        try:
            browser = pw.chromium.launch()
        except Exception as exc:
            raise RuntimeError('Chromium 실행 실패. pptkit html setup을 실행하세요. ' + str(exc)[:200]) from exc
        try:
            page = browser.new_page(viewport={"width": WIDTH, "height": HEIGHT}, device_scale_factor=1)
            # Decks are local artifacts. External dependencies must be downloaded first.
            page.route('http://**/*', lambda route: route.abort())
            page.route('https://**/*', lambda route: route.abort())
            page.goto(source.as_uri(), wait_until="load")
            page.evaluate("async () => { await document.fonts.ready; if(window.pptkitReady) await window.pptkitReady; await Promise.all([...document.images].map(i => i.decode().catch(() => {}))); }")
            result = page.evaluate((HERE / "extract.js").read_text(encoding="utf-8"))
            if previews:
                previews = Path(previews)
                previews.mkdir(parents=True, exist_ok=True)
                paths=[]
                for i, locator in enumerate(page.locator("section.slide").all(), 1):
                    target=previews / f"slide-{i:02}.png"
                    locator.screenshot(path=str(target), animations="disabled")
                    paths.append(target)
                _contact_sheet(paths, previews / "contact-sheet.png")
            if result["errors"]:
                raise ValueError("\n".join(result["errors"]))
            return result
        finally:
            browser.close()


def _contact_sheet(paths, out):
    from PIL import Image, ImageOps, ImageDraw
    if not paths:
        return
    thumb_w, thumb_h, gap, label = 640, 360, 16, 24
    cols = min(2, len(paths))
    canvas = Image.new('RGB', (cols*(thumb_w+gap)+gap, math.ceil(len(paths)/cols)*(thumb_h+label+gap)+gap), '#d8dce3')
    draw = ImageDraw.Draw(canvas)
    for n, path in enumerate(paths):
        with Image.open(path) as im:
            thumb = ImageOps.contain(im.convert('RGB'), (thumb_w, thumb_h))
            x, y = gap+(n%cols)*(thumb_w+gap), gap+(n//cols)*(thumb_h+label+gap)
            canvas.paste(thumb, (x,y))
            draw.text((x,y+thumb_h+5), f"{n+1:02}", fill='#172033')
    canvas.save(out)


def _fill(fill, color):
    if color['alpha'] == 0:
        fill.background()
        return
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(color['hex'])
    if color['alpha'] < 1:
        alpha = OxmlElement('a:alpha')
        alpha.set('val', str(round(color['alpha']*100000)))
        fill.fore_color._xClr.append(alpha)


def _geometry(box):
    return [Inches(box[k]/96) for k in ('x','y','w','h')]


def _font(font, style):
    font.name = style['font']
    font.size = Pt(style['size']*0.75)
    font.bold, font.italic, font.underline = style['bold'], style['italic'], style['underline']
    font._rPr.set('spc',str(round(style.get('tracking',0)*75)))
    _fill(font.fill, style['color'])
    # Explicit East Asian font avoids a different theme font for Korean characters.
    east = OxmlElement('a:ea')
    east.set('typeface', style['font'])
    font._rPr.append(east)


def _text(slide, entry):
    shape = slide.shapes.add_textbox(*_geometry(entry['box']))
    shape.name = entry['name']
    tf = shape.text_frame
    tf.clear()
    tf.word_wrap, tf.auto_size = not entry['singleLine'], MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    top,right,bottom,left = entry['padding']
    tf.margin_top,tf.margin_right,tf.margin_bottom,tf.margin_left = [Inches(v/96) for v in (top,right,bottom,left)]
    p = tf.paragraphs[0]
    p.alignment = {'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT,'end':PP_ALIGN.RIGHT}.get(entry['style']['align'],PP_ALIGN.LEFT)
    p.line_spacing = Pt(entry['style']['lineHeight']*0.75)
    p.space_before = p.space_after = Pt(0)
    for record in entry['runs']:
        for index, text in enumerate(record['text'].split('\n')):
            if index:
                p.add_line_break()
            if text:
                r = p.add_run()
                r.text = text
                _font(r.font, record)
    return shape


def _shape(slide, entry):
    box = entry['box']
    kind = MSO_SHAPE.OVAL if entry['ellipse'] else MSO_SHAPE.ROUNDED_RECTANGLE if entry['radius'] else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(kind, *_geometry(box))
    shape.name = entry['name']
    shape.shadow.inherit = False
    _fill(shape.fill, entry['fill'])
    shape.line.fill.background()
    if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        shape.adjustments[0] = min(0.5, entry['radius']/min(box['w'],box['h']))
    sides = entry['sides']
    if all(s == sides[0] for s in sides) and sides[0]['width']:
        _fill(shape.line.fill, sides[0]['color'])
        shape.line.width = Pt(sides[0]['width']*0.75)
    else:
        x,y,w,h = (box[k]/96 for k in ('x','y','w','h'))
        for border,coords in zip(sides, [(x,y,x+w,y),(x+w,y,x+w,y+h),(x,y+h,x+w,y+h),(x,y,x,y+h)]):
            if border['width']:
                line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,*[Inches(n) for n in coords])
                line.shadow.inherit = False
                _fill(line.line.fill,border['color'])
                line.line.width = Pt(border['width']*0.75)


def _image(slide, entry):
    src = entry['src']
    if src.startswith('data:image/'):
        image = BytesIO(base64.b64decode(src.split(',',1)[1]))
    elif src.startswith('file:'):
        parsed = urlparse(src)
        if parsed.netloc not in ('','localhost'):
            raise ValueError('네트워크 이미지 경로 대신 로컬 이미지를 사용하세요.')
        image = str(Path(url2pathname(parsed.path)))
    else:
        raise ValueError('이미지는 로컬 파일 또는 base64 data URL이어야 합니다.')
    box = dict(entry['box'])
    if entry['fit'] == 'contain':
        iw,ih = entry['natural']
        scale = min(box['w']/iw,box['h']/ih)
        box['x'] += (box['w']-iw*scale)/2
        box['y'] += (box['h']-ih*scale)/2
        box['w'],box['h'] = iw*scale,ih*scale
    picture=slide.shapes.add_picture(image,*_geometry(box))
    picture.name = entry['name']
    if entry['fit']=='cover':
        iw,ih=entry['natural']
        ratio=(box['w']/box['h'])/(iw/ih)
        if ratio<1:
            picture.crop_left=picture.crop_right=(1-ratio)/2
        else:
            picture.crop_top=picture.crop_bottom=(1-1/ratio)/2


def _table(slide, entry):
    rows = entry['rows']
    if not rows or not rows[0] or any(len(r)!=len(rows[0]) for r in rows):
        raise ValueError('표는 같은 열 개수의 비어 있지 않은 행이어야 합니다.')
    table = slide.shapes.add_table(len(rows),len(rows[0]),*_geometry(entry['box'])).table
    for col,cell in zip(table.columns,rows[0]):
        col.width = Inches(cell['w']/96)
    for ri,row in enumerate(rows):
        table.rows[ri].height = Inches(max(c['h'] for c in row)/96)
        for ci,record in enumerate(row):
            cell = table.cell(ri,ci)
            cell.text = record['text']
            padding=record.get('padding',[8,12,8,12])
            cell.margin_top,cell.margin_right,cell.margin_bottom,cell.margin_left=[Inches(v/96) for v in padding]
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            _fill(cell.fill,record['fill'])
            for p in cell.text_frame.paragraphs:
                p.space_after = Pt(0)
                p.alignment={'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT,'end':PP_ALIGN.RIGHT}.get(record['style']['align'],PP_ALIGN.LEFT)
                for r in p.runs:
                    _font(r.font,record['style'])
            for side,index in [('L',3),('R',1),('T',0),('B',2)]:
                line=OxmlElement(f'a:ln{side}')
                border=record.get('borders',[{'width':0}]*4)[index]
                if border['width']:
                    line.set('w',str(round(border['width']*9525)))
                    fill=OxmlElement('a:solidFill')
                    color=OxmlElement('a:srgbClr'); color.set('val',border['color']['hex'])
                    fill.append(color); line.append(fill)
                else:
                    line.append(OxmlElement('a:noFill'))
                properties=cell._tc.get_or_add_tcPr()
                for previous in list(properties):
                    if previous.tag == line.tag: properties.remove(previous)
                properties.append(line)


def _chart(slide, entry):
    spec = entry['data']
    types = {'column':XL_CHART_TYPE.COLUMN_CLUSTERED,'bar':XL_CHART_TYPE.BAR_CLUSTERED,'line':XL_CHART_TYPE.LINE}
    if spec.get('type') not in types:
        raise ValueError('차트 type은 column, bar, line 중 하나여야 합니다.')
    cats,series = spec.get('categories'),spec.get('series')
    if not cats or not series or not spec.get('source'):
        raise ValueError('차트에는 categories, series, source가 필요합니다.')
    data = CategoryChartData()
    data.categories = cats
    for s in series:
        if len(s['values']) != len(cats) or any(isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) for n in s['values']):
            raise ValueError('차트 값은 category 수와 같은 유한한 숫자 배열이어야 합니다.')
        data.add_series(s['name'],s['values'])
    chart = slide.shapes.add_chart(types[spec['type']],*_geometry(entry['box']),data).chart
    chart.has_title = False
    # PowerPoint otherwise invents a title from the single series name on open.
    auto_title = chart._chartSpace.chart.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}autoTitleDeleted')
    if auto_title is None:
        auto_title = OxmlElement('c:autoTitleDeleted')
        chart._chartSpace.chart.insert(0, auto_title)
    auto_title.set('val', '1')
    chart.has_legend = len(series)>1
    chart.font.name = spec.get('font','Arial')
    chart.font.size = Pt(spec.get('fontSize',16)*0.75)
    label_color=RGBColor.from_string(spec.get('labelColor','64716B').lstrip('#'))
    chart.font.color.rgb=label_color
    for axis in [chart.category_axis,chart.value_axis]:
        axis.tick_labels.font.name=spec.get('font','Arial')
        axis.tick_labels.font.size=Pt(spec.get('fontSize',16)*0.75)
        axis.tick_labels.font.color.rgb=label_color
        axis.major_tick_mark=XL_TICK_MARK.NONE
        axis.minor_tick_mark=XL_TICK_MARK.NONE
        axis.format.line.fill.background()
    chart.category_axis.has_major_gridlines=False
    chart.value_axis.has_major_gridlines=True
    chart.value_axis.major_gridlines.format.line.color.rgb=RGBColor.from_string(spec.get('gridColor','E1E5E0').lstrip('#'))
    chart.value_axis.major_gridlines.format.line.width=Pt(0.5)
    chart.value_axis.tick_labels.number_format=spec.get('numberFormat','#,##0')
    if spec.get('maxValue') is not None: chart.value_axis.maximum_scale=spec['maxValue']
    if spec.get('majorUnit') is not None: chart.value_axis.major_unit=spec['majorUnit']
    if chart.has_legend:
        chart.legend.position=XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout=False
    for native,record in zip(chart.series,series):
        color = RGBColor.from_string(record.get('color','315EF5').lstrip('#'))
        native.format.fill.solid()
        native.format.fill.fore_color.rgb = color
        native.format.line.color.rgb = color
        if spec['type']=='line': native.format.line.width=Pt(2.5)
    chart.value_axis.minimum_scale = min(0,min(v for s in series for v in s['values']))
    chart.plots[0].has_data_labels = spec.get('showValues',True)
    if spec.get('showValues',True):
        chart.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END if spec['type']!='line' else XL_LABEL_POSITION.ABOVE
        chart.plots[0].data_labels.font.size=Pt(spec.get('fontSize',16)*0.75)
        chart.plots[0].data_labels.font.color.rgb=label_color


def _assemble(data, output):
    prs = Presentation()
    prs.slide_width,prs.slide_height = Inches(WIDTH/96),Inches(HEIGHT/96)
    expected_texts=[]
    for record in data['slides']:
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        _fill(slide.background.fill,record['background'])
        for entry in record['entries']:
            {'text':_text,'shape':_shape,'image':_image,'table':_table,'chart':_chart}[entry['kind']](slide,entry)
            if entry['kind']=='text': expected_texts.append(''.join(r['text'] for r in entry['runs']))
        slide.notes_slide.notes_text_frame.text = record['notes']
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    # Validate saved objects before replacing any existing result.
    with tempfile.TemporaryDirectory(dir=output.parent) as td:
        draft=Path(td)/'deck.pptx'
        prs.save(draft)
        saved=Presentation(draft)
        normal=lambda t:' '.join(t.split())
        texts=Counter(normal(s.text) for sl in saved.slides for s in sl.shapes if s.has_text_frame and s.text.strip())
        needed=Counter(normal(t) for t in expected_texts if normal(t))
        if needed-texts:
            raise RuntimeError('저장된 PPT에서 일부 편집형 텍스트를 찾지 못했습니다.')
        counts=Counter(e['kind'] for sl in data['slides'] for e in sl['entries'])
        report={'slides':len(saved.slides),'native_text':counts['text'],'native_shapes':counts['shape'],
                'native_tables':counts['table'],'native_charts':counts['chart'],'images':counts['image'],
                'text_preservation':'passed','visual_review':'pending'}
        draft.replace(output)
    output.with_suffix('.editable.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


_RENDER_PS = r'''
param([string]$inputFile,[string]$outputDir)
$ErrorActionPreference='Stop'
$app=New-Object -ComObject PowerPoint.Application
$deck=$null
try {
  $deck=$app.Presentations.Open($inputFile,-1,0,0)
  foreach ($slide in $deck.Slides) {
    $name='slide-{0:D2}.png' -f [int]$slide.SlideIndex
    $slide.Export((Join-Path $outputDir $name),'PNG',1280,720)
  }
} finally {
  if ($null -ne $deck) { $deck.Close() }
  if ($app.Presentations.Count -eq 0) { $app.Quit() }
}
'''


def render_pptx(source,out):
    source,out=Path(source).resolve(),Path(out).resolve()
    if not source.is_file(): raise FileNotFoundError(source)
    out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        if sys.platform=='win32':
            script=Path(td)/'render.ps1'
            script.write_text(_RENDER_PS,encoding='utf-8-sig')
            result=subprocess.run(['powershell','-NoProfile','-File',str(script),str(source),str(out)],capture_output=True,timeout=180)
            if result.returncode: raise RuntimeError('PowerPoint 렌더 실패: '+result.stderr.decode(errors='replace')[-500:])
        else:
            soffice=shutil.which('soffice')
            if not soffice: raise RuntimeError('PPT 시각 검수에는 Windows PowerPoint 또는 LibreOffice가 필요합니다. 시각 검수 미완료로 보고하세요.')
            result=subprocess.run([soffice,f'-env:UserInstallation={Path(td).as_uri()}/profile','--headless','--convert-to','pdf','--outdir',td,str(source)],capture_output=True,timeout=180)
            pdf=Path(td)/f'{source.stem}.pdf'
            if result.returncode or not pdf.exists(): raise RuntimeError('LibreOffice PDF 변환에 실패했습니다.')
            import pymupdf
            with pymupdf.open(pdf) as doc:
                for i,page in enumerate(doc,1):
                    page.get_pixmap(matrix=pymupdf.Matrix(WIDTH/page.rect.width,HEIGHT/page.rect.height)).save(out/f'slide-{i:02}.png')
    count=len(Presentation(source).slides)
    _contact_sheet([out/f'slide-{i:02}.png' for i in range(1,count+1)],out/'contact-sheet.png')
    return f'PPT 렌더 완료 → {out}\n이미지를 열어 HTML과 비교하세요. 렌더 성공은 디자인 검수 통과를 의미하지 않습니다.'


def run(args):
    action=args.html_action
    if action=='designs':
        return ('editorial  편집 디자인: 사진·비대칭 구도·큰 문장\n'
                'product    제품 발표: 브랜드 비주얼·사용 화면·행동\n'
                'strategy   전략 보고: 지표·차트·표·의사결정\n'
                '시작: pptkit html init deck.html --design <name>')
    if action=='setup':
        _playwright()
        subprocess.run([sys.executable,'-m','playwright','install','chromium'],check=True)
        return 'Chromium 설치 완료'
    if action=='init':
        out=Path(args.out)
        assets=out.with_name(out.stem+'.assets')
        if out.exists() or assets.exists(): raise ValueError(f'{out} 또는 {assets}이 이미 있습니다. 다른 파일명을 사용하세요.')
        design=getattr(args,'design','editorial')
        source=HERE/'system'/'examples'/f'{design}.html'
        if not source.is_file(): raise ValueError(f'지원하지 않는 디자인: {design}')
        out.parent.mkdir(parents=True,exist_ok=True)
        shutil.copytree(HERE/'system',assets,ignore=shutil.ignore_patterns('examples'))
        from html import escape
        from urllib.parse import quote
        prefix=escape(quote(assets.name)+'/')
        out.write_text(source.read_text(encoding='utf-8').replace('../',prefix),encoding='utf-8')
        return (f'Studio {design} 시작 파일 → {out}\n토큰·서체·에셋 → {assets}\n'
                f'편집형 안내지·검토지·조건표 예제 → {assets / "components" / "working-artifacts.html"}\n'
                '견본의 문구·이미지·가상 데이터를 실제 자료에 맞게 바꾸세요. PPT PC에는 Pretendard 설치가 필요합니다.')
    source=Path(args.input)
    if action=='render':
        return render_pptx(source,args.out or source.with_suffix('.ppt-preview'))
    if action=='preview':
        out=Path(args.out or source.with_suffix('.html-preview'))
        data=_measure(source,out)
        return f'HTML 구조 검사 통과: {len(data["slides"])}장 → {out}\ncontact-sheet.png와 개별 장표를 열어 디자인을 검수하세요.'
    out=Path(args.out or source.with_suffix('.pptx'))
    data=_measure(source)
    report=_assemble(data,out)
    return (f'HTML → PPT 변환 완료: {report["slides"]}장, 텍스트 {report["native_text"]}, '
            f'도형 {report["native_shapes"]}, 표 {report["native_tables"]}, 차트 {report["native_charts"]}, '
            f'이미지 {report["images"]} → {out}\n편집형 텍스트 보존 검사 통과. PPT 시각 검수는 별도로 필요합니다.')
