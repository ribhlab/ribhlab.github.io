// Stable one-to-one short URL migration for GitHub Pages.
// Old deep links stay reachable as instant HTML redirects because Pages does
// not expose per-route server-side HTTP 301 rules. Do not discard aliases.
import fs from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';

export const MAX_CANONICAL_PATH_LENGTH=54;
const escRe=value=>value.replace(/[.*+?^\x24{}()|[\]\\]/g,'\\$&');
const htmlEsc=value=>String(value).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;');
const fileFor=(dist,route)=>path.join(dist,route.replace(/^\//,''),'index.html');

function shortRoute(route,maxLength){
 if(route.length<=maxLength)return route;
 const match=route.match(/^\/(ar|en|fr)\/(.+)\/$/);
 if(!match)throw Error('Cannot shorten nonlocalized route: '+route);
 const parts=match[2].split('/');
 if(parts.length<2)throw Error('Long route has no category: '+route);
 const oldSlug=parts.pop();
 const prefix='/'+match[1]+'/'+parts.join('/')+'/';
 const hash=createHash('sha256').update(parts.join('/')+'/'+oldSlug).digest('hex').slice(0,7);
 const available=maxLength-prefix.length-1;
 if(available<12)throw Error('Route nesting too deep to shorten: '+route);
 const firstWords=oldSlug.split('-').slice(0,2).join('-');
 const human=firstWords.slice(0,available-hash.length-1).replace(/-+$/,'');
 if(human.length<2)throw Error('Could not create human-readable slug: '+route);
 return prefix+human+'-'+hash+'/';
}

export function shortenGeneratedRoutes({dist,domain,routes,generatedRoutes}){
 if(!domain)throw Error('Short URL migration requires the canonical SITE_URL');
 const source=[...new Set(generatedRoutes)];
 const occupied=new Set(source);
 const mapping=new Map();
 const targets=new Set();
 for(const original of source){
  const shorter=shortRoute(original,MAX_CANONICAL_PATH_LENGTH);
  if(shorter===original)continue;
  if(occupied.has(shorter)||targets.has(shorter))throw Error('Short URL collision: '+original+' -> '+shorter);
  if(!fs.existsSync(fileFor(dist,original)))throw Error('Old route missing before migration: '+original);
  mapping.set(original,shorter);targets.add(shorter);
 }
 if(!mapping.size){
  fs.writeFileSync(path.join(dist,'assets','short-url-map.json'),'[]\n');
  return {migrated:0,maxLength:MAX_CANONICAL_PATH_LENGTH};
 }
 const pattern=new RegExp([...mapping.keys()].sort((a,b)=>b.length-a.length).map(escRe).join('|'),'g');
 const replaceLinks=source=>source.replace(pattern,hit=>mapping.get(hit)||hit);
 function visit(dir){
  return fs.readdirSync(dir,{withFileTypes:true}).flatMap(entry=>
   entry.isDirectory()?visit(path.join(dir,entry.name)):[path.join(dir,entry.name)]);
 }
 // Update every internal link, hreflang, canonical, schema.org URL and search entry
 // before writing the new canonical copies.
 for(const filepath of visit(dist)){
  if(!filepath.endsWith('.html')&&!/\/assets\/search-(ar|en|fr)\.json$/.test(filepath))continue;
  const old=fs.readFileSync(filepath,'utf8'),updated=replaceLinks(old);
  if(old!==updated)fs.writeFileSync(filepath,updated,'utf8');
 }
 for(const [original,shorter] of mapping){
  const oldPath=fileFor(dist,original),newPath=fileFor(dist,shorter);
  const html=fs.readFileSync(oldPath,'utf8');
  // Full original content lives at the new canonical route.
  fs.mkdirSync(path.dirname(newPath),{recursive:true});
  fs.writeFileSync(newPath,html,'utf8');
  // Old backlinks still work and Google may treat instant HTML refresh as
  // permanent. Never load advertising code on a redirecting alias.
  const bare=html.replace(/<script async src="https:\/\/pagead2\.googlesyndication\.com\/pagead\/js\/adsbygoogle\.js\?client=[^"]+" crossorigin="anonymous"><\/script>/g,'');
  const redirected=bare.replace('</head>','<meta http-equiv="refresh" content="0; url='+htmlEsc(domain+shorter)+'"></head>');
  if(redirected===bare)throw Error('Alias head missing: '+original);
  fs.writeFileSync(oldPath,redirected,'utf8');
 }
 for(const row of routes)if(mapping.has(row.route))row.route=mapping.get(row.route);
 const result=[...mapping].map(([oldRoute,newRoute])=>({oldRoute,newRoute}));
 fs.writeFileSync(path.join(dist,'assets','short-url-map.json'),JSON.stringify(result,null,2)+'\n');
 return {migrated:mapping.size,maxLength:MAX_CANONICAL_PATH_LENGTH};
}
