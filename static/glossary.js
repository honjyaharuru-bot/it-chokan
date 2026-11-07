(()=>{
const el=document.getElementById('glossary-data');if(!el)return;
const G=JSON.parse(el.textContent);
const KEY='itasakan-known';
let known=new Set();
try{known=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify([...known]))}catch(e){}};
const byKey=new Map();
G.terms.forEach(t=>[t.term,...(t.aliases||[])].forEach(k=>byKey.set(k,t)));
const keys=[...byKey.keys()].sort((a,b)=>b.length-a.length);
const esc=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const ascii=s=>/^[\x20-\x7e]+$/.test(s);
const re=new RegExp(keys.map(k=>ascii(k)?'(?<![A-Za-z0-9-])'+esc(k)+'(?![A-Za-z0-9-])':esc(k)).join('|'),'g');
const root=document.getElementById('article');
const used=new Set();
function wrap(){
  root.querySelectorAll('button.term').forEach(b=>b.replaceWith(document.createTextNode(b.textContent)));
  root.normalize();
  root.querySelectorAll('.topic,.summary,.words').forEach(sec=>{
    const seen=new Set();
    const w=document.createTreeWalker(sec,NodeFilter.SHOW_TEXT);
    const nodes=[];while(w.nextNode())nodes.push(w.currentNode);
    nodes.forEach(n=>{
      const s=n.nodeValue;re.lastIndex=0;let m,last=0,frag=null;
      while((m=re.exec(s))){
        const t=byKey.get(m[0]);used.add(t.term);
        if(known.has(t.term)||seen.has(t.term))continue;
        seen.add(t.term);frag=frag||document.createDocumentFragment();
        frag.append(s.slice(last,m.index));
        const b=document.createElement('button');b.type='button';b.className='term';b.textContent=m[0];b.dataset.t=t.term;
        frag.append(b);last=m.index+m[0].length;
      }
      if(frag){frag.append(s.slice(last));n.replaceWith(frag)}
    });
  });
  const ul=document.getElementById('gllist');if(!ul)return;ul.textContent='';
  G.terms.filter(t=>used.has(t.term)).forEach(t=>{
    const li=document.createElement('li');if(known.has(t.term))li.className='k';
    const b=document.createElement('b');b.textContent=t.term;li.append(b,t.short);ul.append(li);
  });
}
const sheet=document.getElementById('sheet');let cur=null,curBtn=null;
function open(btn){
  const t=G.terms.find(x=>x.term===btn.dataset.t);cur=t;
  if(curBtn)curBtn.classList.remove('on');curBtn=btn;btn.classList.add('on');
  document.getElementById('sT').textContent=t.term;
  document.getElementById('sS').textContent=t.short;
  document.getElementById('sL').textContent=t.long;
  sheet.hidden=false;
}
function close(){sheet.hidden=true;if(curBtn)curBtn.classList.remove('on');curBtn=null}
root.addEventListener('click',e=>{const b=e.target.closest('button.term');if(b)open(b)});
document.getElementById('sX').onclick=close;
document.getElementById('sK').onclick=()=>{if(cur){known.add(cur.term);save();close();wrap()}};
const r=document.getElementById('reset');if(r)r.onclick=()=>{known=new Set();save();wrap()};
document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
wrap();
})();
