"""Author the shipped HTML specimens. All PPT output goes through pptkit html.

Numbers are copied from pptkit pivot output for the repository's fictional eval
fixtures; this script only lays out HTML and never calculates business metrics.
"""
import json
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parents[1]
SYSTEM=ROOT/'pptkit/html_runtime/system'


def compile_tokens():
    data=json.loads((SYSTEM/'tokens.json').read_text(encoding='utf-8'))
    def val(v): return 'var(--'+v[1:-1]+')' if v.startswith('{') else v
    def block(selector,items): return selector+'{\n'+''.join(f'  --{k}:{val(v)};\n' for k,v in items.items())+'}\n'
    css='/* Generated from tokens.json. Edit that source, then run scripts/build_system_specimens.py. */\n'
    css+=block(':root',data['primitive']|data['semantic']|data['component'])
    for mode,overrides in data['modes'].items():
        css+=block('.'+mode,data['semantic']|overrides|data['component'])
    (SYSTEM/'tokens.css').write_text(css,encoding='utf-8')


def t(text,x,y,w,cls='body',style='',tag='p'):
    return f'<{tag} data-pptx="text" class="{cls}" style="left:{x}px;top:{y}px;width:{w}px;{style}">{text}</{tag}>'


def r(x,y,w,h=1,color='var(--line)',extra=''):
    return f'<div data-pptx="shape" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{color};{extra}"></div>'


def img(name,x,y,w,h):
    return f'<img data-pptx="image" src="../assets/{name}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" alt="디자인 견본용 생성 비주얼">'


def folio(label,n,source='PPTKIT STUDIO / 디자인 시스템 견본'):
    return t(label,64,38,900,'label')+t(source,64,675,1080,'caption muted')+t(f'{n:02}',1168,674,48,'caption muted','text-align:right')


def chart(key,x,y,w,h,categories,values,kind='line',color='#164F46',maxvalue=None,unit=None):
    data={'type':kind,'categories':categories,'series':[{'name':'검증 데이터','values':values,'color':color}],
          'source':'저장소 evals/data 가상 검증 데이터','font':'Pretendard','fontSize':16,'labelColor':'#61716B',
          'gridColor':'#DBE3DD','showValues':False}
    if maxvalue is not None:data['maxValue']=maxvalue
    if unit is not None:data['majorUnit']=unit
    return f'<div data-pptx="chart" data-source="{key}" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div><script type="application/json" id="{key}">{json.dumps(data,ensure_ascii=False)}</script>'


def table(x,y,w,widths,rows,height=None,highlight=None):
    cols=''.join(f'<col style="width:{v}%">' for v in widths)
    body=''
    for i,row in enumerate(rows):
        tag='th' if i==0 else 'td'
        cells=''.join(f'<{tag}>{v}</{tag}>' for v in row)
        body+=f'<tr class="{"highlight" if i==highlight else ""}">{cells}</tr>'
    return f'<table data-pptx="table" style="left:{x}px;top:{y}px;width:{w}px;'+(f'height:{height}px;' if height else '')+f'"><colgroup>{cols}</colgroup>{body}</table>'


def slide(mode,content,notes='',extra=''):
    return f'<section class="slide {mode} {extra}">{content}<aside data-notes>{escape(notes)}</aside></section>'


def document(mode,slides):
    return f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PPTKIT Studio · {mode}</title><link rel="stylesheet" href="../tokens.css"><link rel="stylesheet" href="../system.css"></head>
