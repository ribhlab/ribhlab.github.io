(()=>{
 'use strict';
 const byId=id=>document.getElementById(id);
 const menu=document.querySelector('.mobile-menu'),nav=byId('site-nav');
 if(menu&&nav){menu.addEventListener('click',()=>{let open=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(open));});nav.addEventListener('click',e=>{if(e.target.closest('a')){nav.classList.remove('open');menu.setAttribute('aria-expanded','false');}});}
 const modal=byId('search-modal'),openSearch=document.querySelector('[data-search-open]'),closeSearch=document.querySelector('[data-search-close]'),input=byId('site-search'),results=document.querySelector('[data-search-results]');
 const meta=window.RIBHLAB_I18N||{lang:'ar',noResults:'No results'};
 let library=null;
 const norm=text=>String(text||'').toLocaleLowerCase().normalize('NFKD').replace(/[\u064b-\u065f\u0670]/g,'').replace(/[أإآ]/g,'ا').replace(/ى/g,'ي').trim();
 const renderResults=()=>{
  if(!results||!library)return;
  const q=norm(input.value),found=library.filter(x=>!q||norm(x.search).includes(q)).slice(0,14);
  results.replaceChildren();
  if(!found.length){const el=document.createElement('p');el.className='empty-search';el.textContent=meta.noResults;results.append(el);return;}
  for(const x of found){const a=document.createElement('a');a.href=x.url;a.className='search-item';const label=document.createElement('span');label.textContent=x.category;const title=document.createElement('strong');title.textContent=x.title;const desc=document.createElement('p');desc.textContent=x.excerpt;a.append(label,title,desc);results.append(a);}
 };
 if(modal&&openSearch){openSearch.addEventListener('click',async()=>{
  if(!modal.open)modal.showModal();input.focus();
  if(library===null){try{const response=await fetch(`${window.RIBHLAB_BASE_PATH||''}/assets/search-${meta.lang}.json`);if(!response.ok)throw Error('search index missing');library=await response.json();}catch{library=[];} }
  renderResults();
 });closeSearch?.addEventListener('click',()=>modal.close());modal.addEventListener('click',e=>{if(e.target===modal)modal.close();});modal.addEventListener('close',()=>{if(input)input.value='';});input?.addEventListener('input',renderResults);
 document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();openSearch.click();}});
 }
 const n=id=>Number(byId(id)?.value||0);
 const nice=(num)=>Number.isFinite(num)?new Intl.NumberFormat(meta.lang,{minimumFractionDigits:2,maximumFractionDigits:2}).format(num):'—';
 const computeRisk=()=>{const target=byId('risk-result');if(!target)return;const capital=n('risk-capital'),rate=n('risk-percent'),currency=byId('risk-currency').value;target.textContent=capital>=0&&rate>=0&&rate<=100?`${nice(capital*rate/100)} ${currency}`:'—';};
 const computeFee=()=>{const target=byId('fee-result');if(!target)return;const h=n('fee-hours'),r=n('fee-hourly'),exp=n('fee-expenses'),fee=n('fee-platform');target.textContent=h>=0&&r>=0&&exp>=0&&fee>=0&&fee<100?nice((h*r+exp)/(1-fee/100)):'—';};
 if(byId('risk-result')){['risk-capital','risk-percent','risk-currency'].forEach(id=>byId(id)?.addEventListener('input',computeRisk));computeRisk();}
 if(byId('fee-result')){['fee-hours','fee-hourly','fee-expenses','fee-platform'].forEach(id=>byId(id)?.addEventListener('input',computeFee));computeFee();}
 const prompt=byId('prompt-output');byId('create-prompt')?.addEventListener('click',()=>{
  const goal=byId('prompt-goal').value.trim(),context=byId('prompt-context').value.trim(),limits=byId('prompt-constraints').value.trim(),format=byId('prompt-format').value.trim();
  const lang=meta.lang;
  const parts=lang==='ar'?['الهدف','المعطيات والسياق','القيود','المخرجات المطلوبة','اذكر الافتراضات ومواطن عدم اليقين، ولا تخترع بيانات أو مصادر غير متاحة.']:lang==='fr'?['Objectif','Contexte et données','Contraintes','Livrable attendu','Précise tes hypothèses et incertitudes. N’invente aucune donnée ni source.']:['Objective','Context and inputs','Constraints','Expected output','State assumptions and uncertainty. Do not invent data or sources.'];
  prompt.value=[`${parts[0]}: ${goal||'—'}`,`${parts[1]}: ${context||'—'}`,`${parts[2]}: ${limits||'—'}`,`${parts[3]}: ${format||'—'}`,parts[4]].join('\n\n');prompt.focus();
 });
 byId('copy-prompt')?.addEventListener('click',async()=>{if(!prompt?.value)return;try{await navigator.clipboard.writeText(prompt.value);const btn=byId('copy-prompt'),old=btn.textContent;btn.textContent=({ar:'تم النسخ ✓',fr:'Copié ✓',en:'Copied ✓'})[meta.lang];setTimeout(()=>btn.textContent=old,1800);}catch{prompt.select();}});

 // Sharing: links are assembled from the public, canonical URL without third-party tracking scripts.
 const canonical=document.querySelector('link[rel="canonical"]')?.href || location.href.split('#')[0];
 const shareUrl=encodeURIComponent(canonical), shareTitle=encodeURIComponent(document.title),shareText=encodeURIComponent(document.title+' '+canonical);
 const targets={
  WhatsApp:`https://api.whatsapp.com/send?text=${shareText}`,
  Facebook:`https://www.facebook.com/sharer/sharer.php?u=${shareUrl}`,
  X:`https://twitter.com/intent/tweet?url=${shareUrl}&text=${shareTitle}`,
  LinkedIn:`https://www.linkedin.com/sharing/share-offsite/?url=${shareUrl}`,
  Telegram:`https://t.me/share/url?url=${shareUrl}&text=${shareTitle}`,
  Pinterest:`https://pinterest.com/pin/create/button/?url=${shareUrl}&media=${encodeURIComponent(document.querySelector('meta[property="og:image"]')?.content||'')}&description=${shareTitle}`,
  Reddit:`https://www.reddit.com/submit?url=${shareUrl}&title=${shareTitle}`,
  Email:`mailto:?subject=${shareTitle}&body=${shareText}`
 };
 document.querySelectorAll('[data-share-network]').forEach(el=>{
  const href=targets[el.dataset.shareNetwork];if(href)el.href=href;
 });
 const shareLabel={ar:'شارك هذا المقال',en:'Share this article',fr:'Partager cet article'}[meta.lang]||'Share';
 document.querySelectorAll('[data-share-native]').forEach(button=>button.addEventListener('click',async()=>{
  if(navigator.share){try{await navigator.share({title:document.title,url:canonical});}catch(e){if(e.name!=='AbortError')console.warn('Share unavailable');}}
  else {try{await navigator.clipboard.writeText(canonical);button.textContent={ar:'تم نسخ الرابط ✓',en:'Link copied ✓',fr:'Lien copié ✓'}[meta.lang];}catch{button.textContent=shareLabel;}}
 }));
 document.querySelectorAll('[data-share-copy]').forEach(button=>button.addEventListener('click',async()=>{
  const previous=button.textContent;
  try{await navigator.clipboard.writeText(canonical);button.textContent={ar:'تم النسخ ✓',en:'Copied ✓',fr:'Copié ✓'}[meta.lang];setTimeout(()=>button.textContent=previous,2000);}
  catch{const tmp=document.createElement('textarea');tmp.value=canonical;document.body.appendChild(tmp);tmp.select();document.execCommand('copy');tmp.remove();button.textContent=previous;}
 }));
})();

document.querySelectorAll('.pulse-filter').forEach(btn=>btn.addEventListener('click',()=>{const wanted=btn.dataset.pulseFilter;document.querySelectorAll('.pulse-filter').forEach(b=>b.classList.toggle('current',b===btn));document.querySelectorAll('[data-pulse-topic]').forEach(card=>{card.hidden=wanted!=='all'&&card.dataset.pulseTopic!==wanted;});}));
