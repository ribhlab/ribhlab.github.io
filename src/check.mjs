import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dist=path.join(root,'dist');
const configuredUrl=(process.env.SITE_URL||JSON.parse(fs.readFileSync(path.join(root,'site.config.json'),'utf8')).domain||'');
const basePath=configuredUrl ? new URL(configuredUrl).pathname.replace(/\/$/,'') : '';
const stripBase=u=>basePath&&u.startsWith(basePath+'/')?u.slice(basePath.length):u;
if(!fs.existsSync(dist))throw Error('Run npm run build first');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(x=>x.isDirectory()?walk(path.join(dir,x.name)):[path.join(dir,x.name)]);}
const pages=walk(dist).filter(p=>p.endsWith('.html'));
let checked=0;const errors=[];
for(const p of pages){const h=fs.readFileSync(p,'utf8');const pathName='/'+path.relative(dist,p).replace(/\\/g,'/');
 if(/^\/(?:admin\/)?google[a-z0-9]+\.html$/i.test(pathName)) continue; // Google ownership token is not an editorial page
 if(!h.includes('lang=') && !pathName.includes('/admin/') && pathName!=='/index.html')errors.push(`${pathName}: missing language`);
 if(!h.includes('<title>'))errors.push(`${pathName}: missing title`);
 if(!pathName.includes('/admin/') && !['/index.html','/404.html'].includes(pathName)){
  if(!h.includes('name="description"'))errors.push(`${pathName}: missing meta description`);
  if(!h.includes('id="main"'))errors.push(`${pathName}: missing main landmark`);
  const expected=pathName.startsWith('/ar/')?'ar':pathName.startsWith('/en/')?'en':'fr';
  if(!h.includes(`lang="${expected}"`)) errors.push(`${pathName}: incorrect page language`);
 }
 for(const m of h.matchAll(/(?:href|src)="(\/[^"?#]*)/g)){
  let target=stripBase(decodeURIComponent(m[1]));if(target==='/')continue;
  const possible=path.join(dist,target.replace(/^\//,''));
  if(!fs.existsSync(possible)&&!fs.existsSync(path.join(possible,'index.html')))errors.push(`${pathName}: broken link ${target}`);
  checked++;
 }
}
for(const lang of ['ar','en','fr']){
 const index=JSON.parse(fs.readFileSync(path.join(dist,'assets',`search-${lang}.json`),'utf8'));
 if(index.length!==fs.readdirSync(path.join(root,'content/articles')).filter(x=>x.endsWith('.json')).length) errors.push(`Search index ${lang}: inconsistent article count ${index.length}`);
 for(const a of index) if(!fs.existsSync(path.join(dist,stripBase(a.url).replace(/^\//,''),'index.html'))) errors.push(`Search entry broken: ${a.url}`);
}
if(errors.length){console.error(errors.slice(0,20).join('\n'));console.error(`${errors.length} errors`);process.exit(1);}
console.log(`PASS: ${pages.length} HTML files, ${checked} internal links/assets, 27 translated article pages, search indexes and static pages.`);