<body>{''.join(slides)}<script src="../chart.umd.js"></script><script src="../charts.js"></script></body></html>'''


def editorial():
    slides=[]
    c=img('editorial-architecture.png',704,0,576,720)
    c+=t('FIELDNOTES',64,42,560,'label')+t('WORK / CULTURE / PERSPECTIVE',64,78,560,'caption muted')
    c+=t('일의 구조를<br>다시 읽다.',58,198,630,'cover',tag='h1')
    c+=r(64,440,70,5,'var(--accent)')
    c+=t('명확한 관점이 만드는<br>더 나은 팀의 움직임.',64,482,560,'body muted')
    c+=t('EDITORIAL SERIES — 01',64,655,560,'label')
    c+=t('생성 이미지 / 설명용',1000,682,240,'caption white','text-align:right')
    slides.append(slide('editorial',c,'편집형의 표지. 사진의 크기와 타이포그래피를 대등하게 두고 여백을 명확히 확보한다.'))
    c=folio('01 / POINT OF VIEW',2)
    c+=t('좋은 결정은<br>명확한 관점에서<br>시작됩니다.',60,164,720,'cover',tag='h2')
    c+=r(822,166,2,420)+t('IN FOCUS',872,172,330,'label accent')
    c+=t('무엇이 중요한가',872,234,340,'subhead')
    c+=t('모든 정보를 같은 크기로<br>설명하면 핵심은 흐려집니다.<br>이 장에서 남길 생각부터<br>정리합니다.',872,300,340,'body muted')
    c+=t('관점 → 근거 → 다음 행동',872,537,340,'detail')
    slides.append(slide('editorial',c,'비대칭 읽기 구도. 왼쪽은 주장, 오른쪽은 해석이다. 실제 보고의 내용에 맞게 바꾼다.'))
    c=folio('02 / EVIDENCE',3,'자료: evals/data/startup_traction.csv · 디자인 검증용 가상 데이터')
    c+=t('반복되는 기록에서<br>성장의 방향이 보입니다.',64,130,1020,'title',tag='h2')
    c+=t('10.17×',58,330,380,'metric accent')
    c+=t('첫 관측 월 대비 MRR',64,470,340,'detail')
    c+=t('2025.10 — 2026.09',64,518,340,'label muted')
    c+=t('월 반복매출 / 만 원',476,287,700,'label muted')
    c+=chart('editorial-mrr',460,336,754,274,['10월','11월','12월','1월','2월','3월','4월','5월','6월','7월','8월','9월'],[290,380,520,690,880,1110,1350,1620,1890,2210,2560,2950],color='#E64D2D',maxvalue=3200,unit=1000)
    slides.append(slide('editorial',c,'숫자와 해석을 분리한다. 10.17배는 pptkit pivot의 first→last 값이며 가상 검증 데이터다.'))
    c=img('editorial-architecture.png',0,0,640,720)
    c+=t('03 / A DIFFERENT ANGLE',704,42,512,'label')
    c+=t('정보를 더하기 전,<br>읽는 방향을<br>설계합니다.',700,200,520,'title',tag='h2')
    c+=r(704,437,60,5,'var(--accent)')
    c+=t('이미지는 분위기를 정하고,<br>문장은 생각을 붙잡습니다.<br>두 요소에 같은 역할을 맡기지 않습니다.',704,480,510,'body muted')
    c+=t('이미지: 생성 비주얼 · 실제 장소 아님',32,682,560,'caption white')
    c+=t('PPTKIT STUDIO',704,675,440,'caption muted')+t('04',1168,674,48,'caption muted','text-align:right')
    slides.append(slide('editorial',c,'사진을 화면의 절반까지 확장하는 챕터 장표. 사진 위의 본문은 최소화한다.'))
    c=folio('04 / COMPOSITION',5)
    c+=t('같은 내용도,<br>다른 구도가 필요합니다.',64,126,1120,'title',tag='h2')
    c+=table(64,310,1152,[22,39,39],[['전달할 관계','대표 구도','가장 크게 보여줄 것'],['주장과 해석','큰 문장 + 짧은 논평','핵심 주장'],['변화와 추세','지표 + 넓은 차트','변화의 방향'],['맥락과 사례','큰 사진 + 캡션','상황을 설명하는 장면'],['다음 행동','짧은 결론 + 하나의 요청','결정해야 할 일']],height=282)
    slides.append(slide('editorial',c,'읽기 관계에 따른 편집형 구도 선택표. 표 자체는 PowerPoint 네이티브 표다.'))
    c=t('FIELDNOTES / ENDNOTE',64,42,1100,'label')
    c+=t('생각을 정리하고,<br>한 장면을 남기다.',58,220,1160,'cover',tag='h2')
    c+=r(64,518,1152,1,'var(--line)')
    c+=t('다음 장에서는 어떤 생각을 남기고 싶나요?',64,558,1120,'body')
    c+=t('EDITORIAL / PPTKIT STUDIO',64,675,1050,'caption')+t('06',1168,675,48,'caption','text-align:right')
    slides.append(slide('editorial',c,'핵심 문장만 남기는 마무리. 본문을 반복하지 않는다.',extra='bright'))
    return slides


def product():
    slides=[]
    c=img('product-loop.png',592,90,688,548)
    c+=t('CARENOTE',64,42,560,'label')+t('PRODUCT STORY / 2026',848,42,368,'label muted','text-align:right')
    c+=t('기록은 짧게,<br>돌봄은 깊게.',58,216,720,'cover',tag='h1')
    c+=t('돌봄 현장의 목소리를<br>팀이 함께 쓰는 기록으로.',64,468,600,'body muted')
    c+=r(64,589,216,3,'var(--accent)')+t('말하고 · 확인하고 · 공유하다',64,610,800,'label')
    c+=t('케어노트: 저장소의 가상 서비스 사례 · 이미지: 생성 브랜드 비주얼',64,680,1120,'caption muted')
    slides.append(slide('product',c,'제품형 표지. 생성 비주얼은 연결을 상징하며 실제 제품 사진이 아니다.'))
    c=folio('01 / THE PRODUCT',2,'기능 설명용 가상 UI 목업 · 실제 서비스 화면 아님')
    c+=t('말로 남긴 돌봄을<br>팀의 기록으로.',64,177,560,'title',tag='h2')
    c+=t('현장에서 남긴 내용을<br>확인 가능한 초안으로 정리하고,<br>필요한 사람에게 전달합니다.',64,350,490,'body muted')
    c+=r(64,540,42,3,'var(--accent)')+t('입력의 부담은 줄이고,<br>검토의 책임은 분명하게.',64,565,510,'detail')
    c+=r(610,155,606,455,color='var(--color-white)',extra='border:1px solid var(--line);')
    c+=r(610,155,606,58,color='var(--color-ink)')
    c+=t('carenote',638,171,270,'label white')+t('돌봄 기록',1040,172,145,'caption white','text-align:right')
    c+=t('오늘의 기록',642,242,510,'subhead')
    c+=r(642,309,542,79,color='var(--color-paper)')
    c+=t('음성 메모에서 초안을 만들었어요',662,327,500,'detail')
    for i,(a,b) in enumerate([('식사 및 활동','내용 확인'),('복약 관련 메모','담당자 검토'),('보호자 공유','공유 전 확인')]):
        yy=417+i*54
        c+=t(a,642,yy,280,'detail')+t(b,1000,yy+2,170,'label accent','text-align:right')
        if i<2:c+=r(642,yy+39,542)
    slides.append(slide('product',c,'제품 화면과 주장을 나란히 둔다. 화면의 모든 문자와 기본 도형도 native PPT 요소다.',extra='paper'))
    c=folio('02 / HOW IT WORKS',3)
    c+=t('작은 입력에서,<br>팀의 다음 행동까지.',64,126,1120,'title',tag='h2')
    steps=[('01','말로 남기기','현장의 내용을 편한 말로 남깁니다.'),('02','초안 확인하기','누락과 사실관계를 직접 검토합니다.'),('03','기록 공유하기','검토한 내용을 필요한 곳에 전달합니다.')]
    for i,(n,title,desc) in enumerate(steps):
        x=64+392*i
        c+=t(n,x,313,360,'metric accent')+r(x,455,344,2,'var(--line)')
        c+=t(title,x,487,360,'subhead')+t(desc,x,552,344,'detail muted')
    slides.append(slide('product',c,'사용 순서를 숫자와 구분선으로 연결한다. 기능명 나열보다 실제 행동을 먼저 보여준다.'))
    c=folio('03 / TRACTION',4,'자료: evals/data/startup_traction.csv · 디자인 검증용 가상 데이터')
    c+=t('현장의 사용이<br>성장으로 이어집니다.',64,126,1110,'title',tag='h2')
    c+=t('월 반복매출 / 만 원',64,289,720,'label muted')
    c+=chart('product-mrr',48,334,760,287,['4월','5월','6월','7월','8월','9월'],[1350,1620,1890,2210,2560,2950],kind='column',color='#E64D2D',maxvalue=3200,unit=1000)
    c+=r(860,306,2,310)+t('86',904,316,312,'jumbo accent')+t('유료 이용 기관',914,510,300,'subhead')+t('2026년 9월 기준',914,570,300,'label muted')
    slides.append(slide('product',c,'월별 매출과 현재 유료 기관 수를 별도로 보여준다. 전체 수치는 검증용 가상 데이터다.',extra='paper'))
    c=folio('04 / PRICING',5,'자료: evals/data/startup_memo.md · 디자인 검증용 가상 요금제')
    c+=t('팀의 규모에 맞게.',64,132,1100,'title',tag='h2')
    for i,(name,size,price) in enumerate([('ESSENTIAL','30인 이하 기관','29'),('SCALE','31인 이상 기관','59')]):
        x=64+588*i
        c+=t(name,x,278,540,'label accent')+r(x,322,540,1)
        c+=t(price,x-4,355,236,'metric')+t('만 원 / 월',x+244,425,290,'detail muted')
        c+=t(size,x,513,540,'subhead')+t('음성 기록 · 누락 확인 · 보호자 요약',x,575,540,'detail muted')
    slides.append(slide('product',c,'비교 가능한 요금 구성. 둥근 가격 카드 대신 정렬과 선으로 비교 기준을 유지한다.'))
    c=t('CARENOTE / NEXT STEP',64,42,1120,'label')
    c+=t('돌봄에 더 가까운<br>기록의 시작.',58,214,1160,'cover',tag='h2')
    c+=t('우리 기관의 기록 흐름으로 데모를 확인해 보세요.',64,486,1140,'body')
    c+=r(64,587,286,58,color='var(--color-ink)')+t('데모 상담 시작하기 →',88,602,250,'detail white')
    c+=t('PRODUCT / PPTKIT STUDIO · 가상 서비스 견본',64,680,1100,'caption')
    slides.append(slide('product',c,'제품형 결론에서는 다음 행동 하나를 선명하게 남긴다.',extra='bright'))
    return slides


def strategy():
    slides=[]
    c=folio('QUARTERLY REVIEW / 2026 Q3',1,'PPTKIT STUDIO · 전략 보고형 · 디자인 검증용 가상 데이터')
    c+=r(64,104,1152,2,'var(--ink)')
    c+=t('사용자 성장과<br>수익화 지표를<br>함께 봅니다.',60,172,780,'cover',tag='h1')
    c+=t('2026',958,173,260,'label accent','text-align:right')+t('Q3',936,210,280,'jumbo accent','text-align:right')
    c+=r(876,430,340)+t('검토 범위',876,459,340,'label muted')
    c+=t('사용자 기반 · 유료 전환<br>이탈 · 사용자당 매출',876,504,340,'detail')
    c+=r(64,605,1152,32,'var(--accent)')
    slides.append(slide('strategy',c,'전략형 표지. 기간과 검토 범위를 명확히 하고 주제의 핵심을 제목에 둔다.'))
    c=folio('01 / EXECUTIVE SUMMARY',2,'자료: evals/data/kpi_quarterly.csv · 2026 Q3 · 디자인 검증용 가상 데이터')
    c+=t('성장·전환·유지를 같은 화면에서 봅니다',64,121,1152,'title',tag='h2')
    metrics=[('637','천 명','월간 활성 사용자'),('4.2','%','유료 전환율'),('4.4','%','이탈률')]
    for i,(value,unit,label) in enumerate(metrics):
        x=64+i*392
        c+=t(label,x,230,360,'label muted')+t(value,x-4,268,270,'metric accent')+t(unit,x+280,345,80,'detail')
        c+=r(x,422,344)
    rows=[('사용자 기반','첫 관측 분기 대비 1.43배로 확대되었습니다.'),('전환 경로','현재 전환율을 기준으로 단계별 이탈을 점검합니다.'),('유지와 수익','이탈률과 ARPU를 함께 보며 후속 실험을 정합니다.')]
    for i,(title,desc) in enumerate(rows):
        y=461+i*55
        c+=t(f'0{i+1}',64,y,60,'label accent')+t(title,144,y-2,210,'detail')+t(desc,362,y-2,840,'detail muted')
    slides.append(slide('strategy',c,'단위가 다른 지표를 동일한 축의 차트에 섞지 않는다. 숫자와 해석을 분리한다.'))
    c=folio('02 / USER BASE',3,'자료: evals/data/kpi_quarterly.csv · 월간 활성 사용자 / 천 명 · 가상 검증 데이터')
    c+=t('사용자 기반은 첫 관측 분기 대비 1.43배',64,121,1152,'title',tag='h2')
    c+=chart('strategy-mau',48,235,828,378,['25 Q1','25 Q2','25 Q3','25 Q4','26 Q1','26 Q2','26 Q3'],[446,464,499,527,568,609,637],color='#164F46',maxvalue=700,unit=200)
    c+=r(926,240,2,354)+t('637',966,256,250,'metric accent')+t('천 명 / 2026 Q3',976,398,240,'label muted')
    c+=t('규모의 확대와 함께<br>전환·유지 지표를<br>같이 확인합니다.',976,473,240,'detail')
    slides.append(slide('strategy',c,'추세 차트는 네이티브 데이터 차트이며 가로축 기간과 세로축 단위를 명시한다.'))
    c=folio('03 / PERFORMANCE REVIEW',4,'자료: evals/data/kpi_quarterly.csv · 2026 Q3 · 디자인 검증용 가상 데이터')
    c+=t('숫자를 다음 검증 질문으로 연결합니다',64,121,1152,'title',tag='h2')
    c+=table(64,248,1152,[23,17,35,25],[['핵심 지표','현재값','확인할 질문','다음 검증'],['월간 활성 사용자','637천 명','유입과 재방문의 기여는?','유입 경로별 분석'],['유료 전환율','4.2%','어느 단계에서 멈추는가?','전환 경로 점검'],['이탈률','4.4%','어떤 이용자가 떠나는가?','이탈 코호트 확인'],['사용자당 매출','42,932원','요금제별 차이는 무엇인가?','가격·사용 패턴 비교']],height=326,highlight=2)
    c+=t('해석 원칙',64,607,160,'label accent')+t('관측값과 원인을 구분하고, 확인되지 않은 원인은 질문으로 남깁니다.',228,604,980,'detail muted')
    slides.append(slide('strategy',c,'강조 행은 의사결정에 필요한 항목 하나에만 사용한다. 질문은 제안이며 원인이 확인되었다는 주장이 아니다.'))
    c=folio('04 / WORKPLAN',5,'아래는 지표 검토를 바탕으로 한 실행 계획 예시이며, 확정 일정이 아닙니다.')
    c+=t('진단에서 실험으로, 실험에서 검증으로',64,121,1152,'title',tag='h2')
    for i,title in enumerate(['진단','실험','검증']):
        x=358+i*286
        c+=r(x,245,262,55,'var(--accent)' if i==1 else 'var(--panel)')
        c+=t(title,x+20,258,220,'detail white' if i==1 else 'detail')
    labels=['전환 경로','이탈 원인','수익 구조']
    entries=[['단계별 이탈 위치','요금 안내 비교','전환 변화 확인'],['이탈 코호트 분류','유지 메시지 실험','재방문 변화 확인'],['요금제별 이용 분석','가치 설명 보강','ARPU 변화 확인']]
    for ri,label in enumerate(labels):
        y=333+ri*91
        c+=t(label,64,y+17,250,'subhead')+r(64,y+75,1152)
        for ci,text in enumerate(entries[ri]):
            x=358+ci*286
            c+=t(text,x+18,y+22,244,'detail muted')
    slides.append(slide('strategy',c,'프로젝트 계획 예시. 단계별 산출물을 같은 정렬선에 놓고 담당자나 날짜를 임의로 확정하지 않는다.'))
    c=folio('05 / DECISION',6,'STRATEGY / PPTKIT STUDIO · 디자인 시스템 견본')
    c+=t('다음 분기에는<br>전환 경로의 검증을<br>제안합니다.',60,160,840,'cover',tag='h2')
    c+=r(932,168,2,403,'var(--line)')
    c+=t('DECISION NOTES',980,177,236,'label accent')
    c+=t('확인할 것',980,259,236,'subhead')+t('실험 범위와 성공 기준',980,318,236,'detail muted')
    c+=t('정할 것',980,405,236,'subhead')+t('책임자와 검토 주기',980,464,236,'detail muted')
    slides.append(slide('strategy',c,'전략형 결론. 요청할 결정을 크게 남기고 의사결정 조건을 옆에 둔다.'))
    return slides


def working_artifacts():
    """Reusable native objects, with proposed forms visibly distinguished from facts."""
    slides=[]
    c=folio('SERVICE / USEFUL OBJECTS',1,'제안 양식 · 생활 수선 프로그램 예제 / 실제 운영 자료가 아닙니다')
    c+=t('고쳐 쓰는<br>첫 주말.',60,168,540,'',
         'font-size:78px;font-weight:700;line-height:1.18;letter-spacing:-2.5px',tag='h1')
    c+=t('안내지를 따라 시작하고,<br>기록지에 다음 시도를 남깁니다.',64,400,510,'body muted')
    c+=r(64,548,74,4,'var(--accent)')+t('받는 것에서 시작하는 서비스 소개',64,577,520,'detail')
    # Place the rear sheet's text outside the foreground sheet's footprint.
    c+=r(640,122,318,410,'#F4F7F7')+r(640,122,318,12,'#C9F46A')
    c+=t('01 / 처음 받는 안내',664,158,264,'label','color:#14212D')
    c+=t('첫 수선<br>안내지',664,211,264,'',
         'font-size:42px;font-weight:700;line-height:1.2;color:#14212D')
    c+=r(664,332,264,1,'#C5CFD1')
    for y,number,copy in [(356,'1','고칠 부분 살피기'),(412,'2','도구 사용법 익히기'),(468,'3','강사와 함께 시도하기')]:
        c+=t(number,664,y,28,'label','color:#53696F')
        c+=t(copy,702,y-3,224,'detail','color:#14212D')
    c+=r(940,290,276,328,'#C9F46A')
    c+=t('02 / 사용하며 쓰는 기록',964,322,228,'label','color:#14212D')
    c+=t('나의 수선 기록',964,373,228,'',
         'font-size:28px;font-weight:700;line-height:1.3;color:#14212D')
    for y,label in [(434,'오늘 고친 부분'),(513,'다음에 해 볼 것')]:
        c+=t(label,964,y,228,'detail','color:#14212D')+r(964,y+43,228,1,'#779B4A')
    slides.append(slide('product service',c,'앱 화면이 없는 대면 서비스. 안내지와 기록지를 편집 가능한 도형·글자로 제안한다. 문구는 운영자가 실제 과정에 맞게 수정한다.'))

    c=folio('LEARNING / WORKSHEET',2,'제안 양식 + 가상 작성 예시 · 실제 회의 기록이 아닙니다')
    c+=t('원문 옆에서<br>사실을<br>확인합니다.',60,152,476,'',
         'font-size:62px;font-weight:700;line-height:1.22;letter-spacing:-2px',tag='h2')
    c+=t('검토 기준을 설명하는 대신<br>한 문장을 직접 고쳐 봅니다.',64,426,450,'body muted')
    c+=r(64,563,72,4,'var(--accent)')+t('회의 메모 정리 / 실습 장면',64,591,430,'label')
    c+=r(564,124,652,498,'#FFFFFF')
    c+=t('사실 확인 워크시트',596,154,530,'subhead')
    c+=t('원문 → 요약 → 검토 → 수정',596,208,580,'detail muted')
    c+=r(596,252,588,2,'#D8492C')
    c+=t('원문',596,278,92,'label accent')
    c+=t('“일정은 금요일에 다시 논의합시다.”',712,273,470,'detail')
    c+=t('AI 요약',596,334,104,'label accent')
    c+=t('“금요일 출시를 확정했다.”',712,329,470,'detail')
    c+=r(596,386,588,1,'#DDD8CD')
    c+=t('무엇을 확인하나요?',596,408,540,'detail','font-weight:700')
    c+=t('확정 여부 / 날짜의 의미 / 원문에 없는 추정',596,448,580,'detail muted')
    c+=t('수정한 문장',596,507,540,'label accent')
    c+=r(596,580,588,1,'#B5AEA1')
    slides.append(slide('editorial',c,'가상 예시임을 표시한다. 수정란은 참가자가 채운다. 실제 교육에서는 사용자 원문과 검토 목적에 맞춰 항목을 바꾼다.'))

    c=folio('OPERATIONS / DECISION GATE',3,'운영 조건표 템플릿 · 수치·일정·담당자는 실제 기획에 맞게 입력')
    c+=t('시작 조건이 충족되면<br>실행으로 넘어갑니다.',64,126,1090,'title',tag='h2')
    c+=table(64,287,1152,[22,41,37],[
        ['시작 조건','확인할 자료','미충족 시 조치'],
        ['모집 기준 충족','확정 인원 / 최소 운영 인원','발주 전 모집 연장 여부 결정'],
        ['공간·담당 확보','장소 예약 / 진행자 배정','일정 조정 후 참가자 안내'],
        ['비용 범위 확인','수량 × 단가 + 부대 비용','필수 물량부터 범위 조정'],
    ],height=272)
    c+=t('확인 시점: 발주·모집 확정 전',64,594,560,'detail','font-weight:700')
    c+=t('결정 담당: 운영 책임자 지정',704,594,512,'detail muted','text-align:right')
    slides.append(slide('strategy',c,'최소 인원이나 예산 상한을 임의로 정하지 않는다. 운영안에서 정한 조건과 담당자를 이 표에 연결한다. 표 셀은 PowerPoint에서도 편집 가능하다.'))
    return slides


def main():
    compile_tokens()
    modes={'editorial':editorial(),'product':product(),'strategy':strategy()}
    for name,slides in modes.items():
        (SYSTEM/'examples'/f'{name}.html').write_text(document(name,slides),encoding='utf-8')
    components=SYSTEM/'components'
    components.mkdir(exist_ok=True)
    companion=document('working-artifacts',working_artifacts()).replace('</head>',
        '<style>.service{--surface:#14212D;--ink:#FFFFFF;--muted:#BCC9D0;'
        '--accent:#C9F46A;--line:#42515E}</style></head>')
    (components/'working-artifacts.html').write_text(companion,encoding='utf-8')
    print('Studio specimens: '+', '.join(f'{key} {len(value)} slides' for key,value in modes.items()))
    print('Native working-artifact examples: 3 slides')


if __name__=='__main__':main()
