"""Browser-to-PPT tests for observable editability and fail-closed export behavior."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from pptkit import html_deck


@pytest.fixture(scope='module', autouse=True)
def browser_available():
    pw = pytest.importorskip('playwright.sync_api')
    with pw.sync_playwright() as p:
        try:
            b=p.chromium.launch()
        except Exception as exc:
            pytest.skip(f'Chromium missing; run pptkit html setup: {exc}')
        b.close()


def html(tmp_path,body):
    source=tmp_path/'한글 디자인.html'
    source.write_text('''<!doctype html><meta charset="utf-8"><style>
    *{box-sizing:border-box} body{margin:0;font-family:"Malgun Gothic"}
    .slide{width:1280px;height:720px;position:relative;background:#fff}
    p{margin:0;font-size:28px;line-height:1.3}
    </style><section class="slide">'''+body+'</section>',encoding='utf-8')
    return source


def test_starter_roundtrip_preserves_editability(tmp_path):
    data=html_deck._measure(html_deck.HERE/'starter.html')
    out=tmp_path/'starter.pptx'
    report=html_deck._assemble(data,out)
    assert report=={'slides':4,'native_text':35,'native_shapes':13,'native_tables':1,
                   'native_charts':0,'images':0,'text_preservation':'passed','visual_review':'pending'}
    prs=Presentation(out)
    assert all(s.shape_type != MSO_SHAPE_TYPE.PICTURE for sl in prs.slides for s in sl.shapes)
    text=next(s for s in prs.slides[0].shapes if s.has_text_frame and '생각은' in s.text)
    text.text='수정 가능한 한국어 제목'
    table=next(s.table for s in prs.slides[2].shapes if s.has_table)
    table.cell(1,1).text='편집한 셀'
    prs.save(out)
    reread=Presentation(out)
    assert any(s.has_text_frame and s.text=='수정 가능한 한국어 제목' for s in reread.slides[0].shapes)
    assert next(s.table for s in reread.slides[2].shapes if s.has_table).cell(1,1).text=='편집한 셀'


def test_native_chart_data_and_local_image(tmp_path):
    Image.new('RGB',(80,40),'#315ef5').save(tmp_path/'이미지 100%.png')
    source=html(tmp_path,'''<p data-pptx="text">가상 데이터 검증</p>
    <img data-pptx="image" src="이미지 100%.png" style="width:80px;height:40px">
    <div data-pptx="chart" data-source="data" style="position:absolute;left:100px;top:100px;width:800px;height:400px"></div>
    <script type="application/json" id="data">{"type":"column","categories":["가","나"],
    "series":[{"name":"test","values":[12,-34]}],"source":"가상 테스트 데이터"}</script>''')
    out=tmp_path/'data.pptx'
    html_deck._assemble(html_deck._measure(source),out)
    prs=Presentation(out)
    chart=next(s.chart for s in prs.slides[0].shapes if s.has_chart)
    assert list(chart.series[0].values)==[12,-34]
    assert chart.value_axis.minimum_scale <= -34
    assert chart.part.chart_workbook.xlsx_part.blob
    assert chart._chartSpace.chart.find('{http://schemas.openxmlformats.org/drawingml/2006/chart}autoTitleDeleted').get('val') == '1'
    assert sum(s.shape_type==MSO_SHAPE_TYPE.PICTURE for s in prs.slides[0].shapes)==1


def test_letter_spacing_and_cover_keep_editable_objects(tmp_path):
    Image.new('RGB',(200,100),'#e64d2d').save(tmp_path/'wide.png')
    source=html(tmp_path,'''<p data-pptx="text" style="letter-spacing:-1.5px">편집형 자간</p>
    <img data-pptx="image" src="wide.png" style="position:absolute;left:100px;top:100px;width:100px;height:100px;object-fit:cover">''')
    out=tmp_path/'crop.pptx'
    html_deck._assemble(html_deck._measure(source),out)
    slide=Presentation(out).slides[0]
    title=next(s for s in slide.shapes if s.has_text_frame)
    assert title.text=='편집형 자간'
    assert title.text_frame.paragraphs[0].runs[0].font._rPr.get('spc') == '-112'
    picture=next(s for s in slide.shapes if s.shape_type==MSO_SHAPE_TYPE.PICTURE)
    assert picture.crop_left == pytest.approx(.25)
    assert picture.crop_right == pytest.approx(.25)
    # Retain the uncropped source so a recipient can adjust the framing in PPT.
    assert picture.image.size == (200,100)


@pytest.mark.parametrize('design',['editorial','product','strategy'])
def test_portable_studio_init_can_export_without_source_tree(tmp_path,design):
    source=tmp_path/'한글 경로 100%'/(design+' 견본.html')
    args=SimpleNamespace(html_action='init',out=source,design=design)
    html_deck.run(args)
    assets=source.with_name(source.stem+'.assets')
    assert (assets/'layouts.json').is_file()
    assert (assets/'fonts'/'OFL-Pretendard.txt').is_file()
    assert (assets/'LICENSE-ChartJS.md').is_file()
    data=html_deck._measure(source)
    out=source.with_suffix('.pptx')
    report=html_deck._assemble(data,out)
    prs=Presentation(out)
    assert len(prs.slides)==6
    assert all(any(s.has_text_frame and s.text for s in sl.shapes) for sl in prs.slides)
    assert any(s.has_chart for sl in prs.slides for s in sl.shapes)
    assert report['text_preservation']=='passed'
    assert report['images'] < report['slides']
    before=source.read_bytes()
    with pytest.raises(ValueError,match='이미 있습니다'):
        html_deck.run(args)
    assert source.read_bytes()==before


def test_portable_working_artifacts_are_native_and_editable(tmp_path):
    source=tmp_path/'새 주제 100%'/'deck.html'
    html_deck.run(SimpleNamespace(html_action='init',out=source,design='product'))
    companion=source.with_name('deck.assets')/'components'/'working-artifacts.html'
    data=html_deck._measure(companion)
    out=tmp_path/'forms.pptx'
    report=html_deck._assemble(data,out)
    assert report['slides']==3
    assert report['images']==0
    assert report['text_preservation']=='passed'
    prs=Presentation(out)
    guide=next(s for s in prs.slides[0].shapes if s.has_text_frame and '오늘 고친 부분' in s.text)
    guide.text='오늘 관찰한 변화'
    table=next(s.table for s in prs.slides[2].shapes if s.has_table)
    table.cell(1,1).text='실제 모집 기준으로 수정'
    prs.save(out)
    reread=Presentation(out)
    assert any(s.has_text_frame and s.text=='오늘 관찰한 변화' for s in reread.slides[0].shapes)
    assert next(s.table for s in reread.slides[2].shapes if s.has_table).cell(1,1).text=='실제 모집 기준으로 수정'
    assert all(s.shape_type!=MSO_SHAPE_TYPE.PICTURE for sl in reread.slides for s in sl.shapes)


@pytest.mark.parametrize('body,match',[
    ('<p>누락되면 안 되는 내용</p>','표시가 없는 텍스트'),
    ('<img src="missing.png" style="width:100px;height:100px">','이미지에 data-pptx'),
    ('<div data-pptx="shape" style="width:100px;height:100px;background:linear-gradient(red,blue)"></div>','backgroundImage'),
    ('<p data-pptx="text" style="position:absolute;left:1300px">영역 밖</p>','영역을 벗어'),
    ('<div style="width:100px;height:100px;background:red"></div>','배경·테두리'),
    ('<p data-pptx="text" style="width:20px;height:20px">긴 한국어 텍스트 넘침</p>','내용이 요소 크기'),
])
def test_unsupported_or_lost_content_fails(tmp_path,body,match):
    with pytest.raises(ValueError,match=match):
        html_deck._measure(html(tmp_path,body))


def test_rebuild_reads_current_html_and_failure_preserves_output(tmp_path):
    source=html(tmp_path,'<p data-pptx="text">첫 버전</p>')
    out=tmp_path/'deck.pptx'
    html_deck._assemble(html_deck._measure(source),out)
    source.write_text(source.read_text(encoding='utf-8').replace('첫 버전','두 번째 버전'),encoding='utf-8')
    data=html_deck._measure(source)
    html_deck._assemble(data,out)
    assert any(s.has_text_frame and s.text=='두 번째 버전' for s in Presentation(out).slides[0].shapes)
    original=out.read_bytes()
    data['slides'][0]['entries'].append({'kind':'chart','data':{'type':'unsupported'}})
    with pytest.raises(ValueError): html_deck._assemble(data,out)
    assert out.read_bytes()==original
    assert json.loads(out.with_suffix('.editable.json').read_text(encoding='utf-8'))['visual_review']=='pending'
