/* RibhLab course archive admin module.
   This is a client-only editor: the password is a UI gate, GitHub permissions
   remain the real authorization for all repository mutations.
   Credentials are kept in ephemeral JavaScript memory and only sent to GitHub API. */
(() => {
"use strict";
const PRIVATE_REPO="univcours/rdp", PRIVATE_BRANCH="wa-econometrie-s5-2026";
const SITE_REPO="ribhlab/ribhlab.github.io", SITE_BRANCH="main";
const MANIFEST_PATH="manifest.json", CATALOG_PATH="public/econometrie-s5-2026/catalog.json";
const SALT_HEX="4f092cb76b41d0566e166fb31f67acf5";
const HASH_HEX="1d9431042ff3db28e2c5279b1a92532667ac4d29f00b24b3bcc2714fb15f5768";
const MAX_BYTES=20*1024*1024;
const state={unlocked:false,privateToken:"",siteToken:"",verified:false,queue:[],created:[],busy:false,failed:0,blockedUntil:0};
const $=s=>document.getElementById(s);
const ADMIN=$("adminDialog");
if(!ADMIN)return;
const qs=s=>ADMIN.querySelector(s);
const txt=(tag,value,cls)=>{const el=document.createElement(tag);if(cls)el.className=cls;el.textContent=value;return el};
const fromHex=s=>new Uint8Array(s.match(/../g).map(h=>parseInt(h,16)));
const toHex=b=>Array.from(new Uint8Array(b),v=>v.toString(16).padStart(2,"0")).join("");
const escapelessName=s=>s.normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/[^a-zA-Z0-9\-_ .()]/g,"-").replace(/[ ]+/g," ").trim();
const slug=s=>escapelessName(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,65);
const rootSubjects=()=>[...window.courseCatalog.subjects,...state.created];
function status(msg,isError=false){const el=$("adminResult");if(!el)return;el.className="admin-progress"+(isError?" error":" success");el.textContent=msg;el.scrollIntoView({block:"nearest"});}
function fileKind(file){
 const ext=file.name.split(".").pop().toLowerCase();
 if(ext==="pdf")return "PDF";
 if(/^(jpg|jpeg|png|gif|webp|bmp|svg|mp4|webm|mov|mp3|m4a|ogg|wav)$/.test(ext))return "Media";
 return "Documents";
}
function suggestSubject(filename){
 const n=filename.toLowerCase();
 if(/micro|monopole|march[eé]|offre|demande|pareto|bien[- ]?[eê]tre|production|consommateur/.test(n))return "microeconomie";
 if(/simplexe|lin[eé]aire|graphique|recherche.op[eé]ration|\bro[-_ ]/.test(n))return "recherche-operationnelle";
 if(/probabilit|combinatoire|variable al[eé]atoire/.test(n))return "probabilites";
 if(/hypoth[eè]se|statistique|tests?[ -]moyenne/.test(n))return "tests-hypotheses";
 if(/croissance|pib/.test(n))return "croissance-economique";
 if(/anglais|english|unit [1-9]|vocabulary/.test(n))return "anglais";
 if(/juridique|droit|entreprise|contrat/.test(n))return "droit-entreprise";
 if(/plf|finance|budget|dette/.test(n))return "finances-publiques";
 if(/html|css|code|web|javascript|informatique/.test(n))return "informatique-css";
 return "annonces-divers";
}
function defaultTitle(file){
 let s=file.name.replace(/\.[^.]+$/,"").replace(/[_-]+/g," ").replace(/\s+/g," ").trim();
 if(/^(IMG|VID|WA|document|scan|image|file|whatsapp)[\s0-9().-]*$/i.test(s))return "Document "+new Date().toISOString().slice(0,10);
 return s.slice(0,130)||"Document sans titre";
}
async function matchesPassword(input){
 const key=await crypto.subtle.importKey("raw",new TextEncoder().encode(input),"PBKDF2",false,["deriveBits"]);
 const bits=await crypto.subtle.deriveBits({name:"PBKDF2",salt:fromHex(SALT_HEX),iterations:310000,hash:"SHA-256"},key,256);
 const actual=toHex(bits);let mismatch=0;for(let i=0;i<actual.length;i++)mismatch|=actual.charCodeAt(i)^HASH_HEX.charCodeAt(i);
 return mismatch===0;
}
function loginView(){
 $("adminLoginView").hidden=false;$("adminWorkspace").hidden=true;
 $("adminPassword").value="";
 $("adminPassword").focus();
 status("");
}
function workspaceView(){
 $("adminLoginView").hidden=true;$("adminWorkspace").hidden=false;
 fillDefaultSubjects();drawQueue();
}
function openAdmin(){
 if(!ADMIN.open)ADMIN.showModal();
 if(state.unlocked)workspaceView();else loginView();
}
function closeAdmin(){if(ADMIN.open)ADMIN.close();}
async function unlock(e){
 e.preventDefault();
 if(Date.now()<state.blockedUntil){status("Trop d'essais. Réessayez plus tard.",true);return;}
 const value=$("adminPassword").value;$("adminPassword").value="";
 try{
  const ok=await matchesPassword(value);
  if(!ok){state.failed++;if(state.failed>=5){state.blockedUntil=Date.now()+90_000;state.failed=0;}status("Mot de passe incorrect.",true);return;}
  state.unlocked=true;state.failed=0;workspaceView();status("Accès à l'éditeur ouvert. La publication nécessite aussi une autorisation GitHub.");
 }catch(err){status("Vérification impossible : "+err.message,true);}
}
function logOut(){
 state.unlocked=false;state.privateToken="";state.siteToken="";state.verified=false;
 $("adminPrivateToken").value="";$("adminSiteToken").value="";
 loginView();
}
function fillDefaultSubjects(){
 const list=$("adminDefaultSubject"),current=list.value;
 list.replaceChildren();
 for(const s of rootSubjects()){
  const opt=new Option(s.name,s.id);list.add(opt);
 }
 if([...list.options].some(o=>o.value===current))list.value=current;
}
function subjectSelect(value){
 const sel=document.createElement("select");
 for(const s of rootSubjects())sel.add(new Option(s.name,s.id));
 sel.value=[...sel.options].some(x=>x.value===value)?value:"annonces-divers";
 return sel;
}
function drawQueue(){
 const root=$("adminQueue");root.replaceChildren();
 $("adminQueuedCount").textContent=state.queue.length+" fichier(s) en attente";
 state.queue.forEach((entry,index)=>{
  const card=document.createElement("div");card.className="admin-file-card";
  const left=document.createElement("label");left.className="admin-field";
  const origin=txt("span",entry.file.name+" · "+(entry.file.size/1048576).toFixed(2)+" Mo","origin");
  const title=txt("span","Nom du fichier");
  const input=document.createElement("input");input.value=entry.title;input.maxLength=150;input.required=true;input.autocomplete="off";
  input.addEventListener("input",()=>entry.title=input.value);
  left.append(origin,title,input);
  const mid=document.createElement("label");mid.className="admin-field";mid.append(txt("span","Matière"));
  const select=subjectSelect(entry.subject);select.addEventListener("change",()=>entry.subject=select.value);mid.append(select);
  const remove=document.createElement("button");remove.className="remove";remove.type="button";remove.textContent="Supprimer";remove.title="Retirer de la sélection";
  remove.addEventListener("click",()=>{state.queue.splice(index,1);drawQueue();});card.append(left,mid,remove);root.append(card);
 });
 $("adminPublish").disabled=state.busy||state.queue.length===0;
}
function enqueue(fileList){
 const files=Array.from(fileList||[]);let tooLarge=[];
 for(const file of files){
  if(!file.name||file.size===0)continue;
  if(file.size>MAX_BYTES){tooLarge.push(file.name);continue;}
  const subject=suggestSubject(file.name);
  state.queue.push({file,title:defaultTitle(file),subject:rootSubjects().some(s=>s.id===subject)?subject:($("adminDefaultSubject").value||"annonces-divers")});
 }
 drawQueue();
 if(tooLarge.length)status("Fichiers de plus de 20 Mo non ajoutés : "+tooLarge.join(", "),true);
 else if(files.length)status(files.length+" fichier(s) reçu(s). Vérifiez les titres et matières avant de publier.");
}
function createSubject(e){
 e.preventDefault();
 const name=$("adminNewSubjectName").value.trim().slice(0,90),desc=$("adminNewSubjectDesc").value.trim().slice(0,160);
 if(name.length<3){status("Donnez un nom de matière de 3 caractères minimum.",true);return;}
 const id=slug(name);
 if(!id){status("Nom de matière non valide.",true);return;}
 if(rootSubjects().some(s=>s.id===id)){status("Cette matière existe déjà. Sélectionnez-la dans la liste.",true);return;}
 state.created.push({id,name,description:desc||"Documents et supports de cours"});
 $("adminNewSubjectName").value="";$("adminNewSubjectDesc").value="";
 fillDefaultSubjects();$("adminDefaultSubject").value=id;drawQueue();
 status("Matière « "+name+" » ajoutée à votre session. Elle sera créée dans GitHub lors de la publication.");
}
const apiUrl=(repo,path,ref)=>"https://api.github.com/repos/"+repo+"/contents/"+path.split("/").map(encodeURIComponent).join("/")+(ref?"?ref="+encodeURIComponent(ref):"");
async function githubRequest(repo,path,branch,token,method="GET",payload){
 const headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"};
 if(method!=="GET")headers["Content-Type"]="application/json";
 const response=await fetch(apiUrl(repo,path,method==="GET"?branch:null),{method,headers,body:payload?JSON.stringify(payload):undefined,mode:"cors",cache:"no-store"});
 let body;try{body=await response.json();}catch{body={};}
 if(!response.ok){
  const message=(body?.message||response.statusText||"HTTP error");
  throw new Error(repo+" — HTTP "+response.status+" : "+message);
 }
 return body;
}
const utf8ToBase64=text=>{
 const bytes=new TextEncoder().encode(text);let binary="";
 for(let i=0;i<bytes.length;i+=16_384)binary+=String.fromCharCode(...bytes.subarray(i,i+16_384));
 return btoa(binary);
};
const base64ToUtf8=encoded=>{
 const binary=atob((encoded||"").replace(/\s/g,""));const bytes=Uint8Array.from(binary,v=>v.charCodeAt(0));
 return new TextDecoder().decode(bytes);
};
async function tokenCheck(){
 if(!state.unlocked)return;
 const privateToken=$("adminPrivateToken").value.trim(),siteToken=$("adminSiteToken").value.trim()||privateToken;
 if(!privateToken){status("Saisissez un token GitHub autorisé à écrire dans l'archive privée.",true);return;}
 $("adminCheckToken").disabled=true;status("Vérification des accès aux deux dépôts…");
 try{
  await githubRequest(PRIVATE_REPO,MANIFEST_PATH,PRIVATE_BRANCH,privateToken);
  await githubRequest(SITE_REPO,CATALOG_PATH,SITE_BRANCH,siteToken);
  state.privateToken=privateToken;state.siteToken=siteToken;state.verified=true;
  $("adminPrivateToken").value="";$("adminSiteToken").value="";
  status("✓ Dépôt privé et catalogue public accessibles. Les tokens restent seulement dans la mémoire de cette page.");
 }catch(err){state.verified=false;status("Accès refusé : "+err.message+"\nUn token peut être nécessaire pour chaque propriétaire GitHub.",true);}
 finally{$("adminCheckToken").disabled=false;}
}
function checkName(raw,ext){
 let n=escapelessName(raw.trim());
 n=n.replace(/\.[a-z0-9]{1,8}$/i,"").replace(/\.+/g,".").trim();
 if(!n)n="Document-"+Date.now();
 return n.slice(0,145)+"."+ext;
}
function extension(file){
 const x=(file.name.split(".").pop()||"").toLowerCase();
 return /^[a-z0-9]{1,8}$/.test(x)?x:"bin";
}
async function fileBase64(file){
 const bytes=new Uint8Array(await file.arrayBuffer());let all="";
 for(let i=0;i<bytes.length;i+=8192)all+=String.fromCharCode(...bytes.subarray(i,i+8192));
 return btoa(all);
}
async function fileHash(file){
 const b=await crypto.subtle.digest("SHA-256",await file.arrayBuffer());return toHex(b);
}
function buildPublic(manifest){
 return {version:2,updatedAt:new Date().toISOString(),
 subjects:(manifest.subject_order||[]).map(id=>({id,...manifest.subjects[id]})).filter(x=>x.name),
 files:Object.entries(manifest.categories||{}).flatMap(([kind,items])=>items.map(x=>({name:x.name,title:x.title||x.name,path:x.path,subject:x.subject,bytes:x.bytes,kind,sha256:x.sha256,encrypted_path:x.encrypted_path||null}))),
 unavailable:{documents:manifest.unavailable_documents?.length||0,media:manifest.unavailable_media?.length||0}};
}
async function publishFiles(){
 if(state.busy)return;
 if(!state.unlocked){status("Session Admin fermée.",true);return;}
 if(!state.verified){status("Connectez les deux dépôts GitHub avant de publier.",true);return;}
 if(!state.queue.length){status("Sélectionnez au moins un fichier.",true);return;}
 await window.courseVaultWait?.();
 if(!window.courseVaultReady?.()){status("Ouvrez d'abord la bibliothèque avec votre lien d'accès privé pour chiffrer les nouveaux fichiers.",true);return;}
 state.busy=true;$("adminPublish").disabled=true;
 const succeeded=[],failures=[];let publicUpdated=false,manifestUpdated=false;
 try{
  const current=await githubRequest(PRIVATE_REPO,MANIFEST_PATH,PRIVATE_BRANCH,state.privateToken);
  const manifest=JSON.parse(base64ToUtf8(current.content));
  manifest.subjects ||= {};manifest.subject_order ||= [];manifest.categories ||= {};
  for(const subject of state.created){
   if(!manifest.subjects[subject.id]){manifest.subjects[subject.id]={name:subject.name,description:subject.description};manifest.subject_order.push(subject.id);}
  }
  const allFiles=Object.values(manifest.categories).flat();
  const paths=new Set(allFiles.map(x=>x.path));
  for(let i=0;i<state.queue.length;i++){
   const q=state.queue[i];
   try{
    if(!manifest.subjects[q.subject])throw Error("La matière n'existe pas : "+q.subject);
    const title=q.title.trim();if(!title)throw Error("Titre vide.");
    const hash=await fileHash(q.file);
    if(allFiles.some(f=>f.sha256===hash)){failures.push(q.file.name+" : fichier déjà présent (SHA-256 identique)");continue;}
    const kind=fileKind(q.file),ext=extension(q.file);
    let filename=checkName(title,ext),path="files/"+kind+"/"+q.subject+"/"+filename;
    let n=2;
    while(paths.has(path)){
     filename=checkName(title,ext).replace(new RegExp("\\."+ext+"$")," ("+(n++)+")."+ext);
     path="files/"+kind+"/"+q.subject+"/"+filename;
    }
    status("Chiffrement et envoi "+(i+1)+"/"+state.queue.length+" : "+filename);
    const vaultPath="public/econometrie-s5-2026/vault/"+hash+".rbl";
    const encryptedPath="/econometrie-s5-2026/vault/"+hash+".rbl";
    let vaultExists=false;
    try{await githubRequest(SITE_REPO,vaultPath,SITE_BRANCH,state.siteToken);vaultExists=true;}
    catch(e){if(!e.message.includes("HTTP 404"))throw e;}
    if(!vaultExists){
      const encrypted=await window.courseVaultEncrypt(q.file);
      await githubRequest(SITE_REPO,vaultPath,SITE_BRANCH,state.siteToken,"PUT",{message:"Encrypted S5 attachment: "+hash.slice(0,12),branch:SITE_BRANCH,content:encrypted});
    }
    const data=await fileBase64(q.file);
    await githubRequest(PRIVATE_REPO,path,PRIVATE_BRANCH,state.privateToken,"PUT",{message:"Archive S5: add "+filename,branch:PRIVATE_BRANCH,content:data});
    manifest.categories[kind] ||= [];
    manifest.categories[kind].push({original_name:q.file.name,name:filename,title,subject:q.subject,path,bytes:q.file.size,sha256:hash,encrypted_path:encryptedPath,source:"admin",uploaded_at:new Date().toISOString()});
    paths.add(path);allFiles.push({path,sha256:hash});
    succeeded.push({path,file:q.file,title});
   }catch(err){failures.push(q.file.name+" : "+err.message);}
  }
  if(!succeeded.length&&!state.created.length){throw Error(failures.join("\n")||"Aucune modification.");}
  await githubRequest(PRIVATE_REPO,MANIFEST_PATH,PRIVATE_BRANCH,state.privateToken,"PUT",{
   message:"Archive S5: update subjects and attachment manifest",branch:PRIVATE_BRANCH,content:utf8ToBase64(JSON.stringify(manifest,null,2)),sha:current.sha
  });
  manifestUpdated=true;
  const newCatalog=buildPublic(manifest);
  const publicFile=await githubRequest(SITE_REPO,CATALOG_PATH,SITE_BRANCH,state.siteToken);
  await githubRequest(SITE_REPO,CATALOG_PATH,SITE_BRANCH,state.siteToken,"PUT",{
   message:"Update Économétrie S5 catalogue after admin uploads",branch:SITE_BRANCH,sha:publicFile.sha,content:utf8ToBase64(JSON.stringify(newCatalog,null,2))
  });
  publicUpdated=true;
  for(const item of succeeded)window.courseLocalAdminFiles.set(item.path,item.file);
  window.courseReplaceCatalog(newCatalog);
  state.queue=state.queue.filter(q=>!succeeded.some(s=>s.file===q.file));
  state.created=[];
  fillDefaultSubjects();drawQueue();
  status("✓ "+succeeded.length+" fichier(s) enregistrés dans le dépôt privé. Catalogue public mis à jour. GitHub Pages doit publier le nouveau catalogue."+(failures.length?"\nÀ revoir : "+failures.join("\n"):""));
 }catch(err){
  status("Publication incomplète : "+err.message+"\n"+
   (manifestUpdated?"Les fichiers et le manifeste privé ont été modifiés.":"Vérifiez les envois avant de réessayer.")+
   (publicUpdated?"":" Le catalogue public n'a peut-être pas été synchronisé.")+
   (failures.length?"\n"+failures.join("\n"):""),true);
 }finally{state.busy=false;drawQueue();}
}
function render(){
 ADMIN.innerHTML=`<div class="admin-shell">
 <div class="admin-head"><div><strong>🔐 Administration · Économétrie S5</strong><p>Ajouter des documents par matière dans l'archive privée.</p></div><button class="close-admin" type="button" id="adminClose" aria-label="Fermer">✕</button></div>
 <div class="admin-content">
  <section id="adminLoginView" class="admin-section admin-login">
    <h3>Accès administrateur</h3><p>Saisissez le mot de passe choisi pour accéder à la gestion des fichiers.</p>
    <form id="adminLoginForm"><label class="admin-field">Mot de passe
     <input id="adminPassword" type="password" autocomplete="off" required placeholder="Mot de passe administrateur"></label>
     <button type="submit" class="admin-button">Se connecter</button></form>
    <div class="admin-security">La page est statique : ce mot de passe ouvre l'interface, mais <strong>ne remplace pas l'autorisation GitHub</strong>. L'ajout réel de fichiers exige un token GitHub autorisé. Aucun mot de passe en clair ou token n'est publié sur le site.</div>
  </section>
  <section id="adminWorkspace" hidden>
   <div class="admin-section">
    <div class="admin-options"><div><h3>1 · Connecter GitHub</h3><p>Autoriser l'ajout dans le dépôt privé et l'actualisation des cartes.</p></div><button class="admin-button secondary" type="button" id="adminLogout">Déconnexion Admin</button></div>
    <div class="admin-security">Utilisez des tokens GitHub <strong>fine-grained</strong> avec <strong>Contents: Read and write</strong>, uniquement sur les dépôts <code>univcours/rdp</code> et <code>ribhlab/ribhlab.github.io</code>. Si les dépôts ont des propriétaires différents, renseignez deux tokens. Ils restent uniquement en mémoire pendant cette session.</div>
    <div class="admin-grid">
      <label class="admin-field">Token archive privée (univcours/rdp)
      <input id="adminPrivateToken" type="password" autocomplete="off" placeholder="github_pat_…"></label>
      <label class="admin-field">Token site public (ribhlab.github.io) · facultatif si même accès
      <input id="adminSiteToken" type="password" autocomplete="off" placeholder="Laisser vide si même token"></label>
    </div>
    <div class="admin-form-row"><button type="button" id="adminCheckToken" class="admin-button secondary">Vérifier les accès GitHub</button><span class="admin-note">Les fichiers originaux resteront dans GitHub Private.</span></div>
   </div>
   <div class="admin-section">
     <h3>2 · Ajouter des fichiers</h3><p>PDF, images, vidéos, documents Office, audio et textes (20 Mo par fichier maximum).</p>
     <label class="admin-upload-target" id="adminDropZone" for="adminInput"><strong>📂 Choisissez ou déposez les fichiers</strong><small>Vous pouvez en sélectionner plusieurs.</small></label>
     <input id="adminInput" type="file" multiple hidden accept=".pdf,.jpg,.jpeg,.png,.webp,.gif,.mp4,.webm,.mp3,.m4a,.ogg,.wav,.txt,.csv,.json,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.zip">
     <label class="admin-field" style="margin-top:12px">Catégorie proposée pour les nouveaux fichiers
      <select id="adminDefaultSubject"></select></label>
     <div id="adminQueue" class="admin-list"></div>
     <span id="adminQueuedCount" class="admin-counter">0 fichier(s) en attente</span>
   </div>
   <div class="admin-section">
     <h3>3 · Créer une nouvelle matière</h3><p>Si la catégorie n'existe pas, créez-la ici puis affectez les fichiers concernés.</p>
     <form id="adminCreateSubjectForm">
       <div class="admin-subject-row">
        <label class="admin-field">Nom de la matière
         <input id="adminNewSubjectName" maxlength="90" placeholder="Ex. Économétrie avancée"></label>
        <label class="admin-field">Description courte
         <input id="adminNewSubjectDesc" maxlength="160" placeholder="Cours, TD, exercices…"></label>
       </div><button type="submit" class="admin-button secondary">＋ Créer cette matière</button>
     </form>
   </div>
   <div class="admin-upload-actions"><button id="adminPublish" class="admin-button" type="button">⬆ Publier dans GitHub</button></div>
   <p class="admin-warning">Les documents ajoutés restent privés dans GitHub ; le site public affiche uniquement la liste des titres. Les nouveaux fichiers sont chiffrés : les détenteurs du lien privé les verront sans ZIP.</p>
  </section>
  <div id="adminResult" role="status" aria-live="polite" class="admin-progress"></div>
 </div></div>`;
 $("adminClose").onclick=closeAdmin;
 $("adminLoginForm").addEventListener("submit",unlock);
 $("adminLogout").onclick=logOut;
 $("adminCheckToken").onclick=tokenCheck;
 $("adminInput").onchange=e=>{enqueue(e.target.files);e.target.value="";};
 $("adminCreateSubjectForm").addEventListener("submit",createSubject);
 $("adminPublish").onclick=publishFiles;
 const drop=$("adminDropZone");
 drop.addEventListener("dragover",e=>{e.preventDefault();drop.classList.add("drag");});
 drop.addEventListener("dragleave",()=>drop.classList.remove("drag"));
 drop.addEventListener("drop",e=>{e.preventDefault();drop.classList.remove("drag");enqueue(e.dataTransfer.files);});
}
render();
$("openAdmin").addEventListener("click",openAdmin);
ADMIN.addEventListener("click",event=>{if(event.target===ADMIN)closeAdmin();});
})();