/**
 * One-off editorial photo curation (not used during a normal offline build).
 * Retrieves distinctly identified, commercially permitted Openverse photography.
 * Fails closed: incomplete results are NOT committed or published.
 * Metadata remains auditable in content/recipes/curated-photos.json.
 */
import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd(), dir=path.join(root,'content','recipes');
const batches=['meals-01.json','meals-02.json','meals-03.json','meals-04.json','healthy-01.json'];
const recipes=batches.flatMap(file=>JSON.parse(fs.readFileSync(path.join(dir,file),'utf8')).recipes);
const original=JSON.parse(fs.readFileSync(path.join(dir,'photo-library.json'),'utf8'));
const output=path.join(dir,'curated-photos.json');
const previous=fs.existsSync(output)?JSON.parse(fs.readFileSync(output,'utf8')):{photos:{}};
const photos={...(previous.photos||{})},used=new Set([
 ...Object.values(original.photos||{}).map(p=>p.photoId),
 ...Object.values(photos).map(p=>p.id)
]);
const urlUsed=new Set([...Object.values(original.photos||{}).map(p=>p.url.split('?')[0]),...Object.values(photos).map(p=>p.url.split('?')[0])]);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const NOISE=/\b(with|and|the|baked|cooked|healthy|fresh|home|style|homemade|spicy|easy|sauce|dish|vegetable|vegetables)\b/gi;
function queries(r){
 const dish=r.title.en.toLowerCase().replace(NOISE,' ').replace(/[^a-z\s-]/g,' ').replace(/\s+/g,' ').trim();
 const tokens=dish.split(' ').filter(w=>w.length>3);
 const focused=tokens.slice(0,3).join(' ');
 const category=r.method==='skillet'?'food meal':r.method==='roast'?'roasted food':r.method==='soup'?'soup':r.method==='rice'?'rice food':r.method==='sandwich'?'sandwich':r.method==='salad'?'salad':r.method==='tagine'?'tagine':r.method==='couscous'?'couscous':r.method==='pasta'?'pasta':'prepared food';
 return [...new Set([dish,focused,r.title.en.split(' ')[0]+' food',category])].filter(x=>x.length>2);
}
async function search(q){
 const u='https://api.openverse.org/v1/images/?'+new URLSearchParams({q,license:'cc0,by,by-sa',page_size:'20',mature:'false'});
 for(let attempt=0;attempt<4;attempt++){
  let response;try{response=await fetch(u,{headers:{Accept:'application/json','User-Agent':'RibhLab/1.0 (noncommercial editorial photo lookup)'}});}catch(e){if(attempt===3)throw e;await sleep(1500*(attempt+1));continue;}
  if(response.status===429||response.status>=500){if(attempt===3)throw Error('Openverse '+response.status+' for '+q);await sleep(Math.min(25000,Number(response.headers.get('retry-after')||0)*1000||5000*(attempt+1)));continue;}
  if(!response.ok)throw Error('Openverse '+response.status+' for '+q);
  return (await response.json()).results||[];
 }return [];
}
const need=recipes.filter(r=>!original.assignments?.[r.slug]&&!photos[r.slug]);
console.log('Current unique real photographs:',Object.keys(original.assignments||{}).length+Object.keys(photos).length,'of',recipes.length);
let failures=[];
for(let i=0;i<need.length;i++){
 const r=need[i];let selected=null;
 for(const query of queries(r)){
  const results=await search(query);
  const candidates=results.filter(p=>
    ['cc0','by','by-sa'].includes(p.license)&&
    p.id&&p.url?.startsWith('https://')&&p.foreign_landing_url?.startsWith('https://')&&
    !p.mature&&p.width>=640&&p.height>=400&&
    !used.has(p.id)&&!urlUsed.has(p.url.split('?')[0])&&
    /\.(jpe?g|webp|png)(?:\?|$)/i.test(p.url.split('#')[0])&&
    p.creator&&p.license_url?.startsWith('https://')
  );
  if(candidates.length){selected=candidates[0];break;}
  await sleep(350);
 }
 if(!selected){failures.push(r.slug);console.warn('No eligible unique photo: '+r.slug);continue;}
 photos[r.slug]={id:selected.id,url:selected.url,source:selected.foreign_landing_url,photographer:selected.creator,license:selected.license,licenseUrl:selected.license_url,provider:'Openverse',description:selected.title||r.title.en,illustrativeOnly:true};
 used.add(selected.id);urlUsed.add(selected.url.split('?')[0]);
 console.log((i+1)+'/'+need.length+' '+r.slug+' -> '+selected.id+' ('+selected.license+')');
 await sleep(750);
}
const complete=recipes.every(r=>original.assignments?.[r.slug]||photos[r.slug]);
const photoCount=Object.keys(photos).length;
console.log('Curated photo candidates:',photoCount,'/',need.length,'; remaining:',failures.length);
if(!complete){console.error('INCOMPLETE: refusing publication of partly curated imagery. Missing:',failures.join(', '));process.exitCode=1;}
else {
 const ordered=Object.fromEntries(recipes.filter(r=>photos[r.slug]).map(r=>[r.slug,photos[r.slug]]));
 fs.writeFileSync(output,JSON.stringify({licenseNote:'Per-image commercial-use compatible Creative Commons license and author/source recorded, all photographs illustrative',updated:'2026-10-30',photos:ordered},null,2)+'\n');
 console.log('SUCCESS: all',recipes.length,'recipes have distinct, licensed photographic identifiers; wrote',output);
}
