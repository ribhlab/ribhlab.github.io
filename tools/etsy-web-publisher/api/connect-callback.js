import {admin,getCookie,fetchEtsy,cookie} from '../lib/security.js';
const REDIRECT='https://ribhlab.github.io/ar/etsy-oauth-callback.html';
const UI='/';
function go(res,path,cookies=[]){res.setHeader('Cache-Control','no-store');res.setHeader('Referrer-Policy','no-referrer');if(cookies.length)res.setHeader('Set-Cookie',cookies);return res.redirect(303,path);}
export default async function handler(req,res){
 if(req.method!=='GET')return res.status(405).end();
 if(!admin(req))return go(res,'/?error=login');
 const oauth=getCookie(req,'oauth');
 const state=String(req.query.state||''),code=String(req.query.code||'');
 if(!oauth||oauth.exp<Date.now()||!state||state!==oauth.state||code.length<4||code.length>2500)return go(res,'/?error=state',[cookie('oauth',null,0)]);
 const clear=[cookie('oauth',null,0)];
 try{
  const result=await fetchEtsy('/public/oauth/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'authorization_code',client_id:oauth.key,redirect_uri:REDIRECT,code,code_verifier:oauth.verifier})});
  if(!result.access_token||!result.refresh_token)throw Error('token');
  const uid=String(result.access_token).split('.')[0];if(!/^\d+$/.test(uid))throw Error('user');
  const shopResult=await fetchEtsy('/application/users/'+uid+'/shops',{headers:{'x-api-key':oauth.key+':'+oauth.shared,Authorization:'Bearer '+result.access_token}});
  const shop=shopResult.results?.[0]||shopResult;
  if(!/^\d+$/.test(String(shop.shop_id||'')))throw Error('shop');
  const etsy={key:oauth.key,shared:oauth.shared,refresh:result.refresh_token,shopId:String(shop.shop_id),exp:Date.now()+14*86400000};
  return go(res,'/?connected=1',[...clear,cookie('etsy',etsy,14*86400)]);
 }catch{return go(res,'/?error=etsy',[...clear]);}
}
