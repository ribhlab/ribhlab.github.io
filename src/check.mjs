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
  const htmlPath=path.join(dist,lang,article.category,article.slug,'index.html');
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
// Editorial taxonomy: every real article has exactly one section and each section has forty slots.
const taxonomy=JSON.parse(fs.readFileSync(path.join(root,'content','sections.json'),'utf8'));
const publishingPlan=JSON.parse(fs.readFileSync(path.join(root,'content','editorial-plan.json'),'utf8'));
if(taxonomy.sections.length!==10||publishingPlan.sections.length!==10)errors.push('Editorial taxonomy: expected ten sections');
const assignedSlugs=new Set(),knownSlugs=new Set(fs.readdirSync(articleDir).filter(f=>f.endsWith('.json')).map(f=>f.slice(0,-5)));
for(const s of taxonomy.sections){
 const plan=publishingPlan.sections.find(x=>x.id===s.id);
 if(!plan)errors.push('Editorial plan missing '+s.id);
 if(s.targetArticles!==40||!plan||plan.publishedSlugs.length+plan.ideas.length!==40)errors.push('Section target count must equal 40: '+s.id);
 if(plan&&JSON.stringify(plan.publishedSlugs)!==JSON.stringify(s.publishedSlugs))errors.push('Plan mapping out of sync: '+s.id);
 for(const slug of s.publishedSlugs){
  if(!knownSlugs.has(slug)||assignedSlugs.has(slug))errors.push('Missing or duplicate article classification: '+slug);
  assignedSlugs.add(slug);
 }
 for(const lang of ['ar','en','fr']){
  const directory=path.join(dist,lang,'sections',s.id,'index.html');
  if(!fs.existsSync(directory))errors.push('Missing section page '+lang+'/'+s.id);
  else if(!fs.readFileSync(directory,'utf8').includes('rel="canonical"'))errors.push('Missing canonical for section '+lang+'/'+s.id);
 }
}
if(assignedSlugs.size!==knownSlugs.size)errors.push('Not all published articles are classified');
for(const lang of ['ar','en','fr'])if(!fs.existsSync(path.join(dist,lang,'sections','index.html')))errors.push('Missing section directory '+lang);
// Licensed photography: valid provenance, source credit and offline SVG fallback across 87 article views.
const photos=JSON.parse(fs.readFileSync(path.join(root,'content','licensed-photos.json'),'utf8'));
if(photos.licenseUrl!=='https://unsplash.com/license')errors.push('Photo catalog must identify Unsplash license');
if(Object.keys(photos.photos||{}).length)errors.push('Section-level shared image catalog is forbidden');
const photoSlugs=new Set(Object.keys(photos.articlePhotos||{}));
const photoIds=new Map(),photoSources=new Map();
for(const [slug,p] of Object.entries(photos.articlePhotos||{})){
 if(!knownSlugs.has(slug))errors.push('Orphan editorial photo '+slug);
 if(!/^photo-\d+-[a-f0-9]+$/.test(p.photoId)||!/^https:\/\/unsplash\.com\/photos\//.test(p.source)||!p.photographer||!p.alt||!p.altAr||!p.altFr||p.license!=='Unsplash License')errors.push('Incomplete photo license or alt text for '+slug);
 if(photoIds.has(p.photoId))errors.push('DUPLICATE PHOTO: '+slug+' and '+photoIds.get(p.photoId));
 if(photoSources.has(p.source))errors.push('DUPLICATE SOURCE: '+slug+' and '+photoSources.get(p.source));
 photoIds.set(p.photoId,slug);photoSources.set(p.source,slug);
}
if(photoSlugs.size!==knownSlugs.size)errors.push('Each published article requires exactly one unique photo: '+photoSlugs.size+' photos vs '+knownSlugs.size+' articles');
for(const slug of knownSlugs)if(!photoSlugs.has(slug))errors.push('MISSING PHOTOGRAPH: '+slug);
for(const filename of fs.readdirSync(articleDir).filter(f=>f.endsWith('.json'))){
 const a=JSON.parse(fs.readFileSync(path.join(articleDir,filename),'utf8'));
 const p=photos.articlePhotos[a.slug];
 if(!p)continue;
 for(const lang of ['ar','en','fr']){
  const f=path.join(dist,lang,a.category,a.slug,'index.html');
  if(!fs.existsSync(f))continue;
  const h=fs.readFileSync(f,'utf8');
  if(!h.includes('class="article-illustration licensed-editorial-photo"'))errors.push('Missing real photographic article figure '+lang+'/'+a.slug);
  if(!h.includes('images.unsplash.com/'+p.photoId))errors.push('Article image not matched to unique photo '+lang+'/'+a.slug);
  if(!h.includes('property="og:image" content="https://images.unsplash.com/'+p.photoId))errors.push('Article social preview lacks unique real photo '+lang+'/'+a.slug);
  if(!h.includes('name="twitter:image" content="https://images.unsplash.com/'+p.photoId))errors.push('Twitter social preview lacks unique real photo '+lang+'/'+a.slug);
  const photoTag=h.match(/<figure class="article-illustration licensed-editorial-photo">[\s\S]*?<img[^>]+>/);
  if(!photoTag||!photoTag[0].includes('src="https://images.unsplash.com/'+p.photoId))errors.push('Article photographic figure has wrong source '+lang+'/'+a.slug);
  if(!h.includes(p.photographer+' / Unsplash'))errors.push('Photographer credit missing '+lang+'/'+a.slug);
  if(h.includes('/covers/'+a.slug+'.svg')||h.includes('original-cover-figure'))errors.push('Generated SVG illustration still shown '+lang+'/'+a.slug);
 }
}
for(const lang of ['ar','en','fr']){
 const h=fs.readFileSync(path.join(dist,lang,'index.html'),'utf8');
 if(!h.includes('class="card-cover-image editorial-photo"'))errors.push('Homepage missing real photos '+lang);
}

// Official links and article attribution checks (SVG artwork is not a photo).
const resourceConfig=JSON.parse(fs.readFileSync(path.join(root,'content','platform-links.json'),'utf8'));
for(const [id,item] of Object.entries(resourceConfig.platforms)){
 try{if(new URL(item.url).protocol!=='https:')errors.push('Resource '+id+': insecure URL');}
 catch{errors.push('Resource '+id+': invalid URL');}
 if(!item.name)errors.push('Resource '+id+': missing label');
}
for(const filename of fs.readdirSync(articleDir).filter(f=>f.endsWith('.json'))){
 const slug=filename.slice(0,-5);
 const refs=resourceConfig.articleLinks[slug];
 if(!Array.isArray(refs)||refs.length<2)errors.push('Insufficient official platform links for '+slug);
 for(const id of refs||[])if(!resourceConfig.platforms[id])errors.push('Unknown platform ID '+id+' for '+slug);
 const article=JSON.parse(fs.readFileSync(path.join(articleDir,filename),'utf8'));
 for(const lang of ['ar','en','fr']){
  const rendered=path.join(dist,lang,article.category,slug,'index.html');
  if(!fs.existsSync(rendered))continue;
  const html=fs.readFileSync(rendered,'utf8');
  if(!html.includes('class="article-resource-box"'))errors.push('Official link box absent '+lang+'/'+slug);
  const image=html.match(/<figure class="article-illustration licensed-editorial-photo">[\s\S]*?<img[^>]+>/);
  if(!image||!image[0].includes('alt='))errors.push('Article photograph missing alt '+lang+'/'+slug);
 }
}
for(const lang of ['ar','en','fr']){
 const page=fs.readFileSync(path.join(dist,lang,'index.html'),'utf8');
 const top=page.indexOf('id="latest"'),sections=page.indexOf('id="editorial-sections"');
 if(top<0||sections<0||top>sections)errors.push('Newest stories not before section navigation in '+lang);
 const newest=page.slice(top,sections);
 if((newest.match(/class="article-card /g)||[]).length<6)errors.push('Too few homepage latest cards in '+lang);
}

// Every tool must have its own directly addressable working page in all languages.
const toolRoutes=[
 ['risk-calculator','risk-tool','risk-result'],
 ['freelance-pricing','fee-tool','fee-result'],
 ['prompt-builder','prompt-tool','create-prompt'],
 ['speed-test','speed-tool','speed-start'],
 ['ad-revenue','rpm-tool','calc-page-result'],
 ['affiliate-commission','affiliate-tool','calc-aff-result'],
 ['game-revenue','game-revenue-tool','calc-game-result'],
 ['word-counter','word-counter','words-input'],
 ['json-validator','json-formatter','json-format'],
 ['position-size','position-sizer','position-units'],
 ['document-studio','document-studio','studio-preview']
];
for(const lang of ['ar','en','fr']){
 const catalogFile=path.join(dist,lang,'tools','index.html');
 if(!fs.existsSync(catalogFile)){errors.push('Tool index missing '+lang);continue;}
 const catalog=fs.readFileSync(catalogFile,'utf8');
 for(const [slug,cardId,controlId] of toolRoutes){
  const f=path.join(dist,lang,'tools',slug,'index.html');
  if(!fs.existsSync(f)){errors.push('Missing isolated tool '+lang+'/'+slug);continue;}
  const html=fs.readFileSync(f,'utf8');
  if(!html.includes('id="'+cardId+'"')||!html.includes('id="'+controlId+'"'))errors.push('Nonfunctional tool layout '+lang+'/'+slug);
  if(!catalog.includes('/'+lang+'/tools/'+slug+'/'))errors.push('Tool absent from directory '+lang+'/'+slug);
  const ids=Array.from(html.matchAll(/\bid="([^"]+)"/g),m=>m[1]);
  if(new Set(ids).size!==ids.length)errors.push('Duplicate DOM ID in '+lang+'/'+slug);
 }
}
const app=fs.readFileSync(path.join(dist,'assets','app.js'),'utf8');
for(const symbol of ['position-units','words-count','json-format']){
 if(!app.includes(symbol))errors.push('Missing live tool implementation '+symbol);
}


// Document Studio Pro must remain free and operational; payment/AI claims are forbidden.
const plan=JSON.parse(fs.readFileSync(path.join(root,'content','tool-pricing.json'),'utf8')).products?.documentStudioPro;
if(!plan||plan.priceUsd!==0||plan.currency!=='USD'||plan.checkoutEnabled!==false||plan.requiresPaymentMethod!==false||plan.requiresAccount!==false||plan.externalAiEnabled!==false)errors.push('Document Studio Pro must be fully $0 without checkout/account or hosted AI');
for(const filename of ['document-studio.js','document-studio-core.mjs']){
 if(!fs.existsSync(path.join(dist,'assets',filename)))errors.push('Missing standalone Document Studio Pro browser module: '+filename);
}
const documentApp=fs.readFileSync(path.join(dist,'assets','document-studio.js'),'utf8');
for(const symbol of ['studio-save','studio-load','studio-html','studio-json-download','studio-print','studio-csv','studio-prompt','studio-import','studio-add-item','computeTotals','normalizeDraft']){
 if(!documentApp.includes(symbol))errors.push('Document Studio Pro interactive action not implemented: '+symbol);
}
if(/\bfetch\s*\(|XMLHttpRequest|WebSocket/.test(documentApp))errors.push('Studio Pro must not silently upload user documents to external services');
for(const lang of ['ar','en','fr']){
 const f=path.join(dist,lang,'tools','document-studio','index.html');
 if(!fs.existsSync(f)){errors.push('Studio Pro missing locale '+lang);continue;}
 const h=fs.readFileSync(f,'utf8');
 if(!h.includes('Document Studio Pro')||!h.includes('data-price-usd="0"')||!h.includes('data-checkout-enabled="false"'))errors.push('Studio Pro pricing not shown as USD 0 in '+lang);
 if(!h.includes('src="/ribhlab-site/assets/document-studio.js"')&&!h.includes('src="/assets/document-studio.js"'))errors.push('Studio Pro module not loaded '+lang);
 for(const id of ['studio-type','studio-theme','studio-name','studio-client','studio-items','studio-discount','studio-tax','studio-print','studio-html','studio-csv','studio-json-download','studio-save','studio-load','studio-clear','studio-import','studio-ai-prompt-output','studio-preview']){
  if(!h.includes('id="'+id+'"'))errors.push('Studio Pro control '+id+' missing in '+lang);
 }
}

// Each document mode needs its own tailored editor fields instead of generic invoice form.
for(const lang of ['ar','en','fr']){
 const f=path.join(dist,lang,'tools','document-studio','index.html');
 if(!fs.existsSync(f)){errors.push('Document Studio Pro route missing '+lang);continue;}
 const html=fs.readFileSync(f,'utf8');
 for(const [mode,ids] of [
  ['cv',['studio-cv-experience','studio-cv-education','studio-cv-skills','studio-cv-languages','studio-cv-certifications','studio-cv-link','studio-demo']],
  ['report',['studio-report-context','studio-report-method','studio-report-findings','studio-report-recommendations','studio-report-conclusion']],
  ['letter',['studio-letter-subject','studio-letter-greeting','studio-letter-closing']]
 ]){
  if(!html.includes('data-studio-mode="'+mode+'" hidden'))errors.push('Missing hidden mode panel '+mode+' '+lang);
  for(const id of ids)if(!html.includes('id="'+id+'"'))errors.push('Missing tailored '+mode+' input '+id+' '+lang);
 }
}
const studioModule=fs.readFileSync(path.join(dist,'assets','document-studio.js'),'utf8');
for(const fragment of ["modeSwitch(kind)","draft.cvExperience","draft.cvEducation","draft.reportRecommendations","draft.letterSubject","studio-document-section","studio-empty-hint","studio-demo"]){
 if(!studioModule.includes(fragment))errors.push('Missing document-specific live preview support: '+fragment);
}

// The free Pro tool must also be discoverable from the home page (below newest stories).
for(const lang of ['ar','en','fr']){
 const page=fs.readFileSync(path.join(dist,lang,'index.html'),'utf8');
 if(!page.includes('id="studio-free"')||!page.includes('href="/ribhlab-site/'+lang+'/tools/document-studio/"'))errors.push('Document Studio Pro home CTA missing '+lang);
 if(!page.includes('$0 USD'))errors.push('Free USD 0 homepage offer missing '+lang);
 const newest=page.indexOf('id="latest"'),free=page.indexOf('id="studio-free"');
 if(newest<0||free<newest)errors.push('Newest articles must appear before Pro spotlight in '+lang);
}


// Market Pulse editorial quality: primary-source summaries, unique real photographs,
// one registered-GitHub-only comment thread for each story, and locale-specific pages.
const digests=JSON.parse(fs.readFileSync(path.join(root,'content','market-digests.json'),'utf8'));
if(!Array.isArray(digests.items)||digests.items.length<6)errors.push('Fewer than six reviewed Market Pulse stories');
const marketSlugs=new Set(),marketImages=new Set(),marketSources=new Set(),threads=new Set();
for(const d of digests.items||[]){
 if(!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(d.id||'')||marketSlugs.has(d.id))errors.push('Invalid/duplicate Market Pulse slug '+d.id);
 marketSlugs.add(d.id);
 if(!/^\d{4}-\d{2}-\d{2}T/.test(d.publishedAt||'')||d.publishedAt.slice(0,10)>'2026-10-27')errors.push('Source date is invalid or in the future: '+d.id);
 if(!d.source||!/^https:\/\/(?:www\.)?(?:gold\.org|bls\.gov|stats\.gov\.cn|ecb\.europa\.eu|boj\.or\.jp|federalreserve\.gov)\//.test(d.sourceUrl||''))errors.push('Market summary must cite primary source: '+d.id);
 if(!Number.isInteger(d.discussionIssue)||d.discussionIssue<1||threads.has(d.discussionIssue))errors.push('Comment issue not uniquely registered: '+d.id);
 threads.add(d.discussionIssue);
 const p=d.photo||{};
 if(!/^photo-\d+-[a-f0-9]+$/.test(p.photoId||'')||!/https:\/\/unsplash\.com\/photos\//.test(p.source||'')||p.license!=='Unsplash License'||!p.photographer)errors.push('Unlicensed/invalid editorial photograph '+d.id);
 if(marketImages.has(p.photoId)||photoIds.has(p.photoId)||marketSources.has(p.source)||photoSources.has(p.source))errors.push('Duplicated photo across Market Pulse and articles: '+d.id);
 marketImages.add(p.photoId);marketSources.add(p.source);
 for(const lang of ['ar','en','fr']){
  const tr=d.translations?.[lang];
  if(!tr?.title||!tr.summary||tr.summary.length<100||!tr.impact||!tr.watch||!p.alt?.[lang])errors.push('Incomplete translated digest '+lang+'/'+d.id);
  const f=path.join(dist,lang,'markets','read',d.id,'index.html');
  if(!fs.existsSync(f)){errors.push('Market Pulse digest page missing '+lang+'/'+d.id);continue;}
  const html=fs.readFileSync(f,'utf8');
  if(!html.includes('images.unsplash.com/'+p.photoId)||!html.includes('property="og:image" content="https://images.unsplash.com/'+p.photoId))errors.push('Wrong unique real photo/SEO preview '+lang+'/'+d.id);
  if(!html.includes('data-market-comment-thread="'+d.discussionIssue+'"')||!html.includes('https://github.com/univcours/ribhlab-site/issues/'+d.discussionIssue))errors.push('Registered comment thread missing '+lang+'/'+d.id);
  if(!html.includes('market-comments.js')||!html.includes('class="market-summary-main"')||!html.includes('class="market-story-figure"'))errors.push('Market digest incomplete '+lang+'/'+d.id);
  if(!html.includes(d.sourceUrl)||!html.includes(p.source)||!html.includes(p.photographer))errors.push('Primary source or photo attribution missing '+lang+'/'+d.id);
 }
}
for(const lang of ['ar','en','fr']){
 const h=fs.readFileSync(path.join(dist,lang,'markets','index.html'),'utf8');
 if(!h.includes('id="market-digests"')||!h.includes('market-digest-grid'))errors.push('Market Pulse lacks original photo-rich digests '+lang);
 for(const d of digests.items||[])if(!h.includes('/'+lang+'/markets/read/'+d.id+'/'))errors.push('Market digest absent from list '+lang+'/'+d.id);
}
const marketClient=path.join(dist,'assets','market-comments.js');
if(!fs.existsSync(marketClient))errors.push('Market registered comments module not deployed');
else{
 const code=fs.readFileSync(marketClient,'utf8');
 if(!code.includes('api.github.com/repos/univcours/ribhlab-site/issues/')||!code.includes('document.createTextNode')&& !code.includes('body.textContent='))errors.push('Public comments not safely rendered');
 if(code.includes('.innerHTML')||/method\s*:\s*['\"]POST['\"]/.test(code)||/type\s*=\s*['\"]password['\"]/.test(code))errors.push('Unsafe client-side comments or unapproved anonymous login');
}


// Journal design quality gate: multilingual premium editorial interface,
// visually distinct images (no same photo on cover, latest and editor picks),
// and the existing feature-rich site routes continue to work.
const journalThemePath=path.join(dist,'assets','editorial-theme.css');
if(!fs.existsSync(journalThemePath))errors.push('Missing dedicated editorial magazine stylesheet');
else{
 const theme=fs.readFileSync(journalThemePath,'utf8');
 for(const feature of ['.hero-editorial-cover','.magazine-topic-rail','.latest-first .article-grid','.article-content .lead','.market-digest-card','html[lang=ar]','@media(max-width:560px)','@media(prefers-reduced-motion:reduce)']){
  if(!theme.includes(feature))errors.push('Missing editorial design or accessibility style: '+feature);
 }
 const blocks=(theme.match(/\{/g)||[]).length,ends=(theme.match(/\}/g)||[]).length;
 if(blocks!==ends)errors.push('Editorial stylesheet has unbalanced rule braces');
}
for(const lang of ['ar','en','fr']){
 const home=fs.readFileSync(path.join(dist,lang,'index.html'),'utf8');
 for(const marker of ['class="magazine-masthead"','class="hero-editorial-cover"','class="magazine-topic-rail"','class="article-grid"','id="studio-free"','id="latest"']){
  if(!home.includes(marker))errors.push('Premium journal homepage missing '+lang+' '+marker);
 }
 if(!home.includes('/assets/editorial-theme.css')||!home.includes('fonts.googleapis.com'))errors.push('Editorial typography stylesheet absent '+lang);
 if(home.includes('class="hero-visual"')||home.includes('class="mini-chart"'))errors.push('Generic technology placeholder still present in editorial cover '+lang);
 const cover=(home.match(/class="hero-editorial-cover"[\s\S]*?<img[^>]*\bsrc="([^"]+)"/)||[])[1];
 const cards=[...home.matchAll(/class="card-cover-image editorial-photo"[^>]*\bsrc="([^"]+)"/g)].map(m=>m[1]);
 if(!cover||cards.length<9)errors.push('Homepage editorial photography incomplete '+lang);
 if(new Set([cover,...cards]).size!==cards.length+1)errors.push('Same article photograph repeated in journal homepage '+lang);
 if(!home.includes('/'+lang+'/markets/')||!home.includes('/'+lang+'/lifestyle/')||!home.includes('/'+lang+'/tools/'))errors.push('Journal topic rail missing useful routes '+lang);
}


// Immutable content-preservation gate: no redesign or new publication may
// silently unpublish legacy RibhLab articles or Market Pulse editorial stories.
const protectedInventory=JSON.parse(fs.readFileSync(path.join(root,'content','preserved-article-baseline.json'),'utf8'));
if(protectedInventory.legacyArticleCount!==35||protectedInventory.legacyMarketDigestCount!==6)errors.push('Preservation baseline inventory must contain 35 articles and six digests');
const legacySlugs=Object.values(protectedInventory.sections).flat();
if(legacySlugs.length!==35||new Set(legacySlugs).size!==35)errors.push('Legacy article baseline is corrupt');
if(knownSlugs.size<legacySlugs.length+4)errors.push('New articles replaced old articles instead of being appended');
for(const [sectionId,slugs] of Object.entries(protectedInventory.sections)){
 const live=taxonomy.sections.find(s=>s.id===sectionId);
 const planned=publishingPlan.sections.find(s=>s.id===sectionId);
 if(!live||!planned){errors.push('Legacy editorial section was deleted: '+sectionId);continue;}
 for(const slug of slugs){
  if(!live.publishedSlugs.includes(slug)||!planned.publishedSlugs.includes(slug)||!knownSlugs.has(slug))errors.push('Legacy article deleted or unpublished: '+slug);
  if(!photos.articlePhotos[slug])errors.push('Legacy photo lost: '+slug);
  for(const lang of ['ar','en','fr']){
   const file=path.join(dist,lang,live.parent,slug,'index.html');
   if(!fs.existsSync(file))errors.push('Legacy article URL missing after redesign: '+lang+'/'+slug);
  }
 }
}
const activeDigestIds=new Set((digests.items||[]).map(d=>d.id));
for(const id of protectedInventory.marketDigestIds){
 if(!activeDigestIds.has(id))errors.push('Legacy Market Pulse digest deleted: '+id);
 for(const lang of ['ar','en','fr']){
  if(!fs.existsSync(path.join(dist,lang,'markets','read',id,'index.html')))errors.push('Market Pulse digest URL lost: '+lang+'/'+id);
 }
}
const newlyPublished=[
 'homemade-pizza-margherita-authentic-style-recipe',
 'gentle-face-cleanser-choosing-washing-routine',
 'ai-assistant-vs-ai-agent-workflows-practical-guide',
 'why-gold-moves-with-us-dollar-real-yields-explained'
];
for(const slug of newlyPublished){
 if(!knownSlugs.has(slug)||!photos.articlePhotos[slug]||!resourceConfig.articleLinks[slug])errors.push('Added guide incompletely published: '+slug);
 const a=JSON.parse(fs.readFileSync(path.join(articleDir,slug+'.json'),'utf8'));
 for(const lang of ['ar','en','fr']){
  if((a.translations?.[lang]?.sections||[]).length<5)errors.push('New guide insufficient detail '+lang+'/'+slug);
 }
}

if(errors.length){console.error(errors.slice(0,20).join('\n'));console.error(`${errors.length} errors`);process.exit(1);}
console.log(`PASS: ${pages.length} HTML files, ${checked} internal links/assets, translated article pages, search indexes and static pages.`);

