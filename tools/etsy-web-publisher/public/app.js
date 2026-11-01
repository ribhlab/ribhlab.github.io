'use strict';
const $=id=>document.getElementById(id);
const state={job:crypto.randomUUID(),images:[],files:[],uploaded:new Map(),busy:false};
const api=async (path,body)=>{
 const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),credentials:'same-origin'});
 const d=await res.json().catch(()=>({}));if(!res.ok)throw Error(d.error||'خطأ في الاتصال');return d;
};
const show=(id,yes)=>$(id).classList.toggle('hidden',!yes);
const message=(id,txt)=>$(id).textContent=txt;
async function refresh(){
 try{
  const r=await fetch('/api/auth',{cache:'no-store'}).then(r=>r.json());
  show('loginPanel',!r.authenticated);show('connectPanel',r.authenticated&&!r.connected);show('workspace',r.authenticated&&r.connected);
  if(r.connected)message('shopInfo','✅ متجر Etsy متصل #'+r.shop_id);
 }catch{show('loginPanel',true);message('loginStatus','تعذر فحص الاتصال بالخادم.');}
}
$('loginBtn').onclick=async()=>{try{message('loginStatus','جاري الدخول…');await api('/api/auth',{action:'login',password:$('password').value});$('password').value='';message('loginStatus','');await refresh();}catch(e){message('loginStatus',e.message)}};
$('password').addEventListener('keydown',e=>{if(e.key==='Enter')$('loginBtn').click()});
$('logoutBtn').onclick=async()=>{try{await api('/api/auth',{action:'logout'});await refresh();}catch(e){alert(e.message)}};
$('connectBtn').onclick=async()=>{
 try{message('connectStatus','جاري تجهيز الاتصال…');const r=await api('/api/connect-start',{keystring:$('keystring').value,sharedSecret:$('sharedSecret').value});location.assign(r.url);}catch(e){message('connectStatus',e.message)}
};
if(location.search.includes('connected=1'))history.replaceState({},'',location.pathname);
if(location.search.includes('error=')){const p=new URLSearchParams(location.search);setTimeout(()=>message('connectStatus','فشل الربط ('+(p.get('error')||'unknown')+'). تقدر تعاود التجربة.'),500);history.replaceState({},'',location.pathname)}
function fileSize(n){return (n/1048576).toFixed(2)+' MB';}
function renderFiles(){
 const target=$('fileSummary');target.replaceChildren();
 const add=(file,kind)=>{
  const box=document.createElement('div');box.className='filechip';
  if(kind==='image'){
   const img=document.createElement('img');img.alt='Preview';const u=URL.createObjectURL(file);img.src=u;img.onload=()=>URL.revokeObjectURL(u);box.append(img);
  }else{const sign=document.createElement('span');sign.textContent='📄';box.append(sign)}
  const label=document.createElement('strong');label.textContent=file.name+' · '+fileSize(file.size);box.append(label);
  const del=document.createElement('button');del.textContent='×';del.title='حذف';del.onclick=()=>{state[kind==='image'?'images':'files']=state[kind==='image'?'images':'files'].filter(x=>x!==file);renderFiles()};box.append(del);
  target.append(box);
 };
 state.images.forEach(f=>add(f,'image'));state.files.forEach(f=>add(f,'file'));
}
function chooseFiles(id,kind,max,ext){
 const input=$(id),box=$(id==='images'?'dropImages':'dropFiles');
 const handle=list=>{
  const files=Array.from(list),allowed=files.filter(file=>file.size<=20971520&&file.size>0&&ext.some(x=>file.name.toLowerCase().endsWith(x)));
  const arr=state[kind];for(const f of allowed){if(arr.length>=max)break;if(!arr.some(old=>old.name===f.name&&old.size===f.size))arr.push(f)}
  if(allowed.length!==files.length)alert('كاين ملف كبير من 20MB أو بصيغة غير مسموحة.');
  renderFiles();
  if(!$('title').value && state.files.length){$('title').value=state.files[0].name.replace(/\.[^.]+$/,'').replace(/[-_]/g,' ').replace(/\s+/g,' ').slice(0,140)}
 };
 input.onchange=e=>{handle(input.files);input.value=''};box.onclick=e=>{if(e.target.tagName!=='INPUT')input.click()};box.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();input.click()}};
 box.ondragover=e=>{e.preventDefault();box.classList.add('dragover')};box.ondragleave=()=>box.classList.remove('dragover');box.ondrop=e=>{e.preventDefault();box.classList.remove('dragover');handle(e.dataTransfer.files)};
}
chooseFiles('images','images',20,['.jpg','.jpeg','.png','.gif']);
chooseFiles('files','files',5,['.pdf','.zip','.jpg','.jpeg','.png','.gif','.svg','.eps','.txt','.doc','.docx','.psd','.ai']);
$('taxonomy').onchange=()=>show('customTaxonomy',$('taxonomy').value==='custom');
$('autoTags').onclick=()=>{
 const base=['printable wall art','digital prints','instant download','wall art decor','modern wall decor','gallery wall','living room art','home decor print','digital art print','gift for new home','printable poster','minimalist art','boho wall decor'];
 const title=$('title').value.toLowerCase();
 if(title.includes('abstract'))base[12]='abstract wall art';
 if(title.includes('floral'))base[12]='floral wall art';
 if(title.includes('nursery'))base[12]='nursery wall art';
 $('tags').value=base.join(', ');
};
$('autoDesc').onclick=()=>{
 const name=$('title').value.trim()||'Printable Wall Art';
 const fileText=state.files.map(x=>x.name).join(', ')||'Your digital artwork files';
 $('description').value=`${name}\n\nINSTANT DIGITAL DOWNLOAD — NO PHYSICAL ITEM WILL BE SHIPPED.\n\nWHAT YOU RECEIVE\n${fileText}\n\nHOW TO USE\n1. Purchase the listing on Etsy.\n2. Download the digital files from your Etsy account.\n3. Print at home or with a professional print shop using the intended size and paper.\n\nIMPORTANT\nThe frame and room mockups are for display only and are not included. Colors can vary by monitor and printer settings.\n\nPlease review the file dimensions and the artwork preview before purchasing.`;
};
$('jsonImport').onchange=async(e)=>{
 const f=e.target.files?.[0];if(!f)return;
 try{const m=JSON.parse(await f.text());
  if(m.title)$('title').value=String(m.title).slice(0,140);
  if(m.description)$('description').value=String(m.description);
  if(m.price)$('price').value=m.price;
  if(Array.isArray(m.tags))$('tags').value=m.tags.join(', ');
  if(m.taxonomy_id){if(String(m.taxonomy_id)!=='2078'){$('taxonomy').value='custom';$('customTaxonomy').value=m.taxonomy_id;show('customTaxonomy',true)}}
  alert('تم استيراد بيانات listing.json. باقي خاصك تختار الصور والملفات بنفسك.');
 }catch{alert('تعذر قراءة listing.json')}e.target.value='';
};
const markProgress=(text,pct,detail='')=>{show('progressBox',true);message('progressLabel',text);message('progressPercent',pct+'%');$('bar').style.width=pct+'%';message('progressDetail',detail)};
async function uploadFile(file,kind,index,total){
 const key=kind+':'+file.name+':'+file.size;
 if(state.uploaded.has(key))return state.uploaded.get(key);
 const started=await api('/api/upload?action=start',{job:state.job,kind,name:file.name,size:file.size});
 const paths=[];
 for(let i=0;i<started.parts;i++){
  const chunk=file.slice(i*started.chunkSize,Math.min(file.size,(i+1)*started.chunkSize));
  const r=await fetch('/api/upload?action=part&index='+i,{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Upload-Ticket':started.ticket},body:chunk});
  const d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'فشل رفع جزء من '+file.name);
  paths.push(d.path);
  const done=(index+(i+1)/started.parts)/total;
  markProgress('رفع الملفات بشكل خاص…',Math.round(done*75),file.name+' · جزء '+(i+1)+'/'+started.parts);
 }
 const r=await fetch('/api/upload?action=finish',{method:'POST',headers:{'Content-Type':'application/json','X-Upload-Ticket':started.ticket},body:JSON.stringify({paths})});
 const data=await r.json().catch(()=>({}));if(!r.ok)throw Error(data.error||'فشل التحقق من الملف');
 state.uploaded.set(key,data.manifest);
 return data.manifest;
}
async function submit(live){
 if(state.busy)return;
 if(!state.images.length||!state.files.length){alert('اختار صورة إعلان واحدة وملف للمشتري واحد على الأقل.');return;}
 const title=$('title').value.trim(),description=$('description').value.trim(),price=Number($('price').value),taxonomy=$('taxonomy').value==='custom'?Number($('customTaxonomy').value):2078;
 if(title.length<3||!description||!(price>0)||!(taxonomy>0)){alert('عمر العنوان والوصف والثمن والتصنيف.');return;}
 const tags=$('tags').value.trim();const arr=tags.split(',').map(t=>t.trim()).filter(Boolean);
 if(arr.length>13||arr.some(x=>x.length>20)){alert('13 كلمة مفتاحية على الأكثر، كل واحدة 20 حرفاً أو أقل.');return;}
 if(live&&!confirm('واش كاتأكد نشر المنتج LIVE في Etsy؟ قد تحتسب Etsy رسوم الإدراج العادية.'))return;
 state.busy=true;$('draftBtn').disabled=true;$('publishBtn').disabled=true;message('publishStatus','');show('result',false);
 try{
  const groups=[...state.images.map(f=>({file:f,kind:'image'})),...state.files.map(f=>({file:f,kind:'file'}))];
  const imgs=[],files=[];
  for(let i=0;i<groups.length;i++){
   const item=groups[i],m=await uploadFile(item.file,item.kind,i,groups.length);
   (item.kind==='image'?imgs:files).push(m);
  }
  markProgress('نرسل الإعلان إلى Etsy…',86,'إنشاء مسودة Etsy ورفع المحتوى');
  const payload={job:state.job,title,description,price,taxonomy,tags,images:imgs,files,live};
  const r=await api('/api/publish',payload);
  markProgress('مكتمل',100,'');
  const result=$('result');result.replaceChildren();const h=document.createElement('strong');h.textContent=r.status==='active'?'✅ المنتج تنشر فـ Etsy!':'✅ المسودة توجدت فـ Etsy!';result.append(h);
  const p=document.createElement('p');p.textContent='Listing ID: '+r.listingId;result.append(p);
  const link=document.createElement('a');link.href=r.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='فتح الإعلان في Etsy ↗';result.append(link);show('result',true);
  if(r.status==='active'){
   state.job=crypto.randomUUID();state.uploaded.clear();
  }
 }catch(e){message('publishStatus',e.message||'فشل الإرسال، حاول بنفس المنتج مجدداً.');}
 finally{state.busy=false;$('draftBtn').disabled=false;$('publishBtn').disabled=false;}
}
$('draftBtn').onclick=()=>submit(false);$('publishBtn').onclick=()=>submit(true);
refresh();
