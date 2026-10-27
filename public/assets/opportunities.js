/* Local-only opportunity card filter. No applicant data is sent to RibhLab. */
for (const widget of document.querySelectorAll('[data-opportunity-list]')) {
  const search=document.querySelector('[data-opportunity-search]');
  const clear=document.querySelector('[data-opportunity-clear]');
  const empty=document.querySelector('[data-opportunity-empty]');
  if(!search)continue;
  const cards=[...widget.querySelectorAll('[data-opp-item]')];
  const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  function filter(){
    const q=normalize(search.value);
    let visible=0;
    for(const card of cards){const hit=normalize(card.textContent).includes(q);card.hidden=!hit; if(hit)visible++;}
    if(empty)empty.hidden=visible!==0;
  }
  search.addEventListener('input',filter);
  if(clear)clear.addEventListener('click',()=>{search.value='';filter();search.focus();});
}
