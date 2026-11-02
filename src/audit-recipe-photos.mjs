/**
 * Offline, reproducible audit of RibhLab's 120 recipe cards.
 * Count only published photo assignments; candidate searches never count.
 * A valid metadata record is NOT proof that all pictured ingredients match.
 */
import fs from 'node:fs';
import path from 'node:path';

const root=process.cwd(),dir=path.join(root,'content/recipes');
const read=name=>JSON.parse(fs.readFileSync(path.join(dir,name),'utf8'));
const recipes=['meals-01.json','meals-02.json','meals-03.json','meals-04.json','healthy-01.json'].flatMap(name=>read(name).recipes);
const curated=read('curated-photos.json').photos;
const library=read('photo-library.json');
const candidates=read('photo-candidates.json').photos;
const decisions=read('photo-review-decisions.json').rejected;
const rejectedPairs=new Set(Object.entries(decisions).map(([key,p])=>(p.recipeSlug||key)+'|'+p.id));
const css=fs.readFileSync(path.join(root,'public/assets/recipe-pages.css'),'utf8');
const renderer=fs.readFileSync(path.join(root,'src/recipe-pages.mjs'),'utf8');
const slugs=new Set(recipes.map(r=>r.slug));
if(recipes.length!==120||slugs.size!==120)throw Error('Expected 120 distinct recipe slugs, got '+recipes.length);
if(!/\.recipe-card img\[data-recipe-photo\][^{]*\{[^}]*object-fit:contain/.test(css))throw Error('Photo cards may be cropped');
if(!/\.recipe-photo-figure img\{[^}]*object-fit:contain/.test(css))throw Error('Recipe detail photos may be cropped');
if(!renderer.includes('youtube.com/results?search_query=')||!renderer.includes('recipe-video-link'))throw Error('YouTube search-link fallback missing');
const assigned=[...Object.entries(curated),...Object.entries(library.assignments).map(([slug,id])=>[slug,library.photos[id]])];
const ids=new Set(),urls=new Set(),seenSlugs=new Set();
for(const [slug,p] of assigned){
 if(!slugs.has(slug)||seenSlugs.has(slug)||!p)throw Error('Invalid, missing or duplicated photo assignment '+slug);
 seenSlugs.add(slug);
 const id=p.id||p.photoId;
 const url=p.url?.split('?')[0];
 if(!id||!url?.startsWith('https://')||!p.source?.startsWith('https://'))throw Error('Incomplete photo source '+slug);
 if(ids.has(id)||urls.has(url))throw Error('Reused photo '+slug);
 if(rejectedPairs.has(slug+'|'+id))throw Error('Published photo was explicitly rejected as mismatched: '+slug);
 ids.add(id);urls.add(url);
 if(p.provider==='Wikimedia Commons'&&(!['cc0','by','by-sa'].includes(p.license)||!p.licenseUrl?.startsWith('https://creativecommons.org/')))throw Error('Commons photo missing compatible license '+slug);
 if(p.provider==='Pexels'&&(p.license!=='pexels'||p.licenseUrl!=='https://www.pexels.com/license/'||!p.source.startsWith('https://www.pexels.com/photo/')||!p.photographer))throw Error('Pexels photo missing verifiable source or license '+slug);
}
for(const [slug,p] of Object.entries(candidates)){
 if(!slugs.has(slug)||seenSlugs.has(slug)||!p?.id)throw Error('Invalid candidate '+slug);
 if(rejectedPairs.has(slug+'|'+p.id))throw Error('Rejected candidate reappeared '+slug);
 if(ids.has(p.id)||urls.has(p.url?.split('?')[0]))throw Error('Candidate reuses published image '+slug);
}
const missing=recipes.filter(r=>!seenSlugs.has(r.slug)).map(r=>({slug:r.slug,title:r.title.en,kind:r.kind,hasUnreviewedCandidate:!!candidates[r.slug]}));
const report={
 checkedAt:new Date().toISOString(),
 policy:'Counts refer to uniquely assigned photographs in source data, not a complete visual audit of every ingredient or a live browser image test.',
 totalRecipes:recipes.length,
 photoBackedRecipes:assigned.length,
 commonsPhotos:Object.keys(curated).length,
 unsplashPhotos:Object.keys(library.assignments).length,
 temporaryIllustrations:missing.length,
 uniquePhotoIds:ids.size,
 uniquePhotoUrls:urls.size,
 missing,
 unreviewedCandidates:Object.keys(candidates).length,
 rejectedCandidateMatches:Object.keys(decisions).length,
 photoContainmentCSS:true,
 youtubeRecipeLinks:'YouTube search links exist as fallback; specific videos are not individually verified.',
 imageEndpointChecks:'See Check published recipe photo delivery workflow for HTTP checks.'
};
fs.writeFileSync(path.join(dir,'photo-audit.json'),JSON.stringify(report,null,2)+'\n');
console.log('PHOTO AUDIT PASS: '+assigned.length+'/120 unique source photo assignments, '+missing.length+' illustrations, '+Object.keys(candidates).length+' unreviewed candidates, '+Object.keys(decisions).length+' rejected candidate pairs');
console.log('MISSING: '+missing.map(x=>x.slug).join(', '));
