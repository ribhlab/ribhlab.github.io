import test from "node:test";
import assert from "node:assert/strict";
import handler, { validateExchange } from "../../../api/etsy-oauth-token.js";

const input = { client_id: "a".repeat(24), code: "a-valid-temporary-code", code_verifier: "b".repeat(43) };
function request(overrides = {}) {
  return { method: "POST", headers: { origin: "https://ribhlab.github.io", "content-length": "100" }, body: input, ...overrides };
}
function response() {
  const r = { statusCode: 200, headers: {}, payload: null, setHeader(k,v){this.headers[k]=v;return this;}, status(n){this.statusCode=n;return this;}, json(x){this.payload=x;return this;}, end(){return this;} };
  return r;
}
test("validates PKCE inputs",()=>{
  assert.equal(validateExchange(input),true);
  assert.equal(validateExchange({...input,code_verifier:"short"}),false);
  assert.equal(validateExchange({...input,code:"token with space"}),false);
});
test("rejects cross-site origins without permissive CORS", async()=>{
  const r=response(); await handler(request({headers:{origin:"https://untrusted.example"}}),r);
  assert.equal(r.statusCode,403);
  assert.equal(r.headers["Access-Control-Allow-Origin"],undefined);
});
test("preflight succeeds only for approved page",async()=>{
  const r=response(); await handler(request({method:"OPTIONS"}),r);
  assert.equal(r.statusCode,204);
  assert.equal(r.headers["Access-Control-Allow-Origin"],"https://ribhlab.github.io");
});
test("rejects malformed JSON without calling Etsy",async()=>{
  const r=response(); await handler(request({body:"{not-json"}),r);
  assert.equal(r.statusCode,400);
});
test("exchanges valid code without leaking into logs",async()=>{
  const original=globalThis.fetch;const originalEnv=process.env.ETSY_ALLOWED_KEYSTRING;
  delete process.env.ETSY_ALLOWED_KEYSTRING;
  try {
    globalThis.fetch=async(url,opts)=>{
      assert.equal(url,"https://api.etsy.com/v3/public/oauth/token");
      assert.equal(opts.method,"POST");
      assert.equal(opts.headers["Content-Type"],"application/x-www-form-urlencoded");
      const fields=new URLSearchParams(opts.body);
      assert.equal(fields.get("grant_type"),"authorization_code");
      assert.equal(fields.get("redirect_uri"),"https://ribhlab.github.io/ar/etsy-oauth-callback.html");
      assert.equal(fields.get("code_verifier"),input.code_verifier);
      return {ok:true,json:async()=>({access_token:"hidden-access",refresh_token:"test-refresh-token",scope:"listings_r listings_w shops_r shops_w"})};
    };
    const r=response();await handler(request(),r);
    assert.equal(r.statusCode,200);
    assert.deepEqual(r.payload,{refresh_token:"test-refresh-token",granted_scopes:["listings_r","listings_w","shops_r","shops_w"],shops_write_granted:true});
    assert.equal(r.headers["Cache-Control"],"no-store, private");
  } finally {globalThis.fetch=original;if(originalEnv!==undefined)process.env.ETSY_ALLOWED_KEYSTRING=originalEnv;}
});
test("Etsy denial does not echo API error body or secrets",async()=>{
  const orig=globalThis.fetch;try{
    globalThis.fetch=async()=>({ok:false,status:400,text:async()=>"{private details}"});
    const r=response();await handler(request(),r);
    assert.equal(r.statusCode,400);
    assert.deepEqual(r.payload,{error:"etsy_rejected_or_expired_authorization"});
  }finally{globalThis.fetch=orig;}
});

test("does not falsely claim shops_w was granted when Etsy left it out",async()=>{
  const orig=globalThis.fetch;
  try {
    globalThis.fetch=async()=>({ok:true,json:async()=>({
      access_token:"hidden-access",refresh_token:"older-scope-refresh",
      scope:"listings_r listings_w shops_r"
    })});
    const r=response();await handler(request(),r);
    assert.equal(r.statusCode,200);
    assert.equal(r.payload.shops_write_granted,false);
    assert.deepEqual(r.payload.granted_scopes,["listings_r","listings_w","shops_r"]);
  } finally {globalThis.fetch=orig;}
});
