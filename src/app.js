(()=>{
 'use strict';
 const byId=id=>document.getElementById(id);
 // Editorial photography fallback: a failed external image never leaves a broken article or homepage card.
 const restoreImage=img=>{
  if(!img?.matches?.('img.editorial-photo[data-fallback-src]'))return;
  const fallback=img.getAttribute('data-fallback-src');
  if(fallback&&img.getAttribute('src')!==fallback){img.setAttribute('src',fallback);img.classList.add('photo-fallback-active');}
 };
 document.addEventListener('error',e=>restoreImage(e.target),true);
 document.querySelectorAll('img.editorial-photo[data-fallback-src]').forEach(img=>{
  if(img.complete&&img.naturalWidth===0)restoreImage(img);
 });

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

 // Scenario calculators use visitor-entered assumptions, never scraped or invented payout data.
 const validate=(ids)=>ids.every(id=>byId(id)&&Number.isFinite(n(id))&&n(id)>=0);
 const putCalc=(id,num)=>{const e=byId(id);if(e)e.textContent=Number.isFinite(num)?nice(num):'—';};
 const calculateMonetization=()=>{
  if(validate(['calc-page-visits','calc-page-depth','calc-page-rpm'])){
   putCalc('calc-page-result',n('calc-page-visits')*n('calc-page-depth')*n('calc-page-rpm')/1000);
  }
  const affiliateIds=['calc-aff-visits','calc-aff-ctr','calc-aff-conv','calc-aff-value','calc-aff-rate'];
  if(validate(affiliateIds)&&n('calc-aff-ctr')<=100&&n('calc-aff-conv')<=100&&n('calc-aff-rate')<=100){
   putCalc('calc-aff-result',n('calc-aff-visits')*n('calc-aff-ctr')/100*n('calc-aff-conv')/100*n('calc-aff-value')*n('calc-aff-rate')/100);
  }else putCalc('calc-aff-result',NaN);
  if(validate(['calc-game-dau','calc-game-ads','calc-game-ecpm','calc-game-costs'])){
   putCalc('calc-game-result',n('calc-game-dau')*n('calc-game-ads')*30*n('calc-game-ecpm')/1000-n('calc-game-costs'));
  }
 };
 if(byId('calc-page-result')){
  ['calc-page-visits','calc-page-depth','calc-page-rpm','calc-aff-visits','calc-aff-ctr','calc-aff-conv','calc-aff-value','calc-aff-rate','calc-game-dau','calc-game-ads','calc-game-ecpm','calc-game-costs'].forEach(id=>byId(id)?.addEventListener('input',calculateMonetization));
  calculateMonetization();
 }
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

 // Real measurement: only executed after the visitor clicks Start. We do not infer speed from browser hints.
 const speedStart=byId('speed-start'),speedStop=byId('speed-stop'),speedStatus=byId('speed-status');
 let speedController=null;
 const speedMessages={
  ar:{running:'الاختبار جارٍ: نقل بيانات حقيقية...',done:'اكتمل القياس. النتيجة لحظة الاختبار وقد تختلف عند التكرار.',failed:'تعذر قياس الاتصال: قد تمنع الشبكة أو المتصفح خدمة الاختبار. لم نعرض أرقاماً افتراضية.',stopped:'توقف الاختبار بطلبك.'},
  en:{running:'Measuring using real network traffic...',done:'Measurement completed. Repeat to compare connection variability.',failed:'Measurement unavailable: browser or network may block the endpoint. No estimated speed is displayed.',stopped:'Test stopped.'},
  fr:{running:'Mesure du trafic réseau réel...',done:'Test terminé. Les résultats varient selon le moment et la connexion.',failed:'Mesure indisponible : accès aux serveurs bloqué ou problème réseau. Aucun débit fictif affiché.',stopped:'Test arrêté.'}
 }[meta.lang]||{running:'Testing...',done:'Done',failed:'Connection test unavailable',stopped:'Stopped'};
 const putSpeed=(key,value)=>{const el=byId('speed-'+key);if(el)el.textContent=value;};
 const calcMbps=(bytes,ms)=>ms>0?(bytes*8/(ms/1000)/1000000):NaN;
 const request=async(url,options,controller)=>{
  const start=performance.now();
  const response=await fetch(url,{...options,cache:'no-store',signal:controller.signal});
  if(!response.ok)throw new Error('network test HTTP '+response.status);
  const body=await response.arrayBuffer();
  return {ms:performance.now()-start,bytes:body.byteLength};
 };
 speedStop?.addEventListener('click',()=>speedController?.abort());
 speedStart?.addEventListener('click',async()=>{
  if(speedController)return;
  speedController=new AbortController();
  speedStart.disabled=true;speedStop.disabled=false;speedStatus.textContent=speedMessages.running;
  for(const k of ['latency','download','upload'])putSpeed(k,'—');
  const controller=speedController;
  const base='https://speed.cloudflare.com';
  try{
   const latency=[];
   for(let n=0;n<3;n++){const p=await request(base+'/__down?bytes=0&r='+Date.now()+'-'+n,{},controller);latency.push(p.ms);}
   latency.sort((a,b)=>a-b);putSpeed('latency',nice(latency[1]));
   let downloaded=0,downloadTime=0;
   for(let n=0;n<2;n++){const p=await request(base+'/__down?bytes=1000000&r='+Date.now()+'-'+n,{},controller);if(p.bytes<1000000)throw new Error('incomplete measurement');downloaded+=p.bytes;downloadTime+=p.ms;}
   putSpeed('download',nice(calcMbps(downloaded,downloadTime)));
   const data=new Uint8Array(500000); // fixed-size neutral payload; consent is required before sending.
   let uploadBytes=0,uploadTime=0;
   for(let n=0;n<2;n++){const start=performance.now();const response=await fetch(base+'/__up?r='+Date.now()+'-'+n,{method:'POST',body:data,cache:'no-store',signal:controller.signal});if(!response.ok)throw new Error('upload HTTP '+response.status);await response.arrayBuffer();uploadTime+=performance.now()-start;uploadBytes+=data.byteLength;}
   putSpeed('upload',nice(calcMbps(uploadBytes,uploadTime)));
   speedStatus.textContent=speedMessages.done;
  }catch(e){speedStatus.textContent=e.name==='AbortError'?speedMessages.stopped:speedMessages.failed; if(e.name!=='AbortError')console.warn('Speed test unavailable',e);}
  finally{if(speedController===controller)speedController=null;speedStart.disabled=false;speedStop.disabled=true;}
 });
})();


