/**
 * Discover Wikimedia Commons photo candidates for editorial review. Never publish automatically.
 * Uses verified public Wikimedia API. Normal site builds do not depend on this API.
 * The JSON can be resumed, and only distinct image file IDs and URLs are accepted.
 */
import fs from 'node:fs';
import path from 'node:path';
const dir=path.join(process.cwd(),'content','recipes');
const batchFiles=['meals-01.json','meals-02.json','meals-03.json','meals-04.json','healthy-01.json'];
const recipes=batchFiles.flatMap(file=>JSON.parse(fs.readFileSync(path.join(dir,file),'utf8')).recipes);
const existing=JSON.parse(fs.readFileSync(path.join(dir,'photo-library.json'),'utf8'));
const curated=JSON.parse(fs.readFileSync(path.join(dir,'curated-photos.json'),'utf8')).photos;
const output=path.join(dir,'photo-candidates.json');
const previous=fs.existsSync(output)?JSON.parse(fs.readFileSync(output,'utf8')):{photos:{}};
const reviewDecisions=JSON.parse(fs.readFileSync(path.join(dir,'photo-review-decisions.json'),'utf8')).rejected;
const rejectedPairs=new Set(Object.entries(reviewDecisions).map(([slug,p])=>slug+'|'+p.id));
// Old search results were often unrelated (for example roast beef for fish).
// Keep only candidates whose actual file title names multiple recipe components.
const photos=Object.fromEntries(Object.entries(previous.photos||{}).filter(([slug,p])=>{
 const recipe=recipes.find(r=>r.slug===slug);
 return recipe&&!rejectedPairs.has(slug+'|'+p.id)&&matchesRecipe(recipe,p.description);
}));
const usedIds=new Set([...Object.values(photos).map(p=>p.id),...Object.values(curated).map(p=>p.id)]);
const usedUrls=new Set([...Object.values(existing.photos).map(p=>p.url.split('?')[0]),...Object.values(photos).map(p=>p.url.split('?')[0]),...Object.values(curated).map(p=>p.url.split('?')[0])]);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#\d+;/g,' ').replace(/\s+/g,' ').trim().slice(0,180);

