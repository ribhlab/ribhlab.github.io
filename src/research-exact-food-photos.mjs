/**
 * Editorial search for unpublished recipe photo candidates from Wikimedia Commons.
 * Reports candidates only: NEVER updates curated-photos.json or publishes photos.
 * Search titles by dish and distinguishing ingredients, including international names.
 */
import fs from 'node:fs';
const base='content/recipes/',read=f=>JSON.parse(fs.readFileSync(base+f,'utf8'));
const recipes=['meals-01.json','meals-02.json','meals-03.json','meals-04.json','healthy-01.json'].flatMap(f=>read(f).recipes);
const published={...read('curated-photos.json').photos};
const assignments=read('photo-library.json').assignments;
const rejected=new Set(Object.entries(read('photo-review-decisions.json').rejected).map(([key,r])=>(r.recipeSlug||key)+'|'+r.id));
const queries={
 'taktouka-peppers':['taktouka','salade marocaine poivrons tomates'],
 'briouats-spinach-cheese':['spinach cheese briouat','briouate épinards fromage'],
 'moroccan-beef-peas':['beef peas tagine','tajine boeuf petits pois'],
 'mediterranean-fish-lemon':['baked fish lemon potatoes','fish parsley lemon potato'],
 'tuna-pasta-salad':['tuna pasta salad olives','salade pâtes thon olives'],
 'potato-leek-gratin':['potato leek gratin','gratin poireaux pommes de terre'],
 'miso-mushroom-noodles':['mushroom noodle soup','miso mushroom noodle broth'],
 'chinese-ginger-fish':['ginger fish Chinese','steamed fish ginger garlic scallion'],
 'tofu-vegetable-stirfry':['tofu broccoli stir fry','tofu broccoli peppers'],
 'ethiopian-lentil-stew':['misir wat lentil','Ethiopian red lentil stew'],
 'west-african-peanut-stew':['sweet potato peanut spinach stew','maafe vegetarian sweet potato'],
 'north-african-chickpea-soup':['chickpea carrot zucchini soup','moroccan chickpea vegetable soup'],
 'sweetcorn-quesadillas':['corn cheese quesadilla','quesadilla cheese sweet corn'],
 'overnight-oats-apple':['apple cinnamon overnight oats','overnight oats apple walnuts'],
 'lemon-yogurt-cake':['lemon yogurt cake','gâteau yaourt citron'],
 'semolina-orange-cake':['orange semolina cake','basbousa orange semolina'],
 'healthy-quinoa-chickpea-bowl':['quinoa chickpea cucumber tomato','quinoa chickpea salad'],
 'healthy-chicken-brown-rice':['chicken broccoli brown rice bowl','chicken vegetable brown rice'],
 'healthy-roasted-vegetable-tray':['roasted chickpeas sweet potato cauliflower','roasted vegetable chickpea tray'],
 'healthy-vegetable-egg-muffins':['egg muffins vegetables spinach','spinach pepper egg cups'],
 'healthy-tomato-bean-pasta':['pasta beans spinach tomato','whole wheat pasta white beans'],
 'healthy-sweetpotato-bean-chili':['sweet potato kidney bean chili','vegetarian sweet potato bean chili'],
 'healthy-grilled-fish-salad':['grilled fish salad lemon lettuce','grilled fish tomato cucumber salad'],
 'healthy-turkey-vegetable-soup':['turkey vegetable soup carrot celery','turkey zucchini soup'],
 'healthy-baked-apple-oats':['baked apple oat cups','baked apples oats cinnamon']
};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const strip=s=>String(s||'').replace(/<[^>]*>/g,' ').replace(/&[^; ]+;/g,' ').replace(/\s+/g,' ').trim().slice(0,210);
async function search(query){
 const url='https://commons.wikimedia.org/w/api.php?'+new URLSearchParams({action:'query',format:'json',formatversion:'2',generator:'search',gsrnamespace:'6',gsrsearch:query,gsrlimit:'14',prop:'imageinfo',iiprop:'url|size|mime|extmetadata',iiurlwidth:'1000'});
 let last;
 for(let retry=0;retry<3;retry++){
  try {
   const res=await fetch(url,{signal:AbortSignal.timeout(22000),headers:{'User-Agent':'RibhLab/1.0 editorial photo verification','Accept':'application/json'}});
   if(!res.ok)throw Error('HTTP '+res.status);
   return (await res.json()).query?.pages||[];
  }catch(e){last=e;await sleep(500*(retry+1));}
 }
 console.warn('Search failed '+query+': '+last.message);return [];
}
const publishedIds=new Set(Object.values(published).map(p=>p.id));
const out={generatedAt:new Date().toISOString(),policy:'RESEARCH ONLY: titles and CC metadata are not visual proof. An editor must confirm all visible ingredients, dish type, rights and non-duplication.',recipes:{}};
let finished=0;
for(const r of recipes.filter(r=>!published[r.slug]&&!assignments[r.slug])){
 const q=queries[r.slug]||[r.title.en],results=new Map();
 for(const query of q){
  for(const page of await search(query)){
   const info=page.imageinfo?.[0],ext=info?.extmetadata||{};
   const license=String(ext.LicenseUrl?.value||'').replace(/^http:/,'https:');
   if(!info||!license.startsWith('https://creativecommons.org/')||!['image/jpeg','image/png','image/webp'].includes(info.mime)||info.width<640||info.height<400)continue;
   const id='commons:'+page.pageid;
   if(publishedIds.has(id)||rejected.has(r.slug+'|'+id))continue;
   const title=page.title.replace(/^File:/,'');
   if(/\b(logo|banner|illustration|poster|package|advertisement|menu|chart|ingredients only|raw meat)\b/i.test(title))continue;
   if(!results.has(id))results.set(id,{id,title,url:info.thumburl||info.url,source:'https://commons.wikimedia.org/wiki/'+encodeURIComponent(page.title.replaceAll(' ','_')),licenseUrl:license,author:strip(ext.Artist?.value||ext.Attribution?.value||''),description:strip(ext.ImageDescription?.value||''),mime:info.mime,width:info.width,height:info.height,query});
  }
  await sleep(120);
 }
 out.recipes[r.slug]={title:r.title.en,requiredIngredients:r.ingredients.map(i=>i.id),matches:[...results.values()].slice(0,24)};
 finished++;console.log('RESEARCH',finished,r.slug,results.size,'eligible licensed search results');
}
fs.writeFileSync(base+'photo-research.json',JSON.stringify(out,null,2)+'\n');
console.log('RESEARCH COMPLETE: '+finished+' missing recipes; metadata candidates for manual inspection only');
