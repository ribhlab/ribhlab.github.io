/* RibhLab administrator-only content studio.
   Authorization uses GitHub identity and repository ADMIN permission; GitHub independently
   enforces writes. Token stays in JavaScript memory, never storage/cookies/commits. */
(()=>{'use strict';
const REPO='ribhlab/ribhlab.github.io',BRANCH='main',ROOT='https://api.github.com/repos/'+REPO,API='https://api.github.com';
const locales=['ar','en','fr'],categories={earning:'الربح الرقمي',trading:'التداول والاقتصاد',ai:'الذكاء الاصطناعي والتقنية',lifestyle:'نمط الحياة'};
const $=q=>document.querySelector(q),all=q=>Array.from(document.querySelectorAll(q));
const state={token:null,user:null,sections:null,plan:null,photos:null,resources:null,publication:null,articleFiles:[],draftFiles:[],head:null,marketPhotos:[],editingSection:null,editingArticle:null,articleBase:null,activeLang:'ar',busy:false};
const date=()=>new Date().toISOString().slice(0,10);
const slugPattern=/^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const tell=(message,error=false)=>{const node=$('#toast');node.textContent=message;node.className='toast '+(error?'error':'success');node.hidden=false;clearTimeout(tell.handle);tell.handle=setTimeout(()=>node.hidden=true,7500)};
const fail=message=>{throw new Error(message)};
const entry=(tag,cls,content)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(content!==undefined)e.textContent=content;return e};
const labelText=(s,defaultText='—')=>s===undefined||s===null||s===''?defaultText:String(s);
const parseJSON=(text,what)=>{try{return JSON.parse(text)}catch(e){fail('ملف غير صالح: '+what)}};
const decode64=s=>{const bytes=Uint8Array.from(atob(s.replace(/\s/g,'')),c=>c.charCodeAt(0));return new TextDecoder().decode(bytes)};
const json=o=>JSON.stringify(o,null,2)+'\n';
const selectedSection=()=>state.sections?.sections?.find(s=>s.id===$('#article-section').value);
const setBusy=v=>{state.busy=v;all('button').forEach(b=>{if(b.id!=='logout')b.disabled=v})};
async function request(url,method='GET',body=null){
 if(!state.token)fail('يجب تسجيل الدخول أولاً.');
 const response=await fetch(url.startsWith('https://')?url:ROOT+url,{method,headers:{Accept:'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28',Authorization:'Bearer '+state.token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store',referrerPolicy:'no-referrer'});
 if(response.status===404)return null;
 let data;try{data=await response.json()}catch{data=null}
 if(!response.ok){let msg=labelText(data?.message,response.statusText);if(response.status===401||response.status===403){msg='صلاحية الوصول غير كافية، أو رمز GitHub منتهي: '+msg}if(response.status===409||response.status===422){msg='حدث تعارض مع تحديث آخر في GitHub. حدّث البيانات ثم أعد المحاولة. '+msg}throw Error(msg)}
 return data;
}
async function readFile(path,optional=false){
 const data=await request('/contents/'+path+'?ref='+encodeURIComponent(BRANCH));
 if(!data){if(optional)return null;fail('لا يمكن العثور على '+path)}
 if(data.type!=='file'||!data.content)fail('تعذر قراءة ملف '+path);
 return parseJSON(decode64(data.content),path);
}
async function listFolder(folder){
 const data=await request('/contents/'+folder+'?ref='+encodeURIComponent(BRANCH));
 if(!data)return [];
 if(!Array.isArray(data))fail('تعذر فتح مجلد '+folder);
 return data.filter(f=>f.type==='file'&&f.name.endsWith('.json')).map(f=>({name:f.name,path:f.path}));
}
async function commit(files,message){
 // Atomic multi-file Git commit; rejects concurrent branch changes (never force-push).
 if(state.busy)fail('هناك عملية أخرى جارية.');
 setBusy(true);
 try{
  const ref=await request('/git/ref/heads/'+BRANCH);
  if(!ref?.object?.sha)fail('تعذر التحقق من رأس الفرع.');
  if(state.head!==ref.object.sha)fail('تغير المستودع منذ تحميل لوحة التحكم. حدّث البيانات قبل الحفظ حتى لا تُستبدل تحديثات أحدث.');
  const parent=ref.object.sha;
  const base=await request('/git/commits/'+encodeURIComponent(parent));
  if(!base?.tree?.sha)fail('تعذر قراءة شجرة المستودع.');
  const tree=Object.entries(files).map(([path,content])=>({path,mode:'100644',type:'blob',...(content===null?{sha:null}:{content})}));
  const createdTree=await request('/git/trees','POST',{base_tree:base.tree.sha,tree});
  const createdCommit=await request('/git/commits','POST',{message,tree:createdTree.sha,parents:[parent]});
  // Re-read the branch to avoid reporting success on a stale base.
  const current=await request('/git/ref/heads/'+BRANCH);
  if(current.object.sha!==parent)fail('وصل تعديل آخر إلى المستودع أثناء الحفظ. حدّث الصفحة وراجع التغييرات قبل المحاولة.');
  await request('/git/refs/heads/'+BRANCH,'PATCH',{sha:createdCommit.sha,force:false});
  state.head=createdCommit.sha;
  return createdCommit.sha;
 }finally{setBusy(false)}
}
async function login(token){
 state.token=token;
 try{
  const [user,repo]=await Promise.all([request(API+'/user'),request('')]);
  if(!user?.login||repo?.full_name?.toLowerCase()!==REPO.toLowerCase()||repo?.permissions?.admin!==true)fail('هذا الحساب لا يملك صلاحية Administrator على مستودع RibhLab. لن تُعرض لوحة الإدارة.');
  state.user=user;
  $('#session-user').textContent=user.login+' · Admin';$('#session-user').hidden=false;$('#logout').hidden=false;$('#login-screen').hidden=true;$('#studio').hidden=false;$('#token').value='';
  await loadAll();
  tell('تم التحقق من صلاحيات مسؤول GitHub.');
 }catch(e){logout(false);throw e}
}
function logout(show=true){
 state.token=null;state.user=null;state.sections=null;state.plan=null;state.photos=null;state.resources=null;state.publication=null;state.articleFiles=[];state.draftFiles=[];state.head=null;state.marketPhotos=[];state.editingArticle=null;state.articleBase=null;
 $('#studio').hidden=true;$('#login-screen').hidden=false;$('#session-user').hidden=true;$('#session-user').textContent='';$('#logout').hidden=true;$('#token').value='';
 if(show)tell('تم تسجيل الخروج. أُزيل مفتاح الوصول من ذاكرة الصفحة.');
}
async function loadAll(){
 const before=await request('/git/ref/heads/'+BRANCH);
 const [sections,plan,photos,resources,publication,articles,drafts,digests,feeds]=await Promise.all([
  readFile('content/sections.json'),readFile('content/editorial-plan.json'),readFile('content/licensed-photos.json'),readFile('content/platform-links.json'),readFile('content/publication-state.json',true),listFolder('content/articles'),listFolder('content/manual-drafts'),readFile('content/market-digests.json',true),readFile('content/market-feed-photos.json',true)
 ]);
 const after=await request('/git/ref/heads/'+BRANCH);
 if(before.object.sha!==after.object.sha)fail('تغيرت الملفات أثناء التحميل. حاول تحديث البيانات مجدداً.');
 if(!Array.isArray(sections.sections)||!Array.isArray(plan.sections)||!photos.articlePhotos||!resources.platforms)fail('بنية ملفات المحتوى غير متوافقة.');
 Object.assign(state,{sections,plan,photos,resources,publication:publication||{},articleFiles:articles,draftFiles:drafts,head:before.object.sha,marketPhotos:[...(digests?.items||[]).map(x=>x.photo).filter(Boolean),...Object.values(feeds?.topics||{})]});
 renderOverview();renderSections();renderArticleList();populateSections();
}
function renderOverview(){
 $('#stat-sections').textContent=state.sections.sections.length;
 $('#stat-articles').textContent=state.articleFiles.length;
 $('#stat-drafts').textContent=state.draftFiles.length;
}
function switchTab(tab){
 all('.tab').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
 all('.pane').forEach(p=>p.hidden=p.id!=='pane-'+tab);
}
function renderSections(){
 const area=$('#sections-list');area.replaceChildren();
 if(!state.sections.sections.length){area.append(entry('p','muted','لا توجد أقسام بعد.'));return}
 for(const s of state.sections.sections){
  const row=entry('div','section-entry'),info=entry('div');
  info.append(entry('strong','',s.title.ar),entry('small','',categories[s.parent]+' · '+s.publishedSlugs.length+' مقال · '+s.id));
  const button=entry('button','', 'تعديل');button.type='button';button.addEventListener('click',()=>editSection(s.id));
  row.append(info,button);area.append(row);
 }
}
function populateSections(){
 const select=$('#article-section'),old=select.value;select.replaceChildren();
 for(const s of state.sections.sections){
  const option=entry('option','',s.title.ar+' — '+categories[s.parent]);option.value=s.id;select.append(option);
 }
 if(state.sections.sections.some(s=>s.id===old))select.value=old;
}
function sectionFormData(){
 const form=$('#section-form'),f=new FormData(form),id=String(f.get('id')||'').trim(),parent=String(form.elements.namedItem('parent').value||'');
 if(!slugPattern.test(id))fail('معرّف القسم يجب أن يكون لاتينياً صغيراً ومفصولاً بشرطات.');
 if(!categories[parent])fail('المجال الرئيسي غير مدعوم.');
 const title={ar:String(f.get('titleAr')||'').trim(),en:String(f.get('titleEn')||'').trim(),fr:String(f.get('titleFr')||'').trim()};
 const description={ar:String(f.get('descAr')||'').trim(),en:String(f.get('descEn')||'').trim(),fr:String(f.get('descFr')||'').trim()};
 if(Object.values(title).some(x=>x.length<4)||Object.values(description).some(x=>x.length<20))fail('أدخل عناوين واضحة وأوصافاً مفيدة باللغات الثلاث (الوصف 20 حرفاً على الأقل).');
 const target=Number(f.get('target'));if(!Number.isInteger(target)||target<1||target>500)fail('الحد المستهدف يجب أن يكون بين 1 و500.');
 return {id,parent,title,description,targetArticles:target};
}
function newSection(){
 switchTab('sections');state.editingSection=null;const form=$('#section-form');form.reset();form.hidden=false;$('#section-id').readOnly=false;$('#section-parent').disabled=false;$('#section-form-title').textContent='إضافة قسم جديد';form.scrollIntoView({behavior:'smooth',block:'start'});
}
function editSection(id){
 switchTab('sections');const section=state.sections.sections.find(x=>x.id===id);if(!section)return;
 state.editingSection=id;const form=$('#section-form');form.hidden=false;form.reset();
 const bind=(name,value)=>{form.elements.namedItem(name).value=value};
 bind('id',section.id);bind('parent',section.parent);
 for(const l of locales){bind('title'+l[0].toUpperCase()+l.slice(1),section.title[l]);bind('desc'+l[0].toUpperCase()+l.slice(1),section.description[l])}
 bind('target',section.targetArticles);$('#section-id').readOnly=true;$('#section-parent').disabled=section.publishedSlugs.length>0;$('#section-form-title').textContent='تعديل القسم: '+section.title.ar;form.scrollIntoView({behavior:'smooth',block:'start'});
}
async function saveSection(){
 const candidate=sectionFormData(),oldId=state.editingSection;
 if(oldId&&oldId!==candidate.id)fail('لا يمكن تغيير معرّف قسم منشور.');
 const taxonomy=structuredClone(state.sections),plan=structuredClone(state.plan);
 const existing=taxonomy.sections.find(s=>s.id===candidate.id);
 const oldPlan=plan.sections.find(s=>s.id===candidate.id);
 if(!oldId&&existing)fail('معرّف القسم مستخدم مسبقاً.');
 if(oldId&&!existing)fail('القسم المراد تعديله غير موجود.');
 if(['freelance','online-business','ai-automation','mobile-apps','games-security','trading-risk','crypto-web3','gold-macro','body-care','world-recipes'].includes(candidate.id)&&candidate.targetArticles!==40)fail('الأقسام الأصلية محفوظة بهدف 40 مقالاً لكل قسم؛ لا يمكن تغيير سعتها من لوحة الإدارة.');
 if(existing&&existing.publishedSlugs.length&&candidate.parent!==existing.parent)fail('لا يمكن تغيير المجال لقسم يضم مقالات منشورة.');
 if(existing&&candidate.targetArticles<existing.publishedSlugs.length)fail('الحد الجديد أقل من عدد المقالات المنشورة بالقسم.');
 const next=existing?{...existing,...candidate}:{...candidate,publishedSlugs:[]};
 const nextPlan=oldPlan?{...oldPlan,...candidate}:{...candidate,publishedSlugs:[],ideas:[]};
 if(existing)taxonomy.sections=taxonomy.sections.map(s=>s.id===candidate.id?next:s);else taxonomy.sections.push(next);
 if(oldPlan)plan.sections=plan.sections.map(s=>s.id===candidate.id?nextPlan:s);else plan.sections.push(nextPlan);
 plan.lastReviewed=date();
 await commit({'content/sections.json':json(taxonomy),'content/editorial-plan.json':json(plan)},(existing?'Update':'Create')+' multilingual section '+candidate.id+' via RibhLab Studio');
 state.sections=taxonomy;state.plan=plan;$('#section-form').hidden=true;state.editingSection=null;renderSections();populateSections();renderOverview();tell('تم حفظ القسم، وسيظهر بعد نجاح بناء الموقع.');
}
function serializeSections(sections){
 return (sections||[]).map(s=>'## '+(s.heading||'')+'\n\n'+(s.paragraphs||[]).join('\n\n')).join('\n\n');
}
function parseSections(raw,lang){
 const sections=[];let current=null;
 for(const part of String(raw||'').split(/(?=^#{2,3}\s+)/gm)){
  const match=part.trim().match(/^#{2,3}\s+([^\n]+)\n?([\s\S]*)$/);
  if(!match)continue;
  const paragraphs=match[2].trim().split(/\n\s*\n/).map(s=>s.replace(/\s*\n\s*/g,' ').trim()).filter(Boolean);
  current={heading:match[1].trim(),paragraphs};sections.push(current);
 }
 if(sections.length<4)fail('المقال '+lang+': يجب إدخال أربعة محاور على الأقل باستخدام ## لكل عنوان.');
 if(sections.some(s=>s.heading.length<5||s.paragraphs.length<2||s.paragraphs.some(p=>p.length<75)))fail('المقال '+lang+': يتطلب كل محور عنواناً واضحاً وفقرتين مفصلتين (75 حرفاً على الأقل للفقرة).');
 return sections;
}
function ensureLanguageFields(){
 const area=$('#translation-fields');if(area.children.length)return;
 for(const lang of locales){
  const p=entry('div','lang-panel');p.dataset.lang=lang;p.hidden=lang!=='ar';p.dir=lang==='ar'?'rtl':'ltr';
  const title=entry('h4','',({ar:'النص العربي الفصيح',en:'English article',fr:'Article en français'})[lang]);p.append(title);
  const fields=[['title','عنوان المقال / Title'],['excerpt','وصف SEO قصير / Search description'],['lead','المقدمة / Opening paragraph'],['body','المحاور والفقرات / Sections']];
  for(const [key,titleText] of fields){
   const label=entry('label','',titleText);const el=key==='title'?document.createElement('input'):document.createElement('textarea');el.name=key+'_'+lang;el.required=true;if(key!=='title')el.rows=key==='body'?15:key==='lead'?4:2;if(key==='body'){el.className='long-body';el.placeholder='## عنوان المحور الأول\n\nالفقرة الأولى المفصلة...\n\nالفقرة الثانية...\n\n## عنوان المحور الثاني\n\n...'}label.append(el);p.append(label);
   if(key==='body')el.setAttribute('aria-describedby','body-help-'+lang);
  }
  const hint=entry('div','format-example','طريقة المحاور: اكتب ## قبل كل عنوان، واترك سطراً فارغاً بين الفقرات. أربعة محاور على الأقل في كل لغة.');hint.id='body-help-'+lang;p.insertBefore(hint,p.querySelector('[name=body_'+lang+']').parentElement);
  area.append(p);
 }
}
function chooseLanguage(l){
 state.activeLang=l;all('.lang-tab').forEach(x=>x.classList.toggle('active',x.dataset.lang===l));
 all('.lang-panel').forEach(x=>x.hidden=x.dataset.lang!==l);
}
function newArticle(){
 switchTab('articles');ensureLanguageFields();state.editingArticle=null;state.articleBase=null;const form=$('#article-form');form.reset();form.hidden=false;
 $('#article-slug').readOnly=false;$('#article-form-title').textContent='مقال جديد بثلاث لغات';$('#review-confirm').checked=false;chooseLanguage('ar');form.scrollIntoView({behavior:'smooth',block:'start'});
}
async function editArticle(file,kind){
 const base=kind==='draft'?await readFile('content/manual-drafts/'+file):await readFile('content/articles/'+file);
 const slug=file.replace(/\.json$/,'');
 let article,photo,sectionId;
 if(kind==='draft'){article=base.article;photo=base.photo;sectionId=base.sectionId;}else{
  article=base;
  const record=state.sections.sections.find(s=>s.publishedSlugs.includes(slug));sectionId=record?.id;
  photo=state.photos.articlePhotos[slug]||{};
 }
 if(!article||!sectionId)fail('لا يمكن فتح المقال أو العثور على القسم المرتبط به.');
 newArticle();
 state.editingArticle={slug,kind};state.articleBase=article;
 const form=$('#article-form');form.elements.namedItem('slug').value=slug;$('#article-slug').readOnly=true;
 $('#article-section').value=sectionId;form.elements.namedItem('featured').checked=!!article.featured;
 for(const lang of locales){const tr=article.translations?.[lang]||{};for(const k of ['title','excerpt','lead'])form.elements.namedItem(k+'_'+lang).value=tr[k]||'';form.elements.namedItem('body_'+lang).value=serializeSections(tr.sections);}
 form.elements.namedItem('sources').value=(article.sources||[]).map(s=>s.label+' | '+s.url).join('\n');
 for(const [field,value] of Object.entries({photoId:photo.photoId,photoSource:photo.source,photographer:photo.photographer,altAr:photo.altAr,altEn:photo.alt,altFr:photo.altFr,photoNote:photo.note}))form.elements.namedItem(field).value=value||'';
 $('#article-form-title').textContent=(kind==='draft'?'تحرير المسودة: ':'تحديث المقال المنشور: ')+slug;
 form.scrollIntoView({behavior:'smooth',block:'start'});
}
function articleFormData(draft=false){
 const form=$('#article-form'),f=new FormData(form),slug=String(f.get('slug')||'').trim(),sectionId=String(f.get('section')||'');
 if(!slugPattern.test(slug))fail('معرّف المقال غير صالح.');
 const section=state.sections.sections.find(s=>s.id===sectionId);if(!section)fail('اختر قسماً صالحاً.');
 const translations={},existing=state.articleBase;
 for(const lang of locales){
  const title=String(f.get('title_'+lang)||'').trim(),excerpt=String(f.get('excerpt_'+lang)||'').trim(),lead=String(f.get('lead_'+lang)||'').trim(),body=String(f.get('body_'+lang)||'').trim();
  if(!draft&&(title.length<15||excerpt.length<35||lead.length<75))fail('العناوين والمقدمات والوصف قصيرة في '+lang+'.');
  const old=existing?.translations?.[lang]||{};
  const parts=draft?(body?parseSectionsDraft(body):[]):parseSections(body,lang);
  const prev=old.sections||[];
  const sections=parts.map((s,i)=>({...s,...(prev[i]?.heading===s.heading&&Array.isArray(prev[i]?.bullets)?{bullets:prev[i].bullets}:{})}));
  translations[lang]={...old,title,excerpt,lead,sections};
  if(!draft){const words=[lead,...sections.flatMap(s=>s.paragraphs)].join(' ').trim().split(/\s+/).length;if(words<480)fail('المقال '+lang+' يحتوي '+words+' كلمة فقط؛ الحد الأدنى للنشر 480 كلمة مفيدة.');}
 }
 const lines=String(f.get('sources')||'').split('\n').filter(s=>s.trim());
 const sources=lines.map(line=>{const idx=line.indexOf('|');return {label:idx>=0?line.slice(0,idx).trim():'',url:idx>=0?line.slice(idx+1).trim():''}});
 if(!draft&&(sources.length<2||sources.some(s=>s.label.length<4||!/^https:\/\/[^\s/]+\/.+/.test(s.url))||new Set(sources.map(x=>x.url)).size!==sources.length))fail('أدخل مصدرين موثقين على الأقل، مع عنوان ورابط HTTPS صالح لكل مصدر.');
 const photo={photoId:String(f.get('photoId')||'').trim(),source:String(f.get('photoSource')||'').trim(),photographer:String(f.get('photographer')||'').trim(),alt:String(f.get('altEn')||'').trim(),altAr:String(f.get('altAr')||'').trim(),altFr:String(f.get('altFr')||'').trim(),license:'Unsplash License',note:String(f.get('photoNote')||'').trim()};
 if(!draft&&(!/^photo-\d+-[a-f0-9]+$/.test(photo.photoId)||!/^https:\/\/unsplash\.com\/photos\//.test(photo.source)||!photo.photographer||!photo.alt||!photo.altAr||!photo.altFr))fail('بيانات صورة Unsplash غير كاملة أو غير صالحة.');
 const article={...(existing||{}),slug,category:section.parent,date:existing?.date||date(),updated:date(),featured:!!f.get('featured'),related:existing?.related||[],sources,translations};
 return {article,photo,sectionId};
}
function parseSectionsDraft(raw){
 const parts=[];for(const part of String(raw||'').split(/(?=^#{2,3}\s+)/gm)){const m=part.trim().match(/^#{2,3}\s+([^\n]+)\n?([\s\S]*)$/);if(m)parts.push({heading:m[1].trim(),paragraphs:m[2].trim().split(/\n\s*\n/).map(p=>p.replace(/\s*\n\s*/g,' ').trim()).filter(Boolean)})}
 return parts;
}
async function saveDraft(){
 const data=articleFormData(true),slug=data.article.slug;
 if(state.articleFiles.some(f=>f.name===slug+'.json')&&state.editingArticle?.kind!=='published')fail('هذا المعرف موجود كمقال منشور؛ افتح المقال المنشور بدلاً من إنشاء مسودة بالاسم نفسه.');
 if(state.draftFiles.some(f=>f.name===slug+'.json')&&state.editingArticle?.kind!=='draft')fail('توجد مسودة بهذا المعرف. افتحها من قائمة المسودات بدلاً من استبدالها.');
 if(state.editingArticle?.kind==='published')fail('المقال منشور بالفعل، ويمكن تحديثه بزر النشر بعد المراجعة.');
 const payload={sectionId:data.sectionId,article:data.article,photo:data.photo,savedAt:new Date().toISOString(),status:'draft'};
 await commit({['content/manual-drafts/'+slug+'.json']:json(payload)},'Save unpublished multilingual draft '+slug+' via admin');
 state.editingArticle={slug,kind:'draft'};state.articleBase=data.article;$('#article-slug').readOnly=true;
 await loadAll();tell('حُفظت المسودة ولم تُنشر. تنبيه: يمكن قراءة ملف المسودة من مستودع GitHub العمومي.');
}
async function publishArticle(){
 if(!$('#review-confirm').checked)fail('يجب التأكيد بأن المراجع والصورة والترجمات تمت مراجعتها.');
 const data=articleFormData(false),slug=data.article.slug,existing=state.articleFiles.some(f=>f.name===slug+'.json');
 if(existing&&state.editingArticle?.kind!=='published')fail('المقال موجود؛ افتح نسخته المنشورة لتعديلها.');
 if(!existing&&state.editingArticle?.kind==='published')fail('بيانات المقال تغيّرت في المستودع. حدّث قبل الحفظ.');
 const originalSection=state.sections.sections.find(s=>s.publishedSlugs.includes(slug));
 if(existing&&!originalSection)fail('المقال المنشور غير مرتبط بقسم، يلزم إصلاح البيانات قبل التعديل.');
 const otherPhoto=Object.entries(state.photos.articlePhotos).find(([key,v])=>key!==slug&&(v.photoId===data.photo.photoId||v.source===data.photo.source));
 if(otherPhoto)fail('الصورة مستخدمة في مقال آخر: '+otherPhoto[0]);
 if(state.marketPhotos.some(p=>p.photoId===data.photo.photoId||p.source===data.photo.source))fail('الصورة مستخدمة بالفعل في قسم أخبار الأسواق. اختر صورة مختلفة.');
 if(!existing){
  const last=Date.parse(state.publication?.lastPublishedAt||'');
  if(Number.isFinite(last)&&Date.now()-last<25*60*1000)fail('للحفاظ على فاصل النشر التحريري، يجب مرور 25 دقيقة على آخر مقالة. احفظ المادة كمسودة ثم انشرها لاحقاً.');
 }
 const tax=structuredClone(state.sections),plan=structuredClone(state.plan),photos=structuredClone(state.photos),resources=structuredClone(state.resources);
 for(const collection of [tax,plan])for(const s of collection.sections){s.publishedSlugs=s.publishedSlugs.filter(k=>k!==slug)}
 const s=tax.sections.find(k=>k.id===data.sectionId),p=plan.sections.find(k=>k.id===data.sectionId);
 if(!s||!p)fail('الملف التحريري للقسم غير متطابق.');
 if(s.publishedSlugs.length>=s.targetArticles||p.publishedSlugs.length>=p.targetArticles)fail('القسم بلغ الحد المستهدف. عدّل سعة القسم أولاً.');
 s.publishedSlugs.push(slug);p.publishedSlugs.push(slug);
 // A manual article takes the last reserved slot, preserving near-term planned topics.
 if(!existing&&Array.isArray(p.ideas)&&p.ideas.length)p.ideas.pop();
 plan.lastReviewed=date();
 photos.articlePhotos[slug]=data.photo;photos.updated=date();
 const ids=[];
 for(let i=0;i<Math.min(data.article.sources.length,10);i++){
  const id='manual-'+slug+'-'+(i+1);
  resources.platforms[id]={name:data.article.sources[i].label,url:data.article.sources[i].url};
  ids.push(id);
 }
 resources.articleLinks[slug]=ids;resources.updated=date();
 const files={
  ['content/articles/'+slug+'.json']:json(data.article),
  'content/sections.json':json(tax),
  'content/editorial-plan.json':json(plan),
  'content/licensed-photos.json':json(photos),
  'content/platform-links.json':json(resources)
 };
 if(!existing){
  files['content/publication-state.json']=json({...state.publication,lastPublishedAt:new Date().toISOString(),lastSectionId:data.sectionId,lastSlug:slug,releaseCount:(Number(state.publication?.releaseCount)||0)+1});
 }
 if(state.editingArticle?.kind==='draft')files['content/manual-drafts/'+slug+'.json']=null;
 await commit(files,(existing?'Update':'Publish')+' reviewed trilingual article '+slug+' via RibhLab Studio');
 state.editingArticle=null;state.articleBase=null;$('#article-form').hidden=true;
 await loadAll();tell('حُفظ المقال وتصنيفه وصورته ومصادره في التزام واحد. سيظهر بعد نجاح بناء GitHub Pages.');
}
function renderArticleList(){
 const term=$('#article-search').value.trim().toLowerCase(),area=$('#articles-list');area.replaceChildren();
 const candidates=[
  ...state.draftFiles.map(f=>({name:f.name,kind:'draft'})),
  ...state.articleFiles.map(f=>({name:f.name,kind:'published'}))
 ].filter(x=>x.name.toLowerCase().includes(term)).sort((a,b)=>a.name.localeCompare(b.name));
 if(!candidates.length){area.append(entry('p','muted',term?'لا نتائج مطابقة.':'لا توجد مقالات.'));return}
 for(const a of candidates.slice(0,120)){
  const row=entry('div','article-entry'),info=entry('div'),label=a.name.replace(/\.json$/,'');
  info.append(entry('strong','',label),entry('small','',a.kind==='draft'?'مسودة غير منشورة':'مقال منشور'));
  const btn=entry('button','',a.kind==='draft'?'تحرير المسودة':'تعديل');btn.type='button';btn.addEventListener('click',()=>editArticle(a.name,a.kind).catch(e=>tell(e.message,true)));
  row.append(info,btn);area.append(row);
 }
 if(candidates.length>120)area.append(entry('p','muted','تظهر أول 120 نتيجة. استعمل البحث لتحديد المقال المطلوب.'));
}
function bindEvents(){
 $('#signin-form').addEventListener('submit',async e=>{e.preventDefault();const t=$('#token').value.trim();if(!t)return;$('#signin-button').disabled=true;try{await login(t)}catch(err){tell('تعذر الدخول: '+err.message,true)}finally{$('#signin-button').disabled=false}});
 $('#logout').addEventListener('click',()=>logout());
 $('#reload').addEventListener('click',async()=>{try{await loadAll();tell('تم تحديث الملفات من GitHub.')}catch(e){tell(e.message,true)}});
 all('.tab').forEach(b=>b.addEventListener('click',()=>switchTab(b.dataset.tab)));
 all('[data-action=new-section]').forEach(b=>b.addEventListener('click',newSection));
 all('[data-action=new-article]').forEach(b=>b.addEventListener('click',newArticle));
 $('#new-section').addEventListener('click',newSection);$('#new-article').addEventListener('click',newArticle);
 $('#cancel-section').addEventListener('click',()=>{$('#section-form').hidden=true;state.editingSection=null});
 $('#cancel-article').addEventListener('click',()=>{$('#article-form').hidden=true;state.editingArticle=null;state.articleBase=null});
 $('#section-form').addEventListener('submit',async e=>{e.preventDefault();try{await saveSection()}catch(err){tell(err.message,true)}});
 $('#article-form').addEventListener('submit',async e=>{e.preventDefault();try{await publishArticle()}catch(err){tell(err.message,true)}});
 $('#save-draft').addEventListener('click',async()=>{try{await saveDraft()}catch(err){tell(err.message,true)}});
 $('#article-search').addEventListener('input',renderArticleList);
 all('.lang-tab').forEach(b=>b.addEventListener('click',()=>chooseLanguage(b.dataset.lang)));
 window.addEventListener('beforeunload',()=>{state.token=null});
}
bindEvents();
})();
