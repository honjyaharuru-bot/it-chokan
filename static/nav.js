(()=>{
const tabs=[...document.querySelectorAll('.tabs a')];
const parts=tabs.map(a=>document.getElementById(a.dataset.cat)).filter(Boolean);
function onScroll(){
  let cur=parts[0];
  for(const p of parts){if(p.getBoundingClientRect().top<120)cur=p}
  tabs.forEach(a=>a.classList.toggle('on',cur&&a.dataset.cat===cur.id));
  const tt=document.getElementById('totop');
  if(tt){const sh=document.getElementById('sheet');tt.hidden=window.scrollY<600||(sh&&!sh.hidden)}
}
window.addEventListener('scroll',onScroll,{passive:true});
document.addEventListener('click',()=>setTimeout(onScroll,0));
onScroll();
const tt=document.getElementById('totop');
if(tt)tt.addEventListener('click',e=>{e.preventDefault();window.scrollTo({top:0,behavior:'smooth'})});
})();
