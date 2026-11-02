/**
 * Post-rebase candidate sanitizer. The research job may start before an editor
 * publishes a photo: never resurrect stale candidates after the job rebases.
 */
import fs from 'node:fs';
const base='content/recipes/',read=n=>JSON.parse(fs.readFileSync(base+n,'utf8'));
const source=read('photo-candidates.json'),curated=read('curated-photos.json').photos;
const assigned=read('photo-library.json').assignments;
const publishedIds=new Set(Object.values(curated).map(p=>p.id));
const decisions=read('photo-review-decisions.json').rejected;
const rejects=new Set(Object.entries(decisions).map(([key,p])=>(p.recipeSlug||key)+'|'+p.id));
let removed=0;
for(const [slug,p] of Object.entries(source.photos||{})){
 if(curated[slug]||assigned[slug]||publishedIds.has(p.id)||rejects.has(slug+'|'+p.id)){
  delete source.photos[slug];removed++;console.log('PRUNE stale/unapproved',slug);
 }
}
fs.writeFileSync(base+'photo-candidates.json',JSON.stringify(source,null,2)+'\n');
console.log('PRUNED',removed,'candidates after main branch update; remaining',Object.keys(source.photos||{}).length);
