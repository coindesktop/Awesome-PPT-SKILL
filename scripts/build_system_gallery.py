"""Bundle an offline gallery of reviewed HTML and actual PowerPoint renders."""
import argparse
from pathlib import Path


PAGE=r'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PPTKIT Studio · 세 가지 디자인 시스템</title>
<style>
@font-face{font-family:Pretendard;src:url('editorial.assets/fonts/Pretendard-Regular.otf');font-weight:400}
@font-face{font-family:Pretendard;src:url('editorial.assets/fonts/Pretendard-Bold.otf');font-weight:700}
*{box-sizing:border-box}body{margin:0;background:#e9ece7;color:#20221f;font-family:Pretendard,sans-serif}
button,a{font:inherit}button{cursor:pointer}button:focus-visible,a:focus-visible{outline:3px solid #e64d2d;outline-offset:4px}
.wrap{max-width:1440px;margin:auto;padding:32px 44px 40px}header{display:flex;justify-content:space-between;align-items:start;gap:24px}
.eyebrow{font-size:13px;font-weight:700;letter-spacing:2px}h1{font-size:32px;letter-spacing:-1.2px;margin:14px 0 8px}p{margin:0;color:#626b62;line-height:1.6}
.tag{border:1px solid #b9c2b6;padding:9px 12px;font-size:12px;white-space:nowrap}.toolbar{display:flex;align-items:end;justify-content:space-between;gap:20px;margin:28px 0 18px}
.tabs{display:flex;gap:8px}.tabs button,.views button{border:0;background:transparent;color:#626b62;padding:12px 17px;line-height:1.3}
.tabs button{border-bottom:2px solid transparent;font-weight:700;font-size:17px}.tabs button[aria-selected=true]{border-color:#20221f;color:#20221f}
.tabs span{font-size:12px;font-weight:400;display:block;margin-top:4px}.views{display:flex;border:1px solid #bac2b7;padding:3px}
.views button{padding:8px 12px;font-size:13px}.views button[aria-pressed=true]{background:#20221f;color:white}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 224px;gap:28px;align-items:start}
.stage{background:#fff;box-shadow:0 12px 35px #20221f0d;aspect-ratio:16/9}.stage img{width:100%;height:100%;object-fit:contain;display:block}
.caption{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:13px 0 18px;font-size:13px}.caption b{margin-right:10px}.arrows{display:flex;gap:6px}.arrows button{border:1px solid #bac2b7;background:transparent;width:38px;height:32px}
.thumbs{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}.thumbs button{padding:0;background:transparent;border:2px solid transparent;opacity:.6}.thumbs button[aria-current=true]{border-color:#20221f;opacity:1}.thumbs img{width:100%;display:block}
aside{padding-top:6px}h2{font-size:24px;letter-spacing:-.6px;margin:0 0 14px}.description{font-size:14px;min-height:70px}.rule{height:1px;background:#cdd4c9;margin:22px 0}dl{margin:0;font-size:13px}dt{color:#6b7469;margin:15px 0 5px}dd{margin:0;line-height:1.5}.swatches{display:flex;gap:6px;margin-top:20px}.swatches i{width:32px;height:32px;border:1px solid #20221f15}
.download{display:block;text-decoration:none;text-align:center;background:#20221f;color:white;padding:13px 10px;margin-top:22px;font-size:14px;font-weight:700}.source{display:block;text-align:center;margin-top:12px;color:#53604f;font-size:13px}.note{font-size:12px;color:#697263;margin-top:24px;line-height:1.6}
footer{margin-top:28px;border-top:1px solid #cdd4c9;padding-top:16px;display:flex;justify-content:space-between;gap:16px;font-size:12px;color:#697263}
@media(max-width:900px){.wrap{padding:24px}.layout{grid-template-columns:1fr}aside{display:grid;grid-template-columns:1fr 1fr;gap:10px 24px}.rule,dl,.swatches{display:none}.download{margin-top:0}.note{margin:0}.toolbar{align-items:start}.tabs button{padding:10px 8px;font-size:15px}.tag{display:none}.views button{padding:8px}footer{flex-direction:column}}
@media(max-width:540px){h1{font-size:26px}.toolbar{flex-direction:column;gap:12px}.thumbs{gap:4px}aside{display:block}.download{margin-top:16px}.note{margin-top:18px}.description{min-height:0}.wrap{padding:20px 14px}}
</style></head><body><main class="wrap">
<header><div><div class="eyebrow">PPTKIT / STUDIO</div><h1>하나의 도구, 세 가지 표현.</h1><p>편집 디자인 · 제품 발표 · 전략 보고의 실제 변환 결과를 비교합니다.</p></div><div class="tag">18 SLIDES · EDITABLE POWERPOINT</div></header>
<div class="toolbar"><div class="tabs" role="tablist" aria-label="디자인 방향">
<button role="tab" data-mode="editorial" aria-selected="true">Editorial<span>편집 디자인</span></button>
<button role="tab" data-mode="product" aria-selected="false">Product<span>제품 발표</span></button>
<button role="tab" data-mode="strategy" aria-selected="false">Strategy<span>전략 보고</span></button></div>
<div class="views" aria-label="렌더 종류"><button data-view="ppt" aria-pressed="true">실제 PPT</button><button data-view="html" aria-pressed="false">HTML 원본</button></div></div>
<div class="layout"><section aria-label="슬라이드 미리보기"><div class="stage"><img id="slide" alt=""></div>
<div class="caption"><span><b id="counter"></b><span id="slide-name"></span></span><div class="arrows"><button id="prev" aria-label="이전 장">←</button><button id="next" aria-label="다음 장">→</button></div></div><div class="thumbs" id="thumbs" aria-label="장표 선택"></div></section>
<aside><h2 id="name"></h2><p class="description" id="description"></p><div class="swatches" id="swatches"></div><div class="rule"></div><dl><dt>타이포그래피</dt><dd id="type"></dd><dt>대표 구도</dt><dd id="structure"></dd><dt>에셋의 역할</dt><dd id="assets"></dd></dl><a class="download" id="download" download>편집 가능한 PPT 받기 ↗</a><a class="source" id="source">HTML 디자인 원본 열기</a><p class="note">텍스트·기본 도형·표·차트는 편집형 객체입니다. PPT를 여는 PC에는 포함된 Pretendard 서체가 필요합니다.</p></aside></div>
<footer><span>실제 PPT: Windows PowerPoint 렌더 · HTML: Chromium 렌더 · ← → 키로 장표 이동</span><span>견본 수치·서비스·UI는 가상 자료이며, 사진과 오브젝트는 생성 비주얼입니다.</span></footer>
</main><script>
const modes={
editorial:{name:'관점을 선명하게.',description:'큰 문장과 공간의 사진. 비대칭 구도와 여백으로 읽는 순서를 만듭니다.',colors:['#F2F0E9','#20221F','#E64D2D'],type:'Pretendard · 표지 88px\n본문 26px',structure:'사진 표지 / 주장과 논평 / 지표와 근거',assets:'사진의 크롭과 공간감',slides:['사진과 타이포','주장과 논평','지표와 근거','사진 에세이','구도 비교','한 문장 마무리']},
product:{name:'제품을 기억하게.',description:'명확한 물성과 강한 색. 사용 장면에서 효용과 다음 행동으로 이어집니다.',colors:['#161817','#FFFFFF','#FF653B'],type:'Pretendard · 표지 92px\n본문 26px',structure:'브랜드 비주얼 / 사용 화면 / 행동',assets:'생성 브랜드 오브젝트 + 편집형 UI',slides:['제품의 약속','사용 화면','세 단계의 흐름','성장 근거','요금제 비교','다음 행동']},
strategy:{name:'판단의 근거를.',description:'숫자와 해석을 분리하고, 정렬된 비교표로 다음 결정을 돕습니다.',colors:['#FFFFFF','#172F34','#164F46'],type:'Pretendard · 표지 70px\n본문 23px',structure:'지표 요약 / 비교표 / 실행 계획',assets:'데이터 차트와 네이티브 표',slides:['검토 범위','핵심 지표','추세와 해석','지표와 질문','실행 계획','결정 요청']}}
let mode='editorial',view='ppt',index=0;
const el=id=>document.getElementById(id);
const path=(i,v=view)=>`${mode}-${v}/slide-${String(i+1).padStart(2,'0')}.png`;
function render(){const d=modes[mode];el('slide').src=path(index);el('slide').alt=`${mode} ${index+1}장: ${d.slides[index]} · ${view==='ppt'?'실제 PowerPoint':'HTML'}`;
el('name').textContent=d.name;el('description').textContent=d.description;el('type').textContent=d.type;el('structure').textContent=d.structure;el('assets').textContent=d.assets;
el('swatches').replaceChildren(...d.colors.map(c=>{const s=document.createElement('i');s.style.background=c;s.title=c;return s}));
el('counter').textContent=`${String(index+1).padStart(2,'0')} / 06`;el('slide-name').textContent=d.slides[index];el('download').href=`${mode}.pptx`;el('source').href=`${mode}.html`;
el('thumbs').replaceChildren(...d.slides.map((label,i)=>{const b=document.createElement('button');b.setAttribute('aria-current',i===index);b.setAttribute('aria-label',`${i+1}장 ${label}`);const img=document.createElement('img');img.src=path(i);img.alt='';b.append(img);b.onclick=()=>{index=i;render()};return b}));
document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-selected',b.dataset.mode===mode));document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.view===view));}
document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;index=0;render()});document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{view=b.dataset.view;render()});
const move=delta=>{index=(index+delta+6)%6;render()};el('prev').onclick=()=>move(-1);el('next').onclick=()=>move(1);
document.addEventListener('keydown',e=>{if(e.key==='ArrowRight'){e.preventDefault();move(1)}if(e.key==='ArrowLeft'){e.preventDefault();move(-1)}});render();
</script></body></html>'''


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    for mode in ('editorial','product','strategy'):
        for view in ('html','ppt'):
            for n in range(1,7):
                image=args.directory/f'{mode}-{view}'/f'slide-{n:02}.png'
                if not image.is_file():raise FileNotFoundError(image)
        if not (args.directory/f'{mode}.pptx').is_file():raise FileNotFoundError(mode+'.pptx')
    target=args.directory/'index.html'
    target.write_text(PAGE,encoding='utf-8')
    print(target.resolve())


if __name__=='__main__':main()
