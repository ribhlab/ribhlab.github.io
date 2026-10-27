/**
 * Chromium-based responsive smoke test, no external npm dependencies.
 * Checks rendered pages in Arabic, English and French at 320–1440px.
 */
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import {spawn,spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const dist=path.join(root,'dist');
const siteUrl=process.env.SITE_URL||'https://ribhlab.github.io';
const basePath=new URL(siteUrl).pathname.replace(/\/$/,'');
const fullRoute=(lang,route)=>basePath+'/'+lang+route;
if(!fs.existsSync(dist))throw Error('Run npm run build first');
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const executable=[process.env.CHROME_BIN,'google-chrome','google-chrome-stable','chromium','chromium-browser'].filter(Boolean)
 .map(name=>{const r=spawnSync('which',[name],{encoding:'utf8'});return r.status===0?r.stdout.trim():null;}).find(Boolean);
if(!executable)throw Error('No Google Chrome or Chromium found: browser viewport checks required');
const mimetypes={'.html':'text/html','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg'};
const server=http.createServer((req,res)=>{
 try{
  let name=decodeURIComponent(new URL(req.url,'http://127.0.0.1').pathname);
  if(basePath && (name===basePath||name.startsWith(basePath+'/')))name=name.slice(basePath.length)||'/';
  let file=path.resolve(dist,'.'+name);
  if(file!==dist&&!file.startsWith(dist+path.sep)){res.writeHead(403);res.end();return;}
  if(!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  if(fs.statSync(file).isDirectory())file=path.join(file,'index.html');
  if(!fs.existsSync(file)){res.writeHead(404);res.end();return;}
  res.writeHead(200,{'Content-Type':mimetypes[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});
  fs.createReadStream(file).pipe(res);
 }catch{res.writeHead(500);res.end();}
});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const sitePort=server.address().port;
const profile=fs.mkdtempSync(path.join(os.tmpdir(),'ribhlab-chrome-'));
const chrome=spawn(executable,['--headless=new','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--disable-extensions','--no-first-run','--disable-background-networking','--remote-allow-origins=*','--remote-debugging-port=0','--user-data-dir='+profile,'about:blank'],{stdio:'ignore'});
const pending=new Map();
let socket=null,sequence=0,failed=0,checked=0;
const fail=text=>{failed++;console.error('FAIL: '+text);};
try{
 let debugPort=0;
 for(let i=0;i<120;i++){
  const f=path.join(profile,'DevToolsActivePort');
  if(fs.existsSync(f)){debugPort=Number(fs.readFileSync(f,'utf8').split('\n')[0]);break;}
  if(chrome.exitCode!==null)throw Error('Chrome exited before debugger startup');
  await pause(100);
 }
 if(!debugPort)throw Error('Chrome debugger unavailable');
 const response=await fetch('http://127.0.0.1:'+debugPort+'/json/new?about:blank',{method:'PUT'}).then(r=>r.json());
 socket=new WebSocket(response.webSocketDebuggerUrl);
 await new Promise((resolve,reject)=>{socket.onopen=resolve;socket.onerror=reject;});
 socket.onmessage=event=>{
  const msg=JSON.parse(event.data);
  if(!msg.id)return;
  const p=pending.get(msg.id);
  if(!p)return;
  pending.delete(msg.id);
  clearTimeout(p.timeout);
  if(msg.error)p.reject(Error(msg.error.message));
  else p.resolve(msg.result);
 };
 const cdp=(method,params={})=>new Promise((resolve,reject)=>{
  const id=++sequence,timeout=setTimeout(()=>{pending.delete(id);reject(Error(method+' timed out'));},9000);
  pending.set(id,{resolve,reject,timeout});
  socket.send(JSON.stringify({id,method,params}));
 });
 const evalJS=async expression=>{
  const r=await cdp('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  if(r.exceptionDetails)throw Error(r.result?.description||r.exceptionDetails.text||'Runtime evaluation failed');
  return r.result?.value;
 };
 await cdp('Page.enable');await cdp('Runtime.enable');
 const pages=['/','/archive/','/markets/','/opportunities/','/opportunities/morocco/','/opportunities/visa-appointments/','/audience/','/tools/','/tools/document-studio/','/lifestyle/homemade-pizza-margherita-authentic-style-recipe/'];
 const cases=[];
 for(const lang of ['ar','en','fr']){
  for(const width of [320,390,768,1024,1440])cases.push({lang,width,route:'/'});
  for(const route of pages.slice(1))cases.push({lang,width:320,route});
  cases.push({lang,width:768,route:'/tools/document-studio/'});
  cases.push({lang,width:768,route:'/archive/'});
 }
 const inspect='(()=>{const w=innerWidth,selectors=[".header",".nav-inner","#main",".hero-grid",".article-grid",".archive-page",".market-digest-grid",".isolated-tool-layout",".studio-pro",".studio-editor",".studio-preview-panel",".footer-grid"],bad=[];for(const sel of selectors){const el=document.querySelector(sel);if(!el||getComputedStyle(el).display==="none")continue;const r=el.getBoundingClientRect();if(r.width>0&&(r.left < -3 || r.right>w+3))bad.push(sel+":"+r.left.toFixed(0)+".."+r.right.toFixed(0));}return {w,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth,bad,lang:document.documentElement.lang,images:[...document.querySelectorAll(".article-card img.card-cover-image")].every(img=>img.hasAttribute("alt")&&!!img.getAttribute("src"))};})()';
 for(const test of cases){
  const label=test.lang+test.route+' @ '+test.width+'px';
  try{
   await cdp('Emulation.setDeviceMetricsOverride',{width:test.width,height:900,deviceScaleFactor:1,mobile:test.width<=768});
   const nav=await cdp('Page.navigate',{url:'http://127.0.0.1:'+sitePort+fullRoute(test.lang,test.route)});
   if(nav.errorText)throw Error(nav.errorText);
   let ready=false;
   for(let count=0;count<50;count++){
    if(await evalJS('document.readyState!=="loading" && window.location.pathname==='+JSON.stringify(fullRoute(test.lang,test.route))+' && !!document.querySelector("#main") && !!document.querySelector("link[href*=responsive]")')){ready=true;break;}
    await pause(80);
   }
   if(!ready)throw Error('responsive HTML failed to load');
   await pause(100);
   const info=await evalJS(inspect);
   if(info.lang!==test.lang)fail(label+': wrong locale '+info.lang);
   if(Math.abs(info.w-test.width)>2)fail(label+': CSS viewport unexpectedly '+info.w);
   if(info.scroll>test.width+2||info.body>test.width+2)fail(label+': horizontal document overflow '+info.scroll+'/'+info.body);
   if(info.bad.length)fail(label+': clipped layout containers '+info.bad.join(', '));
   if(!info.images)fail(label+': story cards lack descriptive images');
   if(test.width===320&&test.route==='/'){
    const state=await evalJS('(()=>{const b=document.querySelector(".mobile-menu"),n=document.querySelector("#site-nav");if(!b||!n)return {ok:false};b.click();const open=b.getAttribute("aria-expanded")==="true"&&getComputedStyle(n).display!=="none";const rect=n.getBoundingClientRect();document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}));return {ok:open&&b.getAttribute("aria-expanded")==="false"&&getComputedStyle(n).display==="none"&&rect.left>=-2&&rect.right<=innerWidth+2};})()');
    if(!state.ok)fail(label+': mobile menu fails to open/close within viewport');
   }
   if(test.width===320&&test.route==='/archive/'){
    const search=await evalJS('(()=>{const i=document.querySelector("#archive-search"),o=document.querySelector("[data-archive-count]"),e=document.querySelector("[data-archive-empty]");if(!i||!o||!e)return false;i.value="__no_matches__";i.dispatchEvent(new Event("input",{bubbles:true}));return o.textContent.startsWith("0")&&!e.hidden;})()');
    if(!search)fail(label+': archive live search not functional');
   }
   if(test.width===320&&test.route==='/tools/document-studio/'){
    const status=await evalJS('(()=>{const e=document.querySelector("#document-studio"),p=document.querySelector("#studio-preview");return !!e&&!!p&&document.querySelectorAll(".studio-action-buttons button").length>=4&&e.getBoundingClientRect().width<=innerWidth+2;})()');
    if(!status)fail(label+': Document Studio controls missing or too wide');
   }
   if(test.lang==='ar'&&((test.route==='/'&&[390,1440].includes(test.width))||(test.route==='/tools/document-studio/'&&test.width===320))){
    const img=await cdp('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});
    const out=path.join(dist,'responsive-previews');
    fs.mkdirSync(out,{recursive:true});
    const kind=test.route==='/'?'home':'studio';
    fs.writeFileSync(path.join(out,kind+'-'+test.width+'.png'),Buffer.from(img.data,'base64'));
   }
   checked++;
   console.log('PASS '+label);
  }catch(err){fail(label+': '+String(err.message||err));}
 }
 console.log('Responsive Chromium checks complete: '+checked+' passed, '+failed+' failed');
 if(failed)process.exitCode=1;
}finally{
 for(const p of pending.values())clearTimeout(p.timeout);
 if(socket)socket.close();
 chrome.kill('SIGTERM');
 server.close();
 setTimeout(()=>{try{fs.rmSync(profile,{force:true,recursive:true,maxRetries:7,retryDelay:180});}catch{}},1500).unref();
}
