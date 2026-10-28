(()=>{'use strict';
const list=document.querySelector('[data-recipe-list]'),search=document.querySelector('[data-recipe-search]');
if(!list||!search)return;
const cards=[...list.querySelectorAll('[data-recipe-card]')],buttons=[...document.querySelectorAll('[data-recipe-filter]')],counter=document.querySelector('[data-recipe-result-count]'),empty=document.querySelector('[data-recipe-empty]');
let filter='all';const totalSuffix=(counter?.textContent||'').replace(/^\d+\s*/,''),normalize=s=>String(s||'').normalize('NFKC').toLocaleLowerCase().trim();
function update(){
const term=normalize(search.value);let found=0;
for(const card of cards){const visible=(filter==='all'||card.dataset.kind===filter)&&(!term||normalize(card.dataset.search).includes(term));card.hidden=!visible;if(visible)found++;}
if(counter)counter.textContent=found+' '+totalSuffix;if(empty)empty.hidden=found!==0;
}
buttons.forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.recipeFilter;buttons.forEach(x=>x.classList.toggle('active',x===b));update()}));
search.addEventListener('input',update);
})();