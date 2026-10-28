import fs from "node:fs";
const file="content/feeds/latest.json";
const q={crypto:"bitcoin ethereum crypto regulations when:3d",new_tokens:"new token listed exchange Coinbase Binance Kraken when:7d",gold:"gold bullion central bank gold when:3d",us_macro:"Federal Reserve US CPI US payrolls when:3d",europe:"ECB eurozone inflation when:4d",japan:"Bank of Japan yen policy when:4d",china:"China GDP economic data PBOC when:4d",geopolitics:"oil supply sanctions geopolitical markets when:4d",ai_future:"AI industry chips jobs regulations when:5d",digital_income:"creator economy freelancing online business when:5d"};
const decode=s=>String(s||"").replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g,"$1").replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&#(\d+);/g,(_,x)=>String.fromCodePoint(Number(x))).replace(/<[^>]*>/g," ").replace(/\s+/g," ").trim();
const tag=(s,t)=>{const m=s.match(new RegExp("<"+t+"(?:\\s[^>]*)?>([\\s\\S]*?)<\\/"+t+">","i"));return m?decode(m[1]):""};
async function run(t,query){const qs=new URLSearchParams({q:query,hl:"en-US",gl:"US",ceid:"US:en"});const r=await fetch("https://news.google.com/rss/search?"+qs,{signal:AbortSignal.timeout(12000)});if(!r.ok)throw new Error("HTTP "+r.status);const xml=await r.text(),items=[];for(const m of xml.matchAll(/<item(?:\s[^>]*)?>([\s\S]*?)<\/item>/gi)){const x=m[1],title=tag(x,"title").slice(0,245),url=tag(x,"link"),dt=new Date(tag(x,"pubDate"));if(!title||!/^https:\/\//.test(url)||!Number.isFinite(dt.getTime()))continue;if(Date.now()-dt.getTime()>10*86400000)continue;items.push({id:t+"-"+dt.getTime()+"-"+items.length,topic:t,title,url,source:tag(x,"source")||"External news publisher",publishedAt:dt.toISOString()});if(items.length>=6)break;}return items}
const batches=await Promise.allSettled(Object.entries(q).map(([t,query])=>run(t,query)));
const candidates=batches.filter(x=>x.status==="fulfilled"&&x.value.length).flatMap(x=>x.value);
const normalize=s=>String(s||"").toLocaleLowerCase().normalize("NFKC").replace(/[^\\p{L}\\p{N}]+/gu," ").replace(/\\s+/g," ").trim();
const unique=new Set(),good=[],counts=new Map();
for(const item of candidates.sort((a,b)=>b.publishedAt.localeCompare(a.publishedAt))){
 const key=normalize(item.title)+"|"+normalize(item.source);
 if(unique.has(key)||counts.get(item.topic)>=5)continue;
 if(new Date(item.publishedAt).getTime()>Date.now()+5*60*1000)continue;
 unique.add(key);good.push(item);counts.set(item.topic,(counts.get(item.topic)||0)+1);
}
if(good.length){
 const latest=fs.existsSync(file)?JSON.parse(fs.readFileSync(file,"utf8")):null;
 const oldKeys=(latest?.items||[]).map(h=>normalize(h.title)+"|"+normalize(h.source));
 const added=good.filter(h=>!oldKeys.includes(normalize(h.title)+"|"+normalize(h.source))).length;
 fs.writeFileSync(file,JSON.stringify({fetchedAt:new Date().toISOString(),mode:"externally-attributed-RSS-headlines",newItemsSinceLastRefresh:added,items:good},null,2)+"\n");
 console.log("Market Pulse: published",good.length,"uniquely attributed headlines;",added,"new since prior feed.");
}else console.warn("RSS unavailable or empty; retaining dated fallback, not inventing fresh headlines.");