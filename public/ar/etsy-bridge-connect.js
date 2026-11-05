(() => {
"use strict";
// Browser-only OAuth PKCE flow. No Etsy passwords, shared secrets, or tokens are logged/stored here.
const BRIDGE_ORIGIN = "https://ribhlab-etsy-oauth-helper.vercel.app";
const REDIRECT = "https://ribhlab.github.io/ar/etsy-oauth-callback.html";
const key = document.getElementById("etsy-client-id");
const submit = document.getElementById("start-oauth");
const status = document.getElementById("status");
const help = document.getElementById("key-hint");

if (!key || !submit || !status) return;

// The connect button is always available for a real user click.
// Network availability is checked *after* pressing it, not during initial page load.
submit.disabled = false;
submit.type = "button";
let busy = false;
let health = null;

const validKey = value => /^[A-Za-z0-9_-]{12,128}$/.test(value);
const explain = value => {
  const v = value.trim();
  if (!v) return "لسق Keystring ديال تطبيق Etsy؛ ماشي Shared Secret ولا App ID.";
  if (/\s/.test(v)) return "الكود فيه مسافات أو سطر جديد. انسخ Keystring بوحدو من Etsy Developer Apps.";
  if (!/^[A-Za-z0-9_-]+$/.test(v)) return "الـKeystring فيه رموز غير مقبولة. انسخ Keystring بوحدو بلا نقطتين ولا علامات إضافية.";
  if (v.length < 12 || v.length > 128) return "Keystring خاصو يكون بين 12 و128 حرف. تأكد ما نسختيش App ID أو Shared Secret.";
  return "";
};

status.textContent = "لسق Keystring، ومن بعد اضغط «ربط حساب Etsy». الزر خدام حتى إلا كان فحص الاتصال بطيء.";

key.addEventListener("input", () => {
  if (busy) return;
  const problem = explain(key.value);
  status.textContent = problem || "✅ صيغة Keystring مقبولة مبدئياً. اضغط «ربط حساب Etsy» باش نكملو.";
  if (help) help.hidden = !problem;
});

async function checkBridge() {
  if (!/^https:\/\/[a-z0-9-]+\.vercel\.app$/i.test(BRIDGE_ORIGIN)) throw new Error("invalid_backend");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(BRIDGE_ORIGIN + "/api/etsy-oauth-status", {
      method: "GET",
      mode: "cors",
      credentials: "omit",
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) throw new Error("http_" + response.status);
    const data = await response.json();
    if (data.status !== "ready" || data.protocol !== "etsy-oauth-bridge-v1") throw new Error("unexpected_backend");
    health = "ready";
  } finally {
    clearTimeout(timeout);
  }
}

submit.addEventListener("click", async () => {
  if (busy) return;
  const clientId = key.value.trim();
  const problem = explain(clientId);
  if (problem) {
    status.textContent = "⚠️ " + problem;
    key.focus();
    return;
  }
  busy = true;
  submit.disabled = true;
  status.textContent = "كنفحص الاتصال الآمن بالخادم…";
  try {
    await checkBridge();
  } catch {
    status.textContent = "⚠️ الاتصال بخادم الربط فشل. الكود ما تحكمناش عليه؛ تأكد من الإنترنت وعاود الضغط. ما تصيفط حتى رمز فالمحادثة.";
    busy = false;
    submit.disabled = false;
    return;
  }
  status.textContent = "✅ الاتصال خدام. كنوجد صفحة موافقة Etsy الرسمية…";
  try {
    const encode = bytes => btoa(String.fromCharCode(...bytes))
      .replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    const verifier = encode(crypto.getRandomValues(new Uint8Array(32)));
    const state = encode(crypto.getRandomValues(new Uint8Array(24)));
    const challenge = encode(new Uint8Array(
      await crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier))
    ));
    sessionStorage.setItem("ribhlab_etsy_oauth", JSON.stringify({
      clientId, verifier, state, backend: BRIDGE_ORIGIN, at: Date.now()
    }));
    const url = new URL("https://www.etsy.com/oauth/connect");
    for (const [name, value] of Object.entries({
      response_type: "code",
      client_id: clientId,
      redirect_uri: REDIRECT,
      scope: "listings_r listings_w shops_r shops_w",
      state,
      code_challenge: challenge,
      code_challenge_method: "S256"
    })) url.searchParams.set(name, value);
    window.location.assign(url.href);
  } catch {
    status.textContent = "تعذر بدء الربط في المتصفح. تأكد أن Chrome ما كايحظرش التخزين المؤقت وحاول من جديد.";
    busy = false;
    submit.disabled = false;
  }
});
})();