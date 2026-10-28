/**
 * RibhLab reviewed editorial queue.
 * Releases at most one fully sourced trilingual article after >=25 minutes.
 * Never uses generated filler or invents source/photo provenance.
 */
import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd();
const content=path.join(root,'content');
const articlesDir=path.join(content,'articles');
const queueDir=path.join(content,'reviewed-queue');
const stateFile=path.join(content,'publication-state.json');
const MIN_INTERVAL_MS=25*60*1000;
const locales=['ar','en','fr'];
const allowedCategories=new Set(['earning','trading','ai','lifestyle']);
const fail=message=>{throw new Error('RibhLab editorial publishing gate: '+message)};
const readJSON=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const writeJSON=(file,data)=>fs.writeFileSync(file,JSON.stringify(data,null,2)+'\n');
const now=new Date();
const today=now.toISOString().slice(0,10);
const state=fs.existsSync(stateFile)?readJSON(stateFile):{lastPublishedAt:null,lastSectionId:null,releaseCount:0};
const last=state.lastPublishedAt?Date.parse(state.lastPublishedAt):0;
if(last&&!Number.isFinite(last))fail('Invalid lastPublishedAt');
if(last&&now.getTime()-last<MIN_INTERVAL_MS){
 console.log('QUEUE_WAIT: interval not reached. No publication this run.');
 process.exit(0);
}
if(!fs.existsSync(queueDir)){
 console.log('QUEUE_EMPTY: no vetted editorial queue directory');
 process.exit(0);
}
const queueFiles=fs.readdirSync(queueDir).filter(name=>name.endsWith('.json')).sort();
if(!queueFiles.length){
 console.log('QUEUE_EMPTY: vetted articles are needed before next publication');
 process.exit(0);
}
const bundles=queueFiles.map(filename=>({filename,path:path.join(queueDir,filename),...readJSON(path.join(queueDir,filename))}));
const candidate=bundles.find(b=>b.sectionId!==state.lastSectionId)||bundles[0];
const {article,photo,resourceIds,sectionId,review}=candidate;
if(!article?.slug||!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(article.slug))fail('Invalid article slug');
if(!allowedCategories.has(article.category))fail('Invalid article category');
const reviewMs=Date.parse((review?.checkedAt||'')+'T00:00:00Z');
if(!review||review.ready!==true||!Number.isFinite(reviewMs)||reviewMs>now.getTime()||now.getTime()-reviewMs>7*24*60*60*1000||review.sourcesIndependentlyChecked!==true||review.translationsReviewed!==true||review.photoProvenanceChecked!==true)fail('Review signoff incomplete or older than seven days for '+article.slug);
if(!Array.isArray(article.sources)||article.sources.length<2||article.sources.some(s=>!s.label||!/^https:\/\/[^/]+\/.+/.test(s.url)))fail('At least two specific HTTPS primary references required for '+article.slug);
for(const lang of locales){
 const tr=article.translations?.[lang];
 if(!tr?.title||!tr?.excerpt||!tr?.lead||!Array.isArray(tr.sections)||tr.sections.length<4)fail('Missing fully edited '+lang+' translation');
 const paragraphs=[tr.lead,...tr.sections.flatMap(s=>s.paragraphs||[])];
 if(tr.sections.some(s=>!s.heading||!Array.isArray(s.paragraphs)||s.paragraphs.length<2))fail('Thin or empty sections in '+lang);
 if(paragraphs.some(s=>typeof s!=='string'||s.length<75))fail('Paragraphs lack useful explanatory detail in '+lang);
 const words=paragraphs.join(' ').trim().split(/\s+/).length;
 if(words<480)fail('Too short for RibhLab editorial standard in '+lang+' ('+words+' words)');
}
if(!photo||!/^photo-\d+-[a-f0-9]+$/.test(photo.photoId||'')||!/^https:\/\/unsplash\.com\/photos\//.test(photo.source||'')||!photo.photographer||!photo.alt||!photo.altAr||!photo.altFr||photo.license!=='Unsplash License')fail('Unlicensed photo or missing image metadata');
if(!Array.isArray(resourceIds)||resourceIds.length<2||new Set(resourceIds).size!==resourceIds.length)fail('Two unique credible resource links needed');

// Reject near-duplicate structure and phrasing, not just duplicate URLs/slugs.
// This is a mechanical similarity test, NOT an external plagiarism scan.
const normalized=x=>String(x||'').toLocaleLowerCase().normalize('NFKC').replace(/[\u064b-\u065f]/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim();
const tokenSet=x=>new Set(normalized(x).split(' ').filter(w=>w.length>=3));
const fiveGrams=x=>{
 const w=normalized(x).split(' ').filter(Boolean),sets=new Set();
 for(let i=0;i+4<w.length;i++)sets.add(w.slice(i,i+5).join(' '));
 return sets;
};
const overlap=(a,b)=>{
 if(!a.size||!b.size)return 0;
 let common=0;
 for(const key of a)if(b.has(key))common++;
 return common/Math.min(a.size,b.size);
};
const articleText=(a,lang)=>{
 const t=a.translations?.[lang];
 return t?[t.lead,...(t.sections||[]).flatMap(k=>[k.heading,...(k.paragraphs||[])])].join(' '):'';
};
const titleWords=tokenSet(article.translations.ar.title);
for(const filename of fs.readdirSync(articlesDir).filter(name=>name.endsWith('.json'))){
 const old=readJSON(path.join(articlesDir,filename));
 if(normalized(old.translations?.ar?.title)===normalized(article.translations.ar.title))fail('Duplicate article title: '+old.slug);
 if(overlap(titleWords,tokenSet(old.translations?.ar?.title))>.88)fail('Near-duplicate topic/title versus '+old.slug);
 for(const lang of locales){
  if(overlap(fiveGrams(articleText(article,lang)),fiveGrams(articleText(old,lang)))>.33)fail('Near-duplicate '+lang+' text versus '+old.slug);
 }
}
for(const other of bundles){
 if(other===candidate||!other.article)continue;
 if(other.article.slug===article.slug||normalized(other.article.translations?.ar?.title)===normalized(article.translations.ar.title))fail('Duplicate reviewed queue item '+other.filename);
 for(const lang of locales){
  if(overlap(fiveGrams(articleText(article,lang)),fiveGrams(articleText(other.article,lang)))>.33)fail('Similar queued article content '+other.filename+' ('+lang+')');
 }
}

const articlePath=path.join(articlesDir,article.slug+'.json');
if(fs.existsSync(articlePath))fail('Article already exists: '+article.slug);
const tax=readJSON(path.join(content,'sections.json'));
const plan=readJSON(path.join(content,'editorial-plan.json'));
const photos=readJSON(path.join(content,'licensed-photos.json'));
const resources=readJSON(path.join(content,'platform-links.json'));
const target=tax.sections.find(s=>s.id===sectionId);
const planned=plan.sections.find(s=>s.id===sectionId);
if(!target||!planned||target.parent!==article.category||planned.parent!==article.category||!planned.ideas?.length)fail('Invalid/filled editorial section '+sectionId);
if(target.publishedSlugs.includes(article.slug)||planned.publishedSlugs.includes(article.slug))fail('Duplicate taxonomy slug');
for(const x of Object.values(photos.articlePhotos)){
 if(x.photoId===photo.photoId||x.source===photo.source)fail('Photo reused from another article');
}
const digests=readJSON(path.join(content,'market-digests.json')).items;
if(digests.some(d=>d.photo?.photoId===photo.photoId||d.photo?.source===photo.source))fail('Photo reused from Market Pulse');
const feedPhotos=readJSON(path.join(content,'market-feed-photos.json')).topics;
if(Object.values(feedPhotos).some(p=>p.photoId===photo.photoId||p.source===photo.source))fail('Photo reused from market headlines');
for(const id of resourceIds)if(!resources.platforms[id])fail('Unknown reference '+id);
if(resourceIds.some(id=>!/^https:\/\//.test(resources.platforms[id].url)))fail('Insecure resource URL');
const finalArticle={...article,date:today,updated:today,featured:false};
target.publishedSlugs.push(article.slug);
planned.publishedSlugs.push(article.slug);
planned.ideas.shift();
plan.lastReviewed=today;
photos.articlePhotos[article.slug]=photo;
photos.updated=today;
resources.articleLinks[article.slug]=resourceIds;
resources.updated=today;
writeJSON(articlePath,finalArticle);
writeJSON(path.join(content,'sections.json'),tax);
writeJSON(path.join(content,'editorial-plan.json'),plan);
writeJSON(path.join(content,'licensed-photos.json'),photos);
writeJSON(path.join(content,'platform-links.json'),resources);
writeJSON(stateFile,{...state,lastPublishedAt:now.toISOString(),lastSectionId:sectionId,releaseCount:(state.releaseCount||0)+1,lastSlug:article.slug});
fs.unlinkSync(candidate.path);
console.log('PUBLISHED_REVIEWED_ARTICLE '+article.slug+' section='+sectionId+' at '+now.toISOString());
