import { admin, session, hasOrigin, cookie, json, readBody, safeEq, noAuth } from '../lib/security.js';
export default async function handler(req,res){
 if(req.method==='GET') return json(res,200,{authenticated:!!admin(req),connected:!!(admin(req)&&session(req)),shop_id:admin(req)?session(req)?.shopId:null});
 if(req.method!=='POST')return json(res,405,{error:'Method not allowed'});
 if(!hasOrigin(req))return json(res,403,{error:'Invalid origin'});
 const body=await readBody(req).catch(()=>({}));
 if(body.action==='logout')return json(res,200,{ok:true},[cookie('admin',null,0),cookie('etsy',null,0),cookie('oauth',null,0)]);
 if(body.action!=='login')return json(res,400,{error:'Invalid action'});
 if(!process.env.RP_PASSWORD || typeof body.password!=='string' || !safeEq(body.password,process.env.RP_PASSWORD))return json(res,403,{error:'الرمز السري غير صحيح'});
 return json(res,200,{ok:true},[cookie('admin',{v:1,exp:Date.now()+14*86400000},14*86400)]);
}
