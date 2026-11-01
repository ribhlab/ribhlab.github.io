(()=> {
"use strict";
// Replace this ONLY with your own deployed Vercel project origin, never a public CORS proxy.
// Example after deployment: https://ribhlab-etsy-bridge.vercel.app
const BRIDGE_ORIGIN = "https://ribhlab-etsy-oauth-bridge.vercel.app";
const REDIRECT = "https://ribhlab.github.io/ar/etsy-oauth-callback.html";
const key = document.getElementById("etsy-client-id");
const submit = document.getElementById("start-oauth");
const status = document.getElementById("status");
if(!BRIDGE_ORIGIN || !/^https:\/\/[a-z0-9-]+\.vercel\.app$/i.test(BRIDGE_ORIGIN)) {
  submit.disabled = true;
  status.textContent = "خادم الربط الآمن باقي ما تنشرش. ما تعاودش الموافقة حتى نربطو الخادم مع الصفحة.";
  return;
}
status.textContent = "كنفحص الاتصال الآمن بـ Vercel…";
(async()=>{
  try {
    const response = await fetch(BRIDGE_ORIGIN + "/api/etsy-oauth-status", {
      method:"GET", mode:"cors", credentials:"omit", cache:"no-store"
    });
    if(!response.ok)throw new Error("health check failed");
    const data = await response.json();
    if(data.status!=="ready" || data.protocol!=="etsy-oauth-bridge-v1")throw new Error("wrong backend");
    submit.disabled = false;
    status.textContent = "✅ الاتصال آمن والخادم جاهز. لسق Keystring واضغط ربط حساب Etsy.";
  } catch {
    submit.disabled = true;
    status.textContent = "الخادم ما تجاوبش. ما تعاودش ترخيص Etsy دابا؛ عاود فتح الصفحة من Chrome.";
  }
})();
submit.addEventListener("click", async()=> {
  const clientId = key.value.trim();
  if(!/^[A-Za-z0-9_-]{12,128}$/.test(clientId)) {
    status.textContent = "لسق Keystring الصحيح من Etsy.";
    return;
  }
  submit.disabled = true;
  status.textContent = "كنوجد طلب الترخيص الآمن…";
  try {
    const enc = b=>btoa(String.fromCharCode(...new Uint8Array(b)))
      .replace(/\+/g,"-").replace(/\//g,"_").replace(/=+$/,"");
    const verifier = enc(crypto.getRandomValues(new Uint8Array(32)));
    const state = enc(crypto.getRandomValues(new Uint8Array(24)));
    const challenge = enc(await crypto.subtle.digest("SHA-256",new TextEncoder().encode(verifier)));
    sessionStorage.setItem("ribhlab_etsy_oauth",JSON.stringify({
      clientId,verifier,state,backend:BRIDGE_ORIGIN,at:Date.now()
    }));
    const url = new URL("https://www.etsy.com/oauth/connect");
    const vals = {
      response_type:"code",redirect_uri:REDIRECT,
      scope:"listings_r listings_w shops_r",client_id:clientId,
      state,code_challenge:challenge,code_challenge_method:"S256"
    };
    for(const [name,value] of Object.entries(vals))url.searchParams.set(name,value);
    location.assign(url.href);
  } catch {
    submit.disabled = false;
    status.textContent = "وقع خطأ فالبداية. جرّب نفس المتصفح Chrome.";
  }
});
})();