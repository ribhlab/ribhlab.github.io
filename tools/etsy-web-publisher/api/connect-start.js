import crypto from 'node:crypto';
import {admin,hasOrigin,json,readBody,noAuth,cookie} from '../lib/security.js';
const REDIRECT='https://ribhlab.github.io/ar/etsy-oauth-callback.html';
export default async function handler(req,res){
 if(req.method!=='POST')return json(res,405,{error:'Method not allowed'});
 if(!hasOrigin(req))return json(res,403,{error:'Invalid origin'});
 if(!admin(req))return noAuth(res);
 const b=await readBody(req).catch(()=>({}));
 const key=String(b.keystring||'').trim(), shared=String(b.sharedSecret||'').trim();
 if(!/^[a-zA-Z0-9_-]{12,128}$/.test(key)||!/^[a-zA-Z0-9_-]{8,200}$/.test(shared))return json(res,400,{error:'دخل Keystring وShared Secret بشكل صحيح.'});
 const verifier=crypto.randomBytes(48).toString('base64url');
 const challenge=crypto.createHash('sha256').update(verifier).digest('base64url');
 const state='rvp_'+crypto.randomBytes(24).toString('base64url');
 const url=new URL('https://www.etsy.com/oauth/connect');
 for(const [k,v] of Object.entries({response_type:'code',client_id:key,redirect_uri:REDIRECT,scope:'listings_r listings_w shops_r shops_w',state,code_challenge:challenge,code_challenge_method:'S256'}))url.searchParams.set(k,v);
 const oauth={key,shared,verifier,state,exp:Date.now()+12*60000};
 return json(res,200,{url:url.toString()},[cookie('oauth',oauth,720)]);
}