// Standalone text and developer utilities run entirely on the visitor's device.
const wordInput=byId('words-input');
if(wordInput){
 const recount=()=>{
  const v=wordInput.value;
  let words=0;
  if(v.trim()){
   if(typeof Intl.Segmenter==='function'){
    const seg=new Intl.Segmenter(meta.lang||'en',{granularity:'word'});
    words=Array.from(seg.segment(v)).filter(x=>x.isWordLike).length;
   }else words=v.trim().split(/\s+/u).length;
  }
  byId('words-count').textContent=String(words);
  byId('characters-count').textContent=String(Array.from(v).length);
  byId('lines-count').textContent=String(v?v.split(/\r\n|\r|\n/u).length:0);
 };
 wordInput.addEventListener('input',recount);
 recount();
}
const jsonIn=byId('json-input'),jsonOut=byId('json-output'),jsonStatus=byId('json-status');
byId('json-format')?.addEventListener('click',()=>{
 try{
  if(!jsonIn.value.trim())throw new Error('Empty input');
  jsonOut.value=JSON.stringify(JSON.parse(jsonIn.value),null,2);
  jsonStatus.textContent=({ar:'✓ JSON صحيح',en:'✓ Valid JSON',fr:'✓ JSON valide'})[meta.lang];
 }catch(error){
  jsonOut.value='';
  const bad=({ar:'JSON غير صحيح',en:'Invalid JSON',fr:'JSON non valide'})[meta.lang];
  jsonStatus.textContent=bad+': '+error.message;
 }
});
byId('json-copy')?.addEventListener('click',async()=>{
 if(!jsonOut?.value)return;
 try{await navigator.clipboard.writeText(jsonOut.value);jsonStatus.textContent=({ar:'✓ تم النسخ',en:'✓ Copied',fr:'✓ Copié'})[meta.lang];}
 catch{jsonOut.focus();jsonOut.select();jsonStatus.textContent=({ar:'حدد النص وانسخه',en:'Select and copy manually',fr:'Sélectionnez puis copiez'})[meta.lang];}
});

// Position sizing is intentionally expressed in units, not ambiguous broker lot sizes.
const positionOutput=byId('position-units');
if(positionOutput){
 const recompute=()=>{
  const capital=n('position-capital'),risk=n('position-risk'),entry=n('position-entry'),stop=n('position-stop'),multiplier=n('position-multiplier');
  const inputs=[capital,risk,entry,stop,multiplier];
  const valid=inputs.every(Number.isFinite)&&capital>0&&risk>0&&risk<=100&&entry>0&&stop>0&&multiplier>0&&entry!==stop;
  const maxLoss=valid?capital*risk/100:NaN;
  byId('position-loss').textContent=Number.isFinite(maxLoss)?nice(maxLoss):'—';
  positionOutput.textContent=valid?nice(maxLoss/(Math.abs(entry-stop)*multiplier)):'—';
 };
 ['position-capital','position-risk','position-entry','position-stop','position-multiplier'].forEach(id=>byId(id)?.addEventListener('input',recompute));
 recompute();
}

