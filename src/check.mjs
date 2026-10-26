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
// Keep the Search Console ownership token intact across all releases.
const tokenName='googlee227daed117c5deb.html';
const tokenSource=path.join(root,'public',tokenName);
const tokenBuilt=path.join(dist,tokenName);
const expectedToken='google-site-verification: '+tokenName;
if(!fs.existsSync(tokenSource)||fs.readFileSync(tokenSource,'utf8').trim()!==expectedToken) errors.push('Search Console: missing or modified ownership token in public/');
if(!fs.existsSync(tokenBuilt)||fs.readFileSync(tokenBuilt,'utf8').trim()!==expectedToken) errors.push('Search Console: ownership token missing from generated website');
if(configuredUrl){
 const url=configuredUrl.endsWith('/')?configuredUrl.slice(0,-1):configuredUrl;
 const sitemapPath=path.join(dist,'sitemap.xml');
 if(!fs.existsSync(sitemapPath)) errors.push('Search Console: sitemap.xml missing');
 else {
  const sitemap=fs.readFileSync(sitemapPath,'utf8');
  const urls=[...sitemap.matchAll(new RegExp('<loc>([^<]*)</loc>','g'))].map(m=>m[1]);
  if(urls.length<30)errors.push('Search Console: sitemap unexpectedly short ('+urls.length+' URLs)');
  if(new Set(urls).size!==urls.length)errors.push('Search Console: duplicate canonical URLs in sitemap');
  if(urls.some(x=>!x.startsWith(url+'/')))errors.push('Search Console: off-domain or wrong-path URLs in sitemap');
  for(const lang of ['ar','en','fr'])if(!urls.includes(url+'/'+lang+'/'))errors.push('Search Console: missing '+lang+' homepage in sitemap');
 }
}
// Editorial and SEO regression checks: validate every translated article before publishing.
const articleDir=path.join(root,'content','articles');
for(const filename of fs.readdirSync(articleDir).filter(f=>f.endsWith('.json'))){
 let article;
 try{article=JSON.parse(fs.readFileSync(path.join(articleDir,filename),'utf8'));}catch(e){errors.push('Invalid article JSON: '+filename);continue;}
 if(filename!==article.slug+'.json')errors.push(filename+': file/slug mismatch');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(article.date||'')||!/^\d{4}-\d{2}-\d{2}$/.test(article.updated||''))errors.push(filename+': publication/update dates missing');
 if(article.updated<article.date)errors.push(filename+': update date predates publication');
 const refs=(article.sources||[]);
 if(!Array.isArray(refs))errors.push(filename+': sources must be an array');
 else for(const ref of refs){
  try{if(new URL(ref.url).protocol!=='https:')errors.push(filename+': source must use HTTPS');}catch{errors.push(filename+': invalid source URL');}
  if(!ref.label)errors.push(filename+': missing source label');
 }
 for(const lang of ['ar','en','fr']){
  const t=article.translations?.[lang];
  if(!t?.title||!t?.excerpt||!t?.lead||!Array.isArray(t.sections)||t.sections.length<3){errors.push(filename+': missing full '+lang+' translation');continue;}
  for(const sec of t.sections)if(!sec.heading||!Array.isArray(sec.paragraphs)||!sec.paragraphs.length)errors.push(filename+': empty section in '+lang);
  const htmlPath=path.join(dist,lang,'article',article.slug,'index.html');
  if(!fs.existsSync(htmlPath)){errors.push(filename+': missing generated '+lang+' page');continue;}
  const html=fs.readFileSync(htmlPath,'utf8');
  if(configuredUrl&&!html.includes('<link rel="canonical"'))errors.push(filename+': missing canonical in '+lang);
  if(!html.includes('application/ld+json'))errors.push(filename+': missing structured data in '+lang);
  if(!html.includes('name="description"'))errors.push(filename+': missing SEO description in '+lang);
  if(refs.length&&!html.includes('class="article-sources"'))errors.push(filename+': missing reference section in '+lang);
  if(article.partner?.url&&(!html.includes('class="partner-box"')||!html.includes('rel="sponsored nofollow')))errors.push(filename+': missing disclosed partner link in '+lang);
 }
}
for(const pagePath of pages){
 const content=fs.readFileSync(pagePath,'utf8');
 for(const imageTag of content.match(/<img\b[^>]*>/g)||[]){
  if(!/\balt=/.test(imageTag))errors.push(pagePath+': image missing alt attribute');
  if(!/\bwidth=/.test(imageTag)||!/\bheight=/.test(imageTag))errors.push(pagePath+': image missing dimensions');
 }
}
if(errors.length){console.error(errors.slice(0,20).join('\n'));console.error(`${errors.length} errors`);process.exit(1);}
console.log(`PASS: ${pages.length} HTML files, ${checked} internal links/assets, translated article pages, search indexes and static pages.`);