const noise=/\b(with|and|the|baked|cooked|healthy|fresh|home|style|homemade|easy|simple|dish|low|salt|vegetable|vegetables)\b/gi;
function words(s){
 return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ')
  .filter(x=>x.length>=3&&!/^(with|and|the|healthy|style|inspired|home|fresh|moroccan|north|african|mediterranean|asian|whole|grain)$/.test(x))
  .map(x=>x.endsWith('s')&&x.length>4?x.slice(0,-1):x);
}
function matchesRecipe(r,fileTitle){
 const recipeTerms=[...new Set(words(r.title.en))],fileTerms=new Set(words(fileTitle));
 const matched=recipeTerms.filter(x=>fileTerms.has(x));
 // Require multiple matching recipe-specific words. Generic cuisine, method or
 // a single "soup"/"salad" word never qualifies as evidence of a matching dish.
 return matched.length>=2 && matched.some(x=>!['salad','soup','stew','rice','noodle','bowl','cake','grilled','roasted','baked','fish','beef','chicken'].includes(x));
}
function terms(r){
 const title=r.title.en.toLowerCase().replace(noise,' ').replace(/[^a-z\s-]/g,' ').replace(/\s+/g,' ').trim();
 const main=title.split(' ').slice(0,3).join(' ');
 // Specific dish words only; generic "prepared food dish" queries produced unrelated photos.
 return [...new Set([r.title.en.replace(/\b(healthy|style|inspired|whole-grain)\b/gi,'').trim(),title,main])].filter(x=>x&&x.split(' ').length>=2);
}
function allowedLicense(meta){
 const raw=strip(meta.LicenseShortName?.value||meta.License?.value||'').toLowerCase();
 const link=String(meta.LicenseUrl?.value||'').replace(/^http:/,'https:');
 if(!link.startsWith('https://creativecommons.org/'))return null;
 if(/cc0|zero/.test(raw)||link.includes('/publicdomain/zero/'))return {type:'cc0',url:link};
 if(/^cc by-sa\b/.test(raw)||link.includes('/licenses/by-sa/'))return {type:'by-sa',url:link};
 if(/^cc by\b/.test(raw)||link.includes('/licenses/by/'))return {type:'by',url:link};
 return null;
}
async function queryCommons(q,offset=0){
 const params=new URLSearchParams({action:'query',format:'json',formatversion:'2',generator:'search',gsrsearch:q,gsrnamespace:'6',gsrlimit:'30',gsroffset:String(offset),prop:'imageinfo',iiprop:'url|extmetadata|size|mime',iiurlwidth:'1000'});
 const url='https://commons.wikimedia.org/w/api.php?'+params;
 for(let i=0;i<3;i++){
  let response;
  try{response=await fetch(url,{headers:{'User-Agent':'RibhLabImageAudit/1.0 (open licensed editorial photography)','Accept':'application/json'},signal:AbortSignal.timeout(12000)});}catch(e){if(i===2)throw e;await sleep(1000*(i+1));continue;}
  if(!response.ok){if(i===2)throw Error('Wikimedia Commons HTTP '+response.status);await sleep(1200*(i+1));continue;}
  return (await response.json()).query?.pages||[];
 }return [];
}
function convert(page,r){
 const info=page.imageinfo?.[0];if(!info)return null;
 const lic=allowedLicense(info.extmetadata||{});
 const url=info.thumburl||info.url;
 const artist=strip(info.extmetadata?.Artist?.value||info.extmetadata?.Attribution?.value||'Wikimedia Commons');
 if(!lic||!url?.startsWith('https://')||!artist||!/^image\/(jpeg|png|webp)$/.test(info.mime||'')||info.width<640||info.height<400)return null;
 if(/\b(icon|logo|map|chart|diagram|cartoon|illustration|menu|poster|symbol|advertisement)\b/i.test(page.title))return null;
 if(!matchesRecipe(r,page.title.replace(/^File:/,'')))return null;
 const id='commons:'+page.pageid,src='https://commons.wikimedia.org/wiki/'+encodeURIComponent(page.title.replaceAll(' ','_'));
 if(usedIds.has(id)||usedUrls.has(url.split('?')[0])||rejectedPairs.has(r.slug+'|'+id))return null;
 return {id,url,source:src,photographer:artist,license:lic.type,licenseUrl:lic.url,provider:'Wikimedia Commons',description:page.title.replace(/^File:/,''),illustrativeOnly:true};
}
let missing=recipes.filter(r=>!existing.assignments[r.slug]&&!curated[r.slug]&&!photos[r.slug]),errors=[];
console.log('Starting editorial photo candidates; verified published',Object.keys(existing.assignments).length+Object.keys(curated).length,'of',recipes.length,'photos, available candidate backlog',Object.keys(photos).length,'explicitly rejected',rejectedPairs.size);
for(let i=0;i<missing.length;i++){
 const r=missing[i];let result=null;
 const qs=terms(r);
 for(let qi=0;qi<qs.length;qi++){
  let results;
  try{results=await queryCommons(qs[qi],0);}
  catch(err){console.warn('Commons API retry failed for '+r.slug+': '+err.message);continue;}
  result=results.map(p=>convert(p,r)).find(Boolean);
  if(result)break;
  await sleep(180);
 }
 if(!result){errors.push(r.slug);console.warn('Could not assign image to '+r.slug);continue;}
 photos[r.slug]=result;
 usedIds.add(result.id);usedUrls.add(result.url.split('?')[0]);
 console.log('PHOTO '+(i+1)+'/'+missing.length+' '+r.slug+' '+result.description.slice(0,65)+' '+result.license);
 await sleep(180);
}
const ordered=Object.fromEntries(recipes.filter(r=>photos[r.slug]&&!existing.assignments[r.slug]&&!curated[r.slug]&&matchesRecipe(r,photos[r.slug].description)).map(r=>[r.slug,photos[r.slug]]));
fs.writeFileSync(output,JSON.stringify({policy:'UNREVIEWED CANDIDATES ONLY; do not publish without matching actual dish, ingredients, view, license and source. Distinct commercially reusable images proposed by search.',photos:ordered},null,2)+'\n');
const count=Object.keys(existing.assignments).length+Object.keys(curated).length;
console.log('FINISHED: published',count,'of',recipes.length,'photo-backed recipes; candidates for editorial review',Object.keys(ordered).length,'; no search result is published without manual verification; missing candidates:',errors.join(', ')||'none');
if(count!==recipes.length)console.warn('Remaining illustrated recipes: '+(recipes.length-count)+'; candidacy is not approval.');
