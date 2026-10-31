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
const photos={...(previous.photos||{})};
const usedIds=new Set([...Object.values(photos).map(p=>p.id),...Object.values(curated).map(p=>p.id)]);
const usedUrls=new Set([...Object.values(existing.photos).map(p=>p.url.split('?')[0]),...Object.values(photos).map(p=>p.url.split('?')[0]),...Object.values(curated).map(p=>p.url.split('?')[0])]);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#\d+;/g,' ').replace(/\s+/g,' ').trim().slice(0,180);
const hash=s=>[...s].reduce((n,c)=>(Math.imul(n,33)+c.charCodeAt(0))>>>0,5381);
const noise=/\b(with|and|the|baked|cooked|healthy|fresh|home|style|homemade|easy|simple|dish|low|salt|vegetable|vegetables)\b/gi;
function terms(r){
 const title=r.title.en.toLowerCase().replace(noise,' ').replace(/[^a-z\s-]/g,' ').replace(/\s+/g,' ').trim();
 const main=title.split(' ').slice(0,3).join(' ');
 const methodNames={tagine:'Moroccan tagine food',couscous:'Moroccan couscous',rice:'cooked rice',salad:'salad food',soup:'soup bowl',skillet:'cooked meal',roast:'roasted dinner',pasta:'pasta dish',sandwich:'sandwich food',bake:'baked food',stew:'stew food',curry:'curry dish',grill:'grilled food'};
 return [...new Set([main,methodNames[r.method]||r.cuisine+' food',r.cuisine+' cuisine food','prepared food dish'])].filter(Boolean);
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
function convert(page){
 const info=page.imageinfo?.[0];if(!info)return null;
 const lic=allowedLicense(info.extmetadata||{});
 const url=info.thumburl||info.url;
 const artist=strip(info.extmetadata?.Artist?.value||info.extmetadata?.Attribution?.value||'Wikimedia Commons');
 if(!lic||!url?.startsWith('https://')||!artist||!/^image\/(jpeg|png|webp)$/.test(info.mime||'')||info.width<640||info.height<400)return null;
 if(/\b(icon|logo|map|chart|diagram|cartoon|illustration|menu|poster|symbol|advertisement)\b/i.test(page.title))return null;
 const id='commons:'+page.pageid,src='https://commons.wikimedia.org/wiki/'+encodeURIComponent(page.title.replaceAll(' ','_'));
 if(usedIds.has(id)||usedUrls.has(url.split('?')[0]))return null;
 return {id,url,source:src,photographer:artist,license:lic.type,licenseUrl:lic.url,provider:'Wikimedia Commons',description:page.title.replace(/^File:/,''),illustrativeOnly:true};
}
let missing=recipes.filter(r=>!existing.assignments[r.slug]&&!curated[r.slug]&&!photos[r.slug]),errors=[];
console.log('Starting editorial photo candidates; verified published',Object.keys(existing.assignments).length+Object.keys(curated).length,'of',recipes.length,'photos, available candidate backlog',Object.keys(photos).length);
for(let i=0;i<missing.length;i++){
 const r=missing[i];let result=null;
 const qs=terms(r);
 for(let qi=0;qi<qs.length;qi++){
  let results;
  try{results=await queryCommons(qs[qi],qi===3?hash(r.slug)%120:0);}
  catch(err){console.warn('Commons API retry failed for '+r.slug+': '+err.message);continue;}
  result=results.map(convert).find(Boolean);
  if(result)break;
  await sleep(180);
 }
 if(!result){errors.push(r.slug);console.warn('Could not assign image to '+r.slug);continue;}
 photos[r.slug]=result;
 usedIds.add(result.id);usedUrls.add(result.url.split('?')[0]);
 console.log('PHOTO '+(i+1)+'/'+missing.length+' '+r.slug+' '+result.description.slice(0,65)+' '+result.license);
 await sleep(180);
}
const ordered=Object.fromEntries(recipes.filter(r=>photos[r.slug]&&!existing.assignments[r.slug]&&!curated[r.slug]).map(r=>[r.slug,photos[r.slug]]));
fs.writeFileSync(output,JSON.stringify({policy:'UNREVIEWED CANDIDATES ONLY; do not publish without matching actual dish, ingredients, view, license and source. Distinct commercially reusable images proposed by search.',photos:ordered},null,2)+'\n');
const count=Object.keys(existing.assignments).length+Object.keys(curated).length;
console.log('FINISHED: published',count,'of',recipes.length,'photo-backed recipes; candidates for editorial review',Object.keys(ordered).length,'; no search result is published without manual verification; missing candidates:',errors.join(', ')||'none');
if(count!==recipes.length)console.warn('Remaining illustrated recipes: '+(recipes.length-count)+'; candidacy is not approval.');
