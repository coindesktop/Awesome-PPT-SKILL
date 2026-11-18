// The same JSON is consumed by Chart.js for preview and python-pptx for export.
window.pptkitReady=document.fonts.ready.then(()=>{
  for(const el of document.querySelectorAll('[data-pptx="chart"]')){
    const spec=JSON.parse(document.getElementById(el.dataset.source).textContent);
    const canvas=document.createElement('canvas');el.appendChild(canvas);
    const line=spec.type==='line';
    const ticks={font:{family:spec.font||'Pretendard',size:spec.fontSize||16},color:spec.labelColor||'#61716B',padding:10};
    const valueScale={beginAtZero:true,max:spec.maxValue,ticks:{...ticks,stepSize:spec.majorUnit},
      afterBuildTicks:axis=>{if(spec.majorUnit)axis.ticks=axis.ticks.filter(t=>Math.abs(t.value/spec.majorUnit-Math.round(t.value/spec.majorUnit))<1e-8)}};
    new Chart(canvas,{type:line?'line':'bar',data:{labels:spec.categories,datasets:spec.series.map(s=>({
      label:s.name,data:s.values,backgroundColor:s.color||'#164F46',borderColor:s.color||'#164F46',borderWidth:line?3:0,
      pointRadius:0,pointHoverRadius:0,tension:0,borderRadius:0,barPercentage:.65,categoryPercentage:.8
    }))},options:{animation:false,responsive:true,maintainAspectRatio:false,indexAxis:spec.type==='bar'?'y':'x',
      plugins:{legend:{display:spec.series.length>1,position:'bottom',labels:{color:ticks.color,font:ticks.font,usePointStyle:true,boxWidth:8,padding:20}},tooltip:{enabled:false}},
      layout:{padding:{top:10,right:16}},
      scales:{x:{ticks,offset:line,grid:{display:spec.type==='bar',color:spec.gridColor||'#DBE3DD',drawTicks:false},border:{display:false},
        ...(spec.type==='bar'?valueScale: {})},
      y:{ticks,grid:{display:spec.type!=='bar',color:spec.gridColor||'#DBE3DD',drawTicks:false},border:{display:false},
        ...(spec.type!=='bar'?valueScale: {})}}
    }});
  }
});
