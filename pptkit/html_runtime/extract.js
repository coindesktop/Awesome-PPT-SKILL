// pptkit HTML contract v1. DOM measurements are relative to each fixed slide.
() => {
  const errors = [];
  const slides = [...document.querySelectorAll('section.slide')];
  const result = [];
  const norm = s => s.replace(/\s+/g, ' ').trim();
  const cssColor = value => {
    const m = value.match(/^rgba?\(([^)]+)\)$/);
    if (!m) return {hex: '000000', alpha: 1};
    const v = m[1].split(',').map(Number);
    return {hex: v.slice(0, 3).map(n => Math.round(n).toString(16).padStart(2, '0')).join(''), alpha: v[3] ?? 1};
  };
  const textStyle = el => {
    const s = getComputedStyle(el);
    return {
      font: s.fontFamily.split(',')[0].replaceAll('"', '').replaceAll("'", '').trim(),
      size: parseFloat(s.fontSize), bold: Number(s.fontWeight) >= 600,
      italic: s.fontStyle === 'italic', underline: s.textDecorationLine.includes('underline'),
      color: cssColor(s.color), align: s.textAlign,
      tracking: s.letterSpacing === 'normal' ? 0 : parseFloat(s.letterSpacing),
      lineHeight: s.lineHeight === 'normal' ? parseFloat(s.fontSize) * 1.2 : parseFloat(s.lineHeight),
    };
  };
  const runs = root => {
    const out = [];
    function visit(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent.replace(/\s+/g, ' ');
        if (text) out.push({text, ...textStyle(node.parentElement)});
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (node.tagName === 'BR') out.push({text: '\n', ...textStyle(node.parentElement)});
        else [...node.childNodes].forEach(visit);
      }
    }
    [...root.childNodes].forEach(visit);
    if (out.length) {out[0].text = out[0].text.trimStart(); out.at(-1).text = out.at(-1).text.trimEnd();}
    return out;
  };
  if (!slides.length) errors.push('section.slide가 없습니다. pptkit html init으로 시작하세요.');
  for (const [index, slide] of slides.entries()) {
    const prefix = `S${index + 1}`;
    const base = slide.getBoundingClientRect();
    if (cssColor(getComputedStyle(slide).backgroundColor).alpha !== 1)
      errors.push(`${prefix}: 슬라이드 배경색을 불투명 단색으로 명시하세요.`);
    if (Math.abs(base.width - 1280) > 1 || Math.abs(base.height - 720) > 1)
      errors.push(`${prefix}: 슬라이드 크기는 1280×720px이어야 합니다.`);
    const nodes = [...slide.querySelectorAll('[data-pptx]')];
    const entries = [];
    // Detect unexported content and unsupported painted layers, not just marked elements.
    const walker = document.createTreeWalker(slide, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode, parent = node.parentElement;
      if (!norm(node.textContent) || parent.closest('script,style,[data-notes]')) continue;
      const rect = parent.getBoundingClientRect();
      if (!rect.width || !rect.height || getComputedStyle(parent).visibility === 'hidden') continue;
      if (!parent.closest('[data-pptx="text"],[data-pptx="table"],[data-pptx="chart"]'))
        errors.push(`${prefix}: 내보내기 표시가 없는 텍스트: ${norm(node.textContent).slice(0, 40)}`);
    }
    for (const el of [slide, ...slide.querySelectorAll('*')]) {
      if (el.closest('script,style,[data-notes]')) continue;
      if (el.parentElement?.closest('[data-pptx="chart"],[data-pptx="table"]')) continue;
      const s = getComputedStyle(el), rect = el.getBoundingClientRect();
      if (!rect.width || !rect.height || s.display === 'none' || s.visibility === 'hidden') continue;
      const label = `${prefix} ${el.id || el.tagName.toLowerCase()}`;
      for (const [key, value] of Object.entries({transform:s.transform, filter:s.filter,
        backdropFilter:s.backdropFilter, boxShadow:s.boxShadow, textShadow:s.textShadow,
        backgroundImage:s.backgroundImage, clipPath:s.clipPath, maskImage:s.maskImage})) {
        if (value && value !== 'none') errors.push(`${label}: ${key}은 편집형 변환 v1에서 지원하지 않습니다.`);
      }
      if (s.opacity !== '1' || s.mixBlendMode !== 'normal' || s.zIndex !== 'auto')
        errors.push(`${label}: opacity/mix-blend-mode/z-index 대신 DOM 순서와 단색을 사용하세요.`);
      for (const pseudo of ['::before', '::after']) {
        const ps = getComputedStyle(el, pseudo);
        if (ps.content !== 'none' && ps.content !== 'normal')
          errors.push(`${label}: ${pseudo} 대신 실제 HTML 요소를 사용하세요.`);
      }
      const owner = el.dataset.pptx;
      const insideData = el.closest('[data-pptx="chart"],[data-pptx="table"]');
      const painted = cssColor(s.backgroundColor).alpha > 0 ||
        ['Top','Right','Bottom','Left'].some(side => parseFloat(s[`border${side}Width`]) > 0);
      if (el !== slide && painted && !insideData && owner !== 'shape')
        errors.push(`${label}: 배경·테두리는 data-pptx="shape" 요소에 지정하세요.`);
      if (['SVG','CANVAS','VIDEO','IFRAME'].includes(el.tagName.toUpperCase()) && !insideData)
        errors.push(`${label}: 미지원 미디어입니다. 원본 이미지 또는 편집형 도형으로 표현하세요.`);
      if (el.tagName === 'IMG' && owner !== 'image' && !insideData)
        errors.push(`${label}: 이미지에 data-pptx="image" 표시가 필요합니다.`);
      if (['UL','OL'].includes(el.tagName) && !insideData)
        errors.push(`${label}: 목록의 각 항목을 독립된 text 요소로 작성하세요.`);
      if (el.closest('[data-pptx="text"]') && s.textTransform !== 'none')
        errors.push(`${label}: text-transform 대신 변환된 문구를 직접 작성하세요.`);
    }
    for (const el of nodes) {
      if (el.parentElement?.closest('[data-pptx="text"],[data-pptx="table"],[data-pptx="chart"]')) continue;
      const kind = el.dataset.pptx, s = getComputedStyle(el), rect = el.getBoundingClientRect();
      if (!rect.width || !rect.height || s.visibility === 'hidden' || s.display === 'none') continue;
      const box = {x:rect.left-base.left, y:rect.top-base.top, w:rect.width, h:rect.height};
      const name = el.id || `${kind}-${entries.length+1}`;
      const label = `${prefix} ${name}`;
      if (box.x < -1 || box.y < -1 || box.x+box.w > base.width+1 || box.y+box.h > base.height+1)
        errors.push(`${label}: 슬라이드 영역을 벗어났습니다.`);
      // Korean glyph ink may extend a few pixels beyond its CSS line box.
      if (el.scrollWidth > el.clientWidth + 2 || el.scrollHeight > el.clientHeight + 4)
        errors.push(`${label}: 내용이 요소 크기를 넘습니다. 글을 줄이거나 영역을 키우세요.`);
      if (kind === 'text') {
        if (!['left','start','center','right','end'].includes(s.textAlign))
          errors.push(`${label}: text-align은 left, center, right를 사용하세요.`);
        if (s.textTransform !== 'none' || s.whiteSpace !== 'normal')
          errors.push(`${label}: text-transform/white-space 대신 본문과 <br>을 사용하세요.`);
        for (const child of el.querySelectorAll('*')) {
          if (!['SPAN','B','STRONG','I','EM','U','BR'].includes(child.tagName))
            errors.push(`${label}: 텍스트 안에는 인라인 요소와 <br>만 허용됩니다.`);
        }
        const padding = ['Top','Right','Bottom','Left'].map(side => parseFloat(s[`padding${side}`]));
        entries.push({kind,name,box,style:textStyle(el),runs:runs(el),padding,
          singleLine:!el.querySelector('br') && rect.height-padding[0]-padding[2] <= textStyle(el).lineHeight+1});
      } else if (kind === 'shape') {
        const sides = ['Top','Right','Bottom','Left'].map(side => ({width:parseFloat(s[`border${side}Width`]),
          color:cssColor(s[`border${side}Color`]), style:s[`border${side}Style`]}));
        if (sides.some(b=>b.width && b.style !== 'solid')) errors.push(`${label}: 실선 테두리만 지원합니다.`);
        const radii = ['TopLeft','TopRight','BottomRight','BottomLeft'].map(c=>s[`border${c}Radius`]);
        if (new Set(radii).size !== 1 || radii[0].includes(' ')) errors.push(`${label}: 같은 크기의 모서리 반경을 사용하세요.`);
        const radius = parseFloat(radii[0]);
        entries.push({kind,name,box,fill:cssColor(s.backgroundColor),sides,
          ellipse:radii[0].includes('%') && radius >= 50,
          radius:radii[0].includes('%') ? Math.min(box.w,box.h)*radius/100 : radius});
      } else if (kind === 'image') {
        if (el.tagName !== 'IMG' || !el.complete || !el.naturalWidth) errors.push(`${label}: 로컬 이미지 로딩에 실패했습니다.`);
        if (!['fill','contain','cover'].includes(s.objectFit)) errors.push(`${label}: object-fit은 fill, contain 또는 cover를 사용하세요.`);
        if (s.objectPosition !== '50% 50%' || parseFloat(s.borderRadius))
          errors.push(`${label}: 이미지 위치 조정·둥근 크롭은 원본 이미지에 반영하세요.`);
        entries.push({kind,name,box,src:el.currentSrc,fit:s.objectFit,natural:[el.naturalWidth,el.naturalHeight]});
      } else if (kind === 'table') {
        if (el.tagName !== 'TABLE') errors.push(`${label}: table 태그를 사용하세요.`);
        const rows = [...el.rows].map(row=>[...row.cells].map(cell=>{
          if (cell.colSpan !== 1 || cell.rowSpan !== 1) errors.push(`${label}: 병합 셀은 v1에서 지원하지 않습니다.`);
          const cs=getComputedStyle(cell), cr=cell.getBoundingClientRect();
          return {text:cell.innerText,style:textStyle(cell),fill:cssColor(cs.backgroundColor),w:cr.width,h:cr.height,
            padding:['Top','Right','Bottom','Left'].map(side=>parseFloat(cs[`padding${side}`])),
            borders:['Top','Right','Bottom','Left'].map(side=>({width:parseFloat(cs[`border${side}Width`]),color:cssColor(cs[`border${side}Color`])}))};
        }));
        entries.push({kind,name,box,rows});
      } else if (kind === 'chart') {
        try {
          const data = JSON.parse(document.getElementById(el.dataset.source).textContent);
          entries.push({kind,name,box,data});
        } catch { errors.push(`${label}: data-source가 올바른 JSON script를 가리켜야 합니다.`); }
      } else errors.push(`${label}: 알 수 없는 data-pptx 종류입니다.`);
    }
    result.push({background:cssColor(getComputedStyle(slide).backgroundColor),
      notes:slide.querySelector('[data-notes]')?.textContent.trim() || '', entries});
  }
  return {slides:result, errors:[...new Set(errors)]};
}
