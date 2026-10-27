/* Local-only opportunity card filter. No applicant data is sent to RibhLab. */
for (const widget of document.querySelectorAll('[data-opportunity-list]')) {
  const search=document.querySelector('[data-opportunity-search]');
  const clear=document.querySelector('[data-opportunity-clear]');
  const empty=document.querySelector('[data-opportunity-empty]');
  if(!search)continue;
  // Keep deadline ordering accurate in the browser, even between deployments.
  const cards=[...widget.querySelectorAll('[data-opp-item]')];
  const today=new Date().toLocaleDateString('en-CA',{timeZone:'Africa/Casablanca'});
  const expiredLabel={ar:'انتهى آخر أجل',en:'Deadline passed',fr:'Date limite dépassée'}[document.documentElement.lang]||'Deadline passed';
  const key=card=>{
    const deadline=card.dataset.deadline;
    if(!deadline)return [1,'9999-12-31'];
    if(deadline<today)return [2,'9999-12-31']; // expired listings move below live entries
    return [0,deadline];
  };
  cards.sort((a,b)=>{
    const ka=key(a),kb=key(b);
    return ka[0]-kb[0] || ka[1].localeCompare(kb[1]);
  });
  for(const card of cards){
    const deadline=card.dataset.deadline;
    if(deadline&&deadline<today&&!card.querySelector('.opp-expired-label')){
      const pill=document.createElement('span');
      pill.className='opp-muted opp-expired-label';
      pill.textContent=expiredLabel;
      const header=card.querySelector('.opp-topline');
      header?.appendChild(pill);
    }
    widget.appendChild(card);
  }
  const normalize=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
  function filter(){
    const q=normalize(search.value);
    let visible=0;
    for(const card of cards){const deadline=card.dataset.deadline;const stillOpen=!deadline||deadline>=today;const hit=stillOpen&&normalize(card.textContent).includes(q);card.hidden=!hit;if(hit)visible++;}
    if(empty)empty.hidden=visible!==0;
  }
  filter();
  search.addEventListener('input',filter);
  if(clear)clear.addEventListener('click',()=>{search.value='';filter();search.focus();});
}
