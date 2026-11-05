(async()=> {
"use strict";
const status=document.getElementById("status");
const copy=document.getElementById("copy");
const next=document.getElementById("next");
const params=new URLSearchParams(location.search);
const code=params.get("code");
const state=params.get("state");
const error=params.get("error");
// RibhLab Etsy Web Publisher: preserve Etsy's registered callback but
// hand the short-lived authorization code to the authenticated browser app.
if(state?.startsWith("rvp_")) {
  const callback=new URL("https://ribhlab-etsy-oauth-bridge.vercel.app/api/connect-callback");
  if(code)callback.searchParams.set("code",code);
  if(state)callback.searchParams.set("state",state);
  if(error)callback.searchParams.set("error",error);
  history.replaceState(null,"",location.pathname);
  location.replace(callback.toString());
  return;
}
history.replaceState(null,"",location.pathname);
if(error){status.textContent="Etsy رفضات الترخيص أو وقع خطأ. عاود من رابط البداية.";return;}
if(!code){status.textContent="صفحة الرجوع خدامة. خاصك تبدا من صفحة ربط Etsy أولاً.";return;}
let auth=null;
try{auth=JSON.parse(sessionStorage.getItem("ribhlab_etsy_oauth")||"null");}catch{}
sessionStorage.removeItem("ribhlab_etsy_oauth");
if(!auth || !state || state!==auth.state || !auth.clientId || !auth.verifier ||
   Date.now()-auth.at>15*60*1000) {
  status.textContent="جلسة الحماية سالات أو ما تطابقش state. فتح نفس Chrome اللي بديتي فيه الربط، وعاود الموافقة.";
  return;
}
if(!/^https:\/\/[a-z0-9-]+\.vercel\.app$/i.test(auth.backend||"")) {
  status.textContent="خادم الربط ما كانش مهيأ وقت الموافقة. ما تشاركش رابط code، عاود بعد تجهيز الخادم.";
  return;
}
status.textContent="Etsy وافقات؛ كنكمّلو التبادل عبر الخادم الآمن…";
try{
  const response=await fetch(auth.backend+"/api/etsy-oauth-token",{
    method:"POST",headers:{"Content-Type":"application/json"},
    body:JSON.stringify({client_id:auth.clientId,code,code_verifier:auth.verifier}),
    cache:"no-store",credentials:"omit",redirect:"error"
  });
  if(!response.ok)throw new Error("Token exchange rejected");
  const data=await response.json();
  if(typeof data.refresh_token!=="string"||!data.refresh_token)throw new Error("Missing refresh token");
  // Etsy may grant a subset of requested OAuth scopes. Verify the actual grant
  // before asking the seller to replace the working GitHub Actions credential.
  if(data.shops_write_granted!==true || !Array.isArray(data.granted_scopes) ||
      !data.granted_scopes.includes("shops_w")) {
    status.textContent="⚠️ Etsy ما عطاش الصلاحية shops_w لهاد الربط. ما تبدلش الرمز القديم فـGitHub. رجع لصفحة الربط ووافق على صلاحية تعديل المتجر، بلا مشاركة أي Token.";
    return;
  }
  let token=data.refresh_token;
  status.textContent="✅ Etsy منحات shops_w بالفعل. نسخ Refresh Token الجديد وخزنو مكان القديم داخل GitHub Secrets، ثم اضغط Update secret.";
  copy.hidden=false;
  next.hidden=false;
  copy.addEventListener("click",async()=>{
    try{
      await navigator.clipboard.writeText(token);
      status.textContent="تنسخ الرمز. دابا دخلو فـ Secret ETSY_REFRESH_TOKEN، وما تصيفطوش فالشات.";
    }catch{
      status.textContent="المتصفح منع النسخ. افتح Chrome مباشرة وحاول من جديد.";
    }
  },{once:false});
} catch{
  status.textContent="تعذر إكمال الربط عبر الخادم. ما تصيفط حتى رمز هنا. تأكد أن الخادم منشور وعاود من صفحة البداية.";
}
})();