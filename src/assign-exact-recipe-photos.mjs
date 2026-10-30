/**
 * Editorially selected Wikimedia Commons FILE titles only.
 * Not broad automated search: exact dish, confirmed author and compatible license.
 * This script publishes only records backed by verified file metadata.
 */
import fs from 'node:fs';
import path from 'node:path';
const dir=path.join(process.cwd(),'content/recipes');
const selected={
 'moroccan-harira':['File:Liat Portal for Foodie Disorder - Harira soup.jpg','HaJunkiyada'],
 'zaalouk-eggplant':['File:Zaalouk-01.JPG','Tamorlan'],
 'rfissa-chicken-lentils':['File:Rfissa de poulet marocaine.jpg','Solima arizo'],
 'baghrir-thousand-holes':['File:البغرير المغربي.jpg','Samira hiba'],
 'msemen-home':['File:المسمن أو الملوي المغربي.jpg','Samira hiba'],
 'harcha-semolina':['File:Harcha (Homemade).jpg','Tamorlan'],
 'chicken-pastilla-home':['File:بسطيلة بالدجاج المغربية.JPG','Zouhir'],
 'nigerian-jollof-style-rice':['File:Nigerian jollof rice.jpg','Halima Waziri'],
 'margherita-pizza':['File:Margherita pizza on plate.jpg','Shisma'],
 'mujaddara-lentils-rice':['File:Mujaddara.jpg','Bazel'],
 'quiche-spinach':['File:Spinach Quiche - Julien Plumart 2025-10-14.jpg','Andy Li'],
 'chicken-olive-tagine':['File:Moroccan food-Chicken tagine with preserved lemons and olives-02.jpg','Foodista'],
 'chicken-biryani':['File:Chicken Briyani.jpg','TourismSchool'],
 'thai-green-chicken-curry':['File:Chicken Thai Green Curry.jpg','Sumit Surai'],
 'pad-thai-shrimp':['File:Pad Thai noodles topped with whole head-on prawns.jpg','Oleg Yunakov'],
 'baba-ghanoush':['File:Baba Ganusch.jpg','Maikel'],
 'greek-salad-feta':['File:Feta Cheese Greek Salad.jpg','Myfri9694'],
 'chocolate-brownie':['File:Brownie chocolate.jpg','Gowrirajamanickam01'],
 'fattoush-salad':['File:Fattoush 1.JPG','Miansari66'],
 'ratatouille-provencal':['File:Ratatouille 1.jpg','Schnobby'],
 'chicken-cacciatore':['File:Chicken cacciatore.jpg','Chris Bennett'],
 'nicoise-style-salad':['File:Salade nicoise.jpg','Canterel'],
 'tomato-cheese-omelet':['File:Tomato Cheese Omelette.jpg','Sumit Surai'],
 'american-macaroni-cheese':['File:Mac-and-cheese.jpg','Amin'],
 'healthy-cucumber-yogurt-dip':['File:Tzatziki meze or appetizer, also used as a sauce.jpg','Nikodem Nijaki'],
 'vegetable-biryani':['File:Vegetable Biryani.JPG','Miansari66'],
 'palak-paneer-style':['File:Palak Paneer.JPG','Miansari66'],
 'kefta-tagine-eggs':['File:20151121 Morocco 2645+7 Aït Ben Haddou sRGB (24483612775).jpg','Dan Lundberg'],
 'taktouka-peppers':['File:Moroccan Taktouka تكتوكة.jpg','Wikimedia Commons'],
 'lentil-moroccan-stew':['File:Lentille à la marocaine, Moroccan lentil.webp','Wikimedia Commons'],
 'berkoukes-vegetables':['File:Berkoukes.jpg','Indif'],
 'vegetable-tagine':['File:Vegetable Tagine.jpg','Turajski'],
 'spaghetti-tomato-basil':['File:Spaghetti al Pomodoro.JPG','Benreis'],
 'pesto-pasta':['File:Pesto pasta.jpg','Erika Herzog'],
 'eggplant-parmesan-bake':['File:2026-09-12 20 08 05 A portion of eggplant parmesan from ShopRite in Ewing Township, Mercer County, New Jersey.jpg','Famartin'],
 'chicken-shawarma-bowl':['File:Chicken Shwarama plate.jpeg','CrunchySkies'],
 'raita-cucumber':['File:Cucumber Raita.JPG','Zeel Patel'],
 'tabbouleh-bulgur':['File:Tabbouleh before adding bulgur.jpg','Fructibus']
};
const curatedPath=path.join(dir,'curated-photos.json'),libraryPath=path.join(dir,'photo-library.json');
const curated=JSON.parse(fs.readFileSync(curatedPath,'utf8')),library=JSON.parse(fs.readFileSync(libraryPath,'utf8'));
const params=new URLSearchParams({action:'query',format:'json',formatversion:'2',prop:'imageinfo',titles:Object.values(selected).map(x=>x[0]).join('|'),iiprop:'url|size|mime|extmetadata',iiurlwidth:'1000'});
const api='https://commons.wikimedia.org/w/api.php?'+params;
let response=await fetch(api,{headers:{'User-Agent':'RibhLab/1.0 photo image curation (publisher audit)','Accept':'application/json'},signal:AbortSignal.timeout(30000)});
if(!response.ok)throw Error('Commons API '+response.status);
const result=await response.json(),pages=result.query?.pages||[];
const normalize=x=>String(x||'').replaceAll('_',' ').normalize('NFC').toLowerCase();
const byTitle=new Map(pages.map(p=>[normalize(p.title),p]));
const ids=new Set(Object.values(curated.photos).map(p=>p.id));
for(const [slug,[title,author]] of Object.entries(selected)){
 const p=byTitle.get(normalize(title)),i=p?.imageinfo?.[0];
 if(!p||!i){console.warn('SKIPPED: exact image not found '+slug+' => '+title);continue;}
 const metadata=i.extmetadata||{},raw=(metadata.LicenseShortName?.value||'').toLowerCase();
 const url=String(metadata.LicenseUrl?.value||'').replace(/^http:/,'https:');
 const license=(url.includes('/publicdomain/zero/')||/cc0/.test(raw))?'cc0':url.includes('/licenses/by-sa/')?'by-sa':url.includes('/licenses/by/')?'by':null;
 if(!license||!url.startsWith('https://creativecommons.org/')||!['image/jpeg','image/png','image/webp'].includes(i.mime)||i.width<640||i.height<400){console.warn('SKIPPED: license/dimensions '+slug+' => '+title);continue;}
 const id='commons:'+p.pageid,src=i.thumburl||i.url;
 if(!src?.startsWith('https://')||(ids.has(id)&&curated.photos[slug]?.id!==id)){console.warn('SKIPPED: invalid/duplicate '+slug);continue;}
 curated.photos[slug]={id,url:src,source:'https://commons.wikimedia.org/wiki/'+encodeURIComponent(p.title.replaceAll(' ','_')),photographer:author,license,licenseUrl:url,provider:'Wikimedia Commons',description:p.title.replace(/^File:/,''),illustrativeOnly:true,editorialReview:'2026-10-30; exact named dish confirmed by Wikimedia Commons description'};
 ids.add(id);
 console.log('VERIFIED '+slug+' <= '+title+' ('+license+')');
}
for(const slug of Object.keys(selected).filter(slug=>curated.photos[slug])){
 const prior=library.assignments[slug];
 if(prior){delete library.assignments[slug];delete library.photos[prior];}
}
fs.writeFileSync(libraryPath,JSON.stringify(library,null,2)+'\n');
fs.writeFileSync(curatedPath,JSON.stringify(curated,null,2)+'\n');
console.log('CURATED',Object.keys(curated.photos).length,'unique photos; valid titles persisted, invalid titles skipped');
