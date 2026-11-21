/* Private one-click file vault for Économétrie S5.
   AES-256-GCM ciphertext is hosted as public static assets.
   The 256-bit access key is never published; it lives in URL fragment or
   a non-extractable browser CryptoKey stored on the user's own device. */
(() => {
"use strict";
const $=id=>document.getElementById(id);
let vaultKey=null;let keyPromise=null;
const pref="ribhLab-S5-private-key";
const textEncoder=new TextEncoder();
function parseAccess(input){
 const raw=String(input||"").trim();
 let candidate=raw;
 try{
   const url=new URL(raw);
   candidate=new URLSearchParams(url.hash.replace(/^#/,"")).get("access")||url.hash.slice(1)||raw;
 }catch{
   if(raw.includes("#"))candidate=new URLSearchParams(raw.split("#").pop()).get("access")||raw;
 }
 if(candidate.startsWith("access="))candidate=candidate.slice(7);
 if(!/^[a-zA-Z0-9_-]{43}$/.test(candidate))throw Error("Lien d'accès incorrect. Utilisez le lien privé transmis au propriétaire.");
 const bytes=Uint8Array.from(atob(candidate.replace(/-/g,"+").replace(/_/g,"/")+"="),c=>c.charCodeAt(0));
 if(bytes.length!==32)throw Error("Clé d'accès invalide.");
 return bytes;
}
function openDb(){
 return new Promise((resolve,reject)=>{
  const req=indexedDB.open("ribhLabS5Vault",1);
  req.onupgradeneeded=()=>{if(!req.result.objectStoreNames.contains("keys"))req.result.createObjectStore("keys",{keyPath:"id"});};
  req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
 });
}
async function saveKey(k){
 try{const db=await openDb();await new Promise((resolve,reject)=>{
  const transaction=db.transaction("keys","readwrite");
  transaction.objectStore("keys").put({id:pref,key:k});
  transaction.oncomplete=resolve;transaction.onerror=()=>reject(transaction.error);
 });db.close();}catch(e){console.warn("La clé ne peut pas être mémorisée sur cet appareil.",e);}
}
async function readKey(){
 try{const db=await openDb();const key=await new Promise((resolve,reject)=>{
  const request=db.transaction("keys","readonly").objectStore("keys").get(pref);
  request.onsuccess=()=>resolve(request.result?.key||null);request.onerror=()=>reject(request.error);
 });db.close();return key;}catch{return null;}
}
async function activate(raw,remember=true){
 const bytes=parseAccess(raw);
 const key=await crypto.subtle.importKey("raw",bytes,{name:"AES-GCM"},false,["encrypt","decrypt"]);
 let first=(window.courseCatalog?.files||[]).find(x=>x.encrypted_path);
 if(!first){
  const response=await fetch("/econometrie-s5-2026/catalog.json?refresh="+Date.now(),{cache:"no-store"});
  if(response.ok){
   const updated=await response.json();
   if(window.courseReplaceCatalog)window.courseReplaceCatalog(updated);
   first=(window.courseCatalog?.files||[]).find(x=>x.encrypted_path);
  }
 }
 if(!first)throw Error("Les fichiers en ligne ne sont pas encore publiés. Réessayez après la synchronisation.");
 await fetchEncrypted(first,key,true);
 vaultKey=key;
 if(remember)saveKey(key);
 return key;
}
async function fetchEncrypted(item,usingKey,validateOnly=false){
 if(!item?.encrypted_path)throw Error("Ce document n'a pas encore de version en ligne. Demandez sa synchronisation.");
 const r=await fetch(item.encrypted_path,{cache:"force-cache"});
 if(!r.ok)throw Error("Fichier indisponible sur le site (HTTP "+r.status+").");
 const buf=new Uint8Array(await r.arrayBuffer());
 if(buf.length<35||String.fromCharCode(...buf.subarray(0,4))!=="RBL1")throw Error("Le document chiffré est invalide.");
 let plain;
 try{plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:buf.subarray(4,16)},usingKey,buf.subarray(16));}
 catch{throw Error("Le lien d'accès n'est pas valable pour cette archive.");}
 if(item.bytes&&plain.byteLength!==item.bytes)throw Error("Fichier incomplet : taille inattendue.");
 return validateOnly?true:new Blob([plain],{type:guessMime(item.name)});
}
function guessMime(n){
 const x=(n.split(".").pop()||"").toLowerCase();
 return ({pdf:"application/pdf",jpg:"image/jpeg",jpeg:"image/jpeg",png:"image/png",gif:"image/gif",webp:"image/webp",svg:"image/svg+xml",mp4:"video/mp4",webm:"video/webm",mov:"video/quicktime",mp3:"audio/mpeg",m4a:"audio/mp4",ogg:"audio/ogg",wav:"audio/wav",txt:"text/plain",html:"text/html",css:"text/css",csv:"text/csv",json:"application/json"})[x]||"application/octet-stream";
}
async function restore(){
 const hash=new URLSearchParams(location.hash.replace(/^#/,""));
 const access=hash.get("access");
 if(access){
  try{await activate(access,true);return;}
  catch(e){console.warn("Le lien privé ne permet pas l'accès.",e);}
 }
 vaultKey=await readKey();
}
keyPromise=restore();
window.courseVaultWait=()=>keyPromise;
window.courseVaultReady=()=>Boolean(vaultKey);
window.courseVaultFile=async item=>{
 await keyPromise;
 if(!vaultKey)throw Error("Accès privé non activé.");
 return fetchEncrypted(item,vaultKey);
};
window.courseVaultEncrypt=async file=>{
 await keyPromise;
 if(!vaultKey)throw Error("Ouvrez d'abord le site avec le lien d'accès privé pour chiffrer les nouvelles pièces jointes.");
 const iv=crypto.getRandomValues(new Uint8Array(12));
 const plain=await file.arrayBuffer();
 const cipher=new Uint8Array(await crypto.subtle.encrypt({name:"AES-GCM",iv},vaultKey,plain));
 const bytes=new Uint8Array(16+cipher.length);
 bytes.set([82,66,76,49],0);bytes.set(iv,4);bytes.set(cipher,16);
 let result="";
 for(let i=0;i<bytes.length;i+=16384)result+=String.fromCharCode(...bytes.subarray(i,i+16384));
 return btoa(result);
};
window.courseVaultPrompt=item=>{
 const root=$("viewerBody");if(!root)return;
 root.replaceChildren();
 const wrapper=document.createElement("div");wrapper.className="loadhelp";
 const icon=document.createElement("div");icon.className="big";icon.textContent="🔐";
 const title=document.createElement("h3");title.textContent="Ouvrir ce document";
 const desc=document.createElement("p");desc.textContent="La bibliothèque protège les documents du groupe. Ouvrez le lien d'accès privé une seule fois sur cet appareil : ensuite, tous les documents s'affichent d'un clic, sans ZIP ni dossier à choisir.";
 const form=document.createElement("form");form.style.cssText="display:grid;gap:10px;max-width:500px;margin:20px auto";
 const input=document.createElement("input");input.placeholder="Collez votre lien d'accès privé";input.autocomplete="off";input.required=true;input.style.cssText="background:#122839;color:white;border:1px solid #527185;border-radius:10px;padding:13px";
 const submit=document.createElement("button");submit.type="submit";submit.className="btn btn-primary";submit.textContent="🔓 Ouvrir les fichiers";
 const msg=document.createElement("p");msg.style.cssText="font-size:13px;color:#ffccbc;min-height:18px";
 form.append(input,submit,msg);
 form.addEventListener("submit",async e=>{
  e.preventDefault();submit.disabled=true;msg.textContent="Vérification du lien privé…";
  try{
   await activate(input.value,true);msg.textContent="";
   if(item&&$("viewerDialog").open)window.openViewer(item);
  }catch(error){msg.textContent=error.message||"Accès refusé.";}
  finally{submit.disabled=false;}
 });
 wrapper.append(icon,title,desc,form);
 root.append(wrapper);
};
})();