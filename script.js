(function(){
const files={
 meta:'data/meta.json',
 pink:'data/pink_tax.json',
 style:'data/style_gender.json',
 palette:'data/palette_gender.json',
 ladder:'data/price_ladder.json',
 tone:'data/unisex_tone.json',
 photos:'data/photos_price.json',
 dress:'data/dress_price.json',
 words:'data/roadster_words.json',
 charm:'data/charm_pricing.json',
 heat:'data/color_price_heat.json',
capsule:'data/capsule.json'
};
const observer=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible');}),{threshold:0.1});
Promise.all(Object.values(files).map(f=>fetch(f).then(r=>r.json()))).then(([meta,pink,style,palette,ladder,tone,photos,dress,words,charm,heat,capsule])=>{
  d3.select('#meta').text(`${meta.rows} items · ${meta.brands} brands`);
  renderPinkTax(pink);renderStyleGender(style);renderPaletteGender(palette);renderPriceLadder(ladder);
  renderUnisexTone(tone);renderPhotosPrice(photos);renderDressPrice(dress);renderRoadsterWords(words);
  renderCharmPricing(charm);renderColorPriceHeat(heat);renderCapsule(capsule);
  document.querySelectorAll('.chart').forEach(el=>observer.observe(el));
});

function svgIn(sel,h){
 const c=d3.select(sel);const w=c.node().clientWidth;
 const svg=c.append('svg').attr('viewBox',`0 0 ${w} ${h}`).attr('preserveAspectRatio','xMidYMid meet').classed('fade',true);
 window.addEventListener('resize',()=>{svg.attr('viewBox',`0 0 ${c.node().clientWidth} ${h}`);});
 return svg.append('g');
}

function renderPinkTax(data){
 const g=svgIn('#pink-tax .chart',240),w=g.node().ownerSVGElement.clientWidth,h=200;
 const x=d3.scaleBand().domain(['Women-Pink','Men-Blue']).range([40,w-20]).padding(0.4);
 const y=d3.scaleLinear().domain([0,d3.max([data.women_mean,data.men_mean])*1.2]).nice().range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('rect').data([data.women_mean,data.men_mean]).enter().append('rect')
   .attr('x',(d,i)=>x(i? 'Men-Blue':'Women-Pink'))
   .attr('width',x.bandwidth()).attr('y',h).attr('height',0).attr('fill','#f9a').transition().duration(400)
   .attr('y',d=>y(d)).attr('height',d=>h-y(d));
}

function renderStyleGender(data){
 const g=svgIn('#style-gender .chart',260),w=g.node().ownerSVGElement.clientWidth-60,h=200;
 const stack=d3.stack().keys(data.genders)(d3.transpose(data.matrix));
 const x=d3.scaleBand().domain(data.styles).range([40,w]).padding(0.2);
 const y=d3.scaleLinear().domain([0,d3.max(stack[stack.length-1],d=>d[1])]).range([h,20]);
 const color=d3.scaleOrdinal().domain(data.genders).range(d3.schemePastel1);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('g.layer').data(stack).enter().append('g').attr('fill',d=>color(d.key)).selectAll('rect')
   .data(d=>d).enter().append('rect').attr('x',(d,i)=>x(data.styles[i]))
   .attr('width',x.bandwidth()).attr('y',h).attr('height',0)
   .transition().duration(400).attr('y',d=>y(d[1])).attr('height',d=>y(d[0])-y(d[1]));
 g.append('g').selectAll('text').data(data.genders).enter().append('text').attr('x',w-20).attr('y',(d,i)=>20+i*14).text(d=>d).attr('fill',d=>color(d));
}

function renderPaletteGender(data){
 const g=svgIn('#palette-gender .chart',260),w=g.node().ownerSVGElement.clientWidth-60,h=200;
 const x0=d3.scaleBand().domain(data.map(d=>d.color)).range([40,w]).padding(0.2);
 const x1=d3.scaleBand().domain(['men','women']).range([0,x0.bandwidth()]).padding(0.1);
 const y=d3.scaleLinear().domain([0,d3.max(data,d=>Math.max(d.men,d.women))]).range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x0));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.append('g').selectAll('g').data(data).enter().append('g').attr('transform',d=>`translate(${x0(d.color)},0)`).selectAll('rect')
   .data(d=>[d.men,d.women]).enter().append('rect').attr('x',(d,i)=>x1(i? 'women':'men')).attr('width',x1.bandwidth())
   .attr('y',h).attr('height',0).attr('fill',(d,i)=>i?'#f4a':'#69b').transition().duration(400)
   .attr('y',d=>y(d)).attr('height',d=>h-y(d));
}

function renderPriceLadder(data){
 const g=svgIn('#price-ladder .chart',300),w=g.node().ownerSVGElement.clientWidth-100,h=250;
 const y=d3.scaleBand().domain(data.map(d=>d.brand)).range([20,h]).padding(0.2);
 const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.median_price)]).range([0,w]);
 g.append('g').attr('transform','translate(100,0)').call(d3.axisLeft(y));
 g.append('g').attr('transform',`translate(100,${h})`).call(d3.axisBottom(x));
 g.selectAll('rect').data(data).enter().append('rect').attr('x',100).attr('y',d=>y(d.brand))
   .attr('width',0).attr('height',y.bandwidth()).attr('fill','#9ad').transition().duration(400)
   .attr('width',d=>x(d.median_price));
}

