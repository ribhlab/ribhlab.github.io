import test from "node:test";
import assert from "node:assert/strict";
import vm from "node:vm";
import fs from "node:fs";
import { webcrypto } from "node:crypto";

const source=fs.readFileSync("public/ar/etsy-bridge-connect.js","utf8");
const html=fs.readFileSync("public/ar/etsy-connect.html","utf8");

function browser(fetchImpl=async ()=>({ok:true,status:200,json:async()=>({status:"ready",protocol:"etsy-oauth-bridge-v1"})})) {
  const listeners={};
  let redirected=null, stored=null;
  const input={value:"",focus(){this.focused=true;},addEventListener(event,fn){listeners["input:"+event]=fn;}};
  const button={disabled:true,type:"",addEventListener(event,fn){listeners["button:"+event]=fn;}};
  const status={textContent:""};
  const help={hidden:false};
  const elements={"etsy-client-id":input,"start-oauth":button,"status":status,"key-hint":help};
  const context={
    document:{getElementById:id=>elements[id]||null},
    window:{location:{assign:url=>{redirected=url;}}},
    sessionStorage:{setItem:(k,v)=>{stored={key:k,value:v};}},
    crypto:webcrypto,
    TextEncoder, Uint8Array, URL, AbortController, setTimeout, clearTimeout, btoa,
    fetch:fetchImpl,
  };
  vm.runInNewContext(source,context,{filename:"etsy-bridge-connect.js",timeout:1000});
  return {input,button,status,help,
    type(v){input.value=v;listeners["input:input"]();},
    click(){return listeners["button:click"]();},
    get redirect(){return redirected;},
    get stored(){return stored;}
  };
}
test("button is enabled on page load even without prior server health response",()=>{
  const app=browser(async()=>{throw Error("offline")});
  assert.equal(app.button.disabled,false);
  assert.equal(app.button.type,"button");
  assert.ok(!html.includes('id="start-oauth" disabled'));
  assert.match(html,/etsy-bridge-connect\.js\?v=20261105-03/);
});
test("bad or empty key shows actionable message rather than gray button",async()=>{
  const app=browser();
  await app.click();
  assert.equal(app.button.disabled,false);
  assert.match(app.status.textContent,/Keystring/);
  app.type("invalid key / shared secret");
  await app.click();
  assert.equal(app.button.disabled,false);
  assert.equal(app.redirect,null);
});
test("valid key and verified bridge go to official Etsy PKCE consent with shops_w",async()=>{
  const app=browser();
  const key="AbCdEFgh01234567_-90ABCD";
  app.type(key);
  assert.match(app.status.textContent,/مقبولة/);
  await app.click();
  assert.ok(app.redirect);
  const u=new URL(app.redirect);
  assert.equal(u.origin,"https://www.etsy.com");
  assert.equal(u.pathname,"/oauth/connect");
  assert.equal(u.searchParams.get("client_id"),key);
  assert.ok(u.searchParams.get("scope").split(" ").includes("shops_w"));
  assert.equal(u.searchParams.get("code_challenge_method"),"S256");
  assert.equal(app.stored.key,"ribhlab_etsy_oauth");
});
test("if bridge is down the button re-enables and reports connection failure",async()=>{
  const app=browser(async()=>{throw Error("backend unreachable")});
  app.type("AbCdEFgh01234567_-90ABCD");
  await app.click();
  assert.equal(app.button.disabled,false);
  assert.match(app.status.textContent,/الاتصال/);
  assert.equal(app.redirect,null);
});
