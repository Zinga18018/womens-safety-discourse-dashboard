import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root=new URL('../',import.meta.url);
const data=JSON.parse(fs.readFileSync(new URL('docs/data/public_summary.json',root),'utf8'));
const html=fs.readFileSync(new URL('docs/index.html',root),'utf8');
class Element { constructor(){this.children=[];this.listeners={};this.textContent='';this.innerHTML='';this.value='';} appendChild(x){this.children.push(x);} addEventListener(t,cb){this.listeners[t]=cb;} }
const elements=Object.fromEntries([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],new Element()]));
const plots={};const body=new Element();
const context=vm.createContext({console,Intl,Date,document:{body,getElementById:id=>{assert.ok(elements[id],id);return elements[id];},createElement:()=>new Element()},fetch:async()=>({json:async()=>data}),Plotly:{newPlot:(id,traces,layout,config)=>{plots[id]={traces,layout,config};}}});
vm.runInContext(fs.readFileSync(new URL('docs/app.js',root),'utf8'),context);
await new Promise(resolve=>setImmediate(resolve));
assert.equal(body.innerHTML,'');
assert.equal(elements['case-select'].children.length,16);
assert.equal(Object.keys(plots).length,5);
assert.equal(elements['metric-rows'].textContent,'351,501');
for(const item of [...data.per_case,...data.per_case].reverse()){
 elements['case-select'].value=item.case;elements['case-select'].listeners.change();
 const platform=plots['platform-chart'];assert.equal(platform.traces[0].type,'bar');
 assert.deepEqual(Array.from(platform.traces[0].y),Object.values(item.platform_counts));
 assert.equal(platform.layout.yaxis.title,'Rows');
 assert.equal(plots['timeline-chart'].traces[0].y.reduce((a,b)=>a+b,0),data.monthly_case_counts.filter(x=>x.case===item.case).reduce((a,b)=>a+b.count,0));
 assert.ok(elements['case-note'].textContent.startsWith(new Intl.NumberFormat('en-US').format(item.n)));
}
console.log('PASS: initialization, 5 genuine plots, all 16 case selections repeated, counts/axes/timelines retained; no browser render claimed.');
