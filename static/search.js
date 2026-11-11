(()=>{
// IT-chokan full-text search (v1). Substring AND match on NFKC + lowercase text; no word splitting needed for Japanese.
const q=document.getElementById('q'),list=document.getElementById('results'),count=document.getElementById('count');
if(!q||!list)return;
const SYN={'漏洩':'漏えい','ろうえい':'漏えい','脆弱性':'穴'};
const norm=s=>s.normalize('NFKC').toLowerCase();
let DATA=null,timer=0;
function terms(v){
  const t=norm(v).split(/\s+/).filter(Boolean);
  return t.map(w=>SYN[w]?[w,SYN[w]]:[w]);
}
function hitAt(low,alts){for(const a of alts){const i=low.indexOf(a);if(i>=0)return[i,a.length]}return null}
function snippet(text,low,ts){
  const first=hitAt(low,ts[0])||[0,0];
  const s=Math.max(0,first[0]-40),e=Math.min(text.length,first[0]+90);
  const frag=document.createDocumentFragment();
  if(s>0)frag.append('…');
  const seg=text.slice(s,e),segLow=low.slice(s,e),marks=[];
  ts.flat().forEach(a=>{if(!a)return;let i=0;while((i=segLow.indexOf(a,i))>=0){marks.push([i,i+a.length]);i+=a.length}});
  marks.sort((a,b)=>a[0]-b[0]);
  let pos=0;
  for(const [a,b] of marks){if(a<pos)continue;frag.append(seg.slice(pos,a));const m=document.createElement('mark');m.textContent=seg.slice(a,b);frag.append(m);pos=b}
  frag.append(seg.slice(pos));
  if(e<text.length)frag.append('…');
  return frag;
}
function render(){
  const v=q.value.trim();
  const url=new URL(location.href);
  if(v)url.searchParams.set('q',v);else url.searchParams.delete('q');
  history.replaceState(null,'',url);
  list.textContent='';
  if(!v){count.textContent='';return}
  if(!DATA){count.textContent='読み込み中…';return}
  const ts=terms(v),res=[];
  for(const e of DATA){
    const all=e._l||(e._l=norm(e.h+' '+e.x));
    if(ts.every(alts=>hitAt(all,alts)))res.push(e);
  }
  count.textContent=res.length?`${res.length}件見つかりました`+(res.length>50?'（新しい順に50件を表示）':''):'見つかりませんでした。別の言葉や、短い言葉で試してください。';
  for(const e of res.slice(0,50)){
    const li=document.createElement('li');
    const a=document.createElement('a');a.href='../'+e.u;
    const d=document.createElement('span');d.className='rd';d.textContent=e.d;
    const h=document.createElement('span');h.className='rh';h.textContent=e.h;
    a.append(d,h);
    if(e.g){const g=document.createElement('span');g.className='tag rg';g.textContent=e.g;a.append(g)}
    const p=document.createElement('p');p.className='rs';
    p.append(snippet(e.x,e._x||(e._x=norm(e.x)),ts));
    li.append(a,p);list.append(li);
  }
}
q.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(render,120)});
const init=new URLSearchParams(location.search).get('q');
if(init)q.value=init;
fetch('../search.json').then(r=>r.ok?r.json():[]).then(j=>{
  DATA=(j||[]).sort((a,b)=>a.d<b.d?1:a.d>b.d?-1:0);render();
}).catch(()=>{count.textContent='検索データを読み込めませんでした。時間をおいて再読み込みしてください。'});
if(!init)q.focus();
})();