function renderUnisexTone(data){
 const g=svgIn('#unisex-tone .chart',240),w=g.node().ownerSVGElement.clientWidth,h=200;
 const entries=Object.entries(data);
 const x=d3.scaleBand().domain(entries.map(d=>d[0])).range([40,w-20]).padding(0.4);
 const y=d3.scaleLinear().domain([0,d3.max(entries,d=>d[1])]).range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('rect').data(entries).enter().append('rect').attr('x',d=>x(d[0])).attr('width',x.bandwidth())
   .attr('y',h).attr('height',0).attr('fill','#fac').transition().duration(400)
   .attr('y',d=>y(d[1])).attr('height',d=>h-y(d[1]));
}

function renderPhotosPrice(data){
 const g=svgIn('#photos-price .chart',300),w=g.node().ownerSVGElement.clientWidth-60,h=240;
 const x=d3.scaleLinear().domain(d3.extent(data.points,d=>d[0])).range([40,w]);
 const y=d3.scaleLinear().domain(d3.extent(data.points,d=>d[1])).nice().range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('circle').data(data.points).enter().append('circle').attr('cx',d=>x(d[0])).attr('cy',h).attr('r',3).attr('fill','#69b').transition().duration(400).attr('cy',d=>y(d[1]));
 const line=d3.line().x(d=>x(d[0])).y(d=>y(d[1]));
 const regPts=[[x.domain()[0], data.slope*x.domain()[0]+data.intercept],[x.domain()[1], data.slope*x.domain()[1]+data.intercept]];
 g.append('path').attr('d',line(regPts)).attr('stroke','#c33').attr('fill','none');
}

function renderDressPrice(data){
 const g=svgIn('#dress-price .chart',300),w=g.node().ownerSVGElement.clientWidth-60,h=240;
 const x=d3.scaleBand().domain(data.map(d=>d.code)).range([40,w]).padding(0.3);
 const y=d3.scaleLinear().domain([0,d3.max(data,d=>d.max)]).nice().range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 const box=g.selectAll('g.box').data(data).enter().append('g').attr('transform',d=>`translate(${x(d.code)},0)`);
 box.append('line').attr('y1',d=>y(d.min)).attr('y2',d=>y(d.max)).attr('x1',x.bandwidth()/2).attr('x2',x.bandwidth()/2).attr('stroke','#999');
 box.append('rect').attr('y',d=>y(d.q3)).attr('height',d=>y(d.q1)-y(d.q3)).attr('width',x.bandwidth()).attr('fill','#bcd');
 box.append('line').attr('y1',d=>y(d.median)).attr('y2',d=>y(d.median)).attr('x1',0).attr('x2',x.bandwidth()).attr('stroke','#333');
}

function renderRoadsterWords(data){
 const g=svgIn('#roadster-words .chart',260),w=g.node().ownerSVGElement.clientWidth-100,h=200;
 const y=d3.scaleBand().domain(data.map(d=>d.word)).range([20,h]).padding(0.2);
 const x=d3.scaleLinear().domain([0,d3.max(data,d=>d.count)]).range([0,w]);
 g.append('g').attr('transform','translate(100,0)').call(d3.axisLeft(y));
 g.append('g').attr('transform',`translate(100,${h})`).call(d3.axisBottom(x));
 g.selectAll('rect').data(data).enter().append('rect').attr('x',100).attr('y',d=>y(d.word))
   .attr('width',0).attr('height',y.bandwidth()).attr('fill','#f7b').transition().duration(400)
   .attr('width',d=>x(d.count));
}

function renderCharmPricing(data){
 const g=svgIn('#charm-pricing .chart',240),w=g.node().ownerSVGElement.clientWidth,h=200;
 const entries=Object.entries(data);
 const x=d3.scaleBand().domain(entries.map(d=>d[0])).range([40,w-20]).padding(0.4);
 const y=d3.scaleLinear().domain([0,d3.max(entries,d=>d[1])]).range([h,20]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('rect').data(entries).enter().append('rect').attr('x',d=>x(d[0])).attr('width',x.bandwidth())
   .attr('y',h).attr('height',0).attr('fill','#9c9').transition().duration(400)
   .attr('y',d=>y(d[1])).attr('height',d=>h-y(d[1]));
}

function renderColorPriceHeat(data){
 const g=svgIn('#color-price-heat .chart',320),w=g.node().ownerSVGElement.clientWidth-60,h=260;
 const x=d3.scaleBand().domain(data.buckets).range([40,w]).padding(0.05);
 const y=d3.scaleBand().domain(data.colors).range([20,h]).padding(0.05);
 const color=d3.scaleSequential(d3.interpolateBlues).domain([0,d3.max(data.matrix.flat())]);
 g.append('g').attr('transform',`translate(0,${h})`).call(d3.axisBottom(x));
 g.append('g').attr('transform','translate(40,0)').call(d3.axisLeft(y));
 g.selectAll('rect').data(data.colors.flatMap((c,i)=>data.buckets.map((b,j)=>({c,b,v:data.matrix[i][j]}))))
   .enter().append('rect').attr('x',d=>x(d.b)).attr('y',d=>y(d.c))
   .attr('width',x.bandwidth()).attr('height',y.bandwidth())
   .attr('fill',d=>color(d.v)).attr('opacity',0).transition().duration(400).attr('opacity',1);
}

function renderCapsule(data){
 const div=d3.select('#capsule .chart');
 const table=div.append('table').classed('fade',true);
 const thead=table.append('thead').append('tr');
 ['Item','Brand','Colour','Price'].forEach(t=>thead.append('th').text(t));
 const rows=table.append('tbody').selectAll('tr').data(data).enter().append('tr');
 rows.append('td').text(d=>d.ProductName);
 rows.append('td').text(d=>d.ProductBrand);
 rows.append('td').text(d=>d.PrimaryColor);
 rows.append('td').text(d=>`₹${d['Price (INR)']}`);
}
})();