// Safe in-browser invoice, CV and report preview. No network request, no AI or paid service.
const studioPreview=byId('studio-preview');
if(studioPreview){
 const t={
  ar:{invoice:'فاتورة تجريبية',cv:'السيرة الذاتية',report:'تقرير',issued:'الجهة المصدرة',client:'العميل',qty:'الكمية',price:'الثمن',tax:'الضريبة',total:'المجموع',role:'المسمى المهني',desc:'التفاصيل',save:'تم إنشاء المعاينة محلياً',invalid:'تحقق من الكمية والثمن والضريبة'},
  en:{invoice:'Draft invoice',cv:'Curriculum vitae',report:'Report',issued:'Issuer',client:'Customer',qty:'Quantity',price:'Unit price',tax:'Tax',total:'Total',role:'Professional title',desc:'Details',save:'Preview generated locally',invalid:'Check quantity, price and tax'},
  fr:{invoice:'Facture brouillon',cv:'Curriculum vitae',report:'Rapport',issued:'Émetteur',client:'Client',qty:'Quantité',price:'Prix unitaire',tax:'Taxe',total:'Total',role:'Fonction',desc:'Détails',save:'Aperçu créé localement',invalid:'Vérifiez la quantité, le prix et la taxe'}
 }[meta.lang];
 const get=id=>byId(id)?.value.trim()||'';
 const el=(tag,content,cls)=>{
  const node=document.createElement(tag);
  node.textContent=content;
  if(cls)node.className=cls;
  studioPreview.appendChild(node);
  return node;
 };
 const render=()=>{
  studioPreview.replaceChildren();
  const kind=get('studio-type'),name=get('studio-name'),client=get('studio-client'),txt=get('studio-text');
  const qty=Number(get('studio-qty')),price=Number(get('studio-price')),rate=Number(get('studio-tax'));
  if(kind==='invoice'&&(!Number.isFinite(qty)||!Number.isFinite(price)||!Number.isFinite(rate)||qty<=0||price<0||rate<0||rate>100)){
   byId('studio-status').textContent=t.invalid;return false;
  }
  el('h2',kind==='cv'?t.cv:kind==='report'?t.report:t.invoice);
  if(kind==='invoice'){
   el('p',t.issued+': '+(name||'—'));
   el('p',t.client+': '+(client||'—'));
   el('p',txt||'—','studio-description');
   const currency=get('studio-currency')||'MAD';
   el('p',t.qty+': '+qty+' · '+t.price+': '+price.toFixed(2)+' '+currency);
   const subtotal=qty*price,total=subtotal*(1+rate/100);
   el('p',t.tax+': '+rate.toFixed(2)+'%');
   el('strong',t.total+': '+total.toFixed(2)+' '+currency,'studio-total');
  }else if(kind==='cv'){
   el('h3',name||'—');el('p',t.role+': '+(client||'—'));el('p',txt||'—','studio-description');
  }else{
   el('h3',client||'—');el('p',t.issued+': '+(name||'—'));el('p',txt||'—','studio-description');
  }
  byId('studio-status').textContent=t.save;
  return true;
 };
 byId('studio-render')?.addEventListener('click',render);
 byId('studio-print')?.addEventListener('click',()=>{if(render())window.print();});
 byId('studio-csv')?.addEventListener('click',()=>{
  if(get('studio-type')!=='invoice'){byId('studio-status').textContent=({ar:'CSV مخصص للفواتير فقط',en:'CSV export is for invoices only',fr:'CSV réservé aux factures'})[meta.lang];return;}
  if(!render())return;
  const qty=Number(get('studio-qty')),price=Number(get('studio-price')),tax=Number(get('studio-tax')),cur=get('studio-currency');
  const safe=v=>{const raw=String(v);const guarded=/^[=+\-@\t\r]/.test(raw)?"'"+raw:raw;return '"'+guarded.replace(/"/g,'""')+'"';};
  const rows=[['Issuer',get('studio-name')],['Customer',get('studio-client')],['Description',get('studio-text')],['Quantity',qty],['Unit price',price],['Tax percent',tax],['Currency',cur],['Total',(qty*price*(1+tax/100)).toFixed(2)]];
  const data='\uFEFF'+rows.map(row=>row.map(safe).join(',')).join('\r\n');
  const blob=new Blob([data],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob),link=document.createElement('a');
  link.href=url;link.download='ribhlab-invoice.csv';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 });
 ['studio-type','studio-name','studio-client','studio-text','studio-qty','studio-price','studio-tax','studio-currency'].forEach(id=>byId(id)?.addEventListener('input',render));
 render();
}

document.querySelectorAll('.pulse-filter').forEach(btn=>btn.addEventListener('click',()=>{const wanted=btn.dataset.pulseFilter;document.querySelectorAll('.pulse-filter').forEach(b=>b.classList.toggle('current',b===btn));document.querySelectorAll('[data-pulse-topic]').forEach(card=>{card.hidden=wanted!=='all'&&card.dataset.pulseTopic!==wanted;});}));
