import crypto from 'node:crypto';
import {put,head} from '@vercel/blob';
import {admin,hasOrigin,noAuth,json,readBody,readRaw,ticket,unticket,noSecrets} from '../lib/security.js';
export const config={api:{bodyParser:false}};
const CHUNK=3*1024*1024;
const accepted={image:['jpg','jpeg','png','gif'],file:['pdf','zip','png','jpg','jpeg','svg','eps','txt','doc','docx','gif','psd','ai']};
const safeName=(raw)=>String(raw).normalize('NFKC').replace(/[^a-zA-Z0-9._-]/g,'-').slice(0,110);
export default async function handler(req,res){
 if(req.method!=='POST')return json(res,405,{error:'Method not allowed'});
 if(!hasOrigin(req))return json(res,403,{error:'Invalid origin'});
 if(!admin(req))return noAuth(res);
 const action=String(req.query.action||'');
 try{
  if(action==='start'){
   const b=await readBody(req);
   const job=String(b.job||''),type=String(b.kind||''),name=safeName(b.name),size=Number(b.size);
   const ext=name.split('.').at(-1).toLowerCase();
   if(!/^[a-f0-9-]{36}$/.test(job)||!accepted[type]?.includes(ext)||!Number.isInteger(size)||size<1||size>20*1024*1024)throw Error('ملف غير مدعوم أو كبير (20MB حد أقصى).');
   const fileId=crypto.randomBytes(12).toString('hex');
   const payload={job,kind:type,name,size,fileId,parts:Math.ceil(size/CHUNK),exp:Date.now()+2*3600000};
   return json(res,200,{ticket:ticket(payload),parts:payload.parts,chunkSize:CHUNK,filename:name});
  }
  const t=unticket(req.headers['x-upload-ticket']);
  if(!t||!accepted[t.kind]?.includes(t.name.split('.').at(-1).toLowerCase()))throw Error('انتهت صلاحية رفع الملف.');
  if(action==='part'){
   const idx=Number(req.query.index);
   if(!Number.isInteger(idx)||idx<0||idx>=t.parts)throw Error('Invalid index');
   const expected=Math.min(CHUNK,t.size-idx*CHUNK);
   const buffer=await readRaw(req,CHUNK+100);
   if(buffer.length!==expected)throw Error('حجم جزء الملف غير مطابق.');
   const pathname=`etsy-products/${t.job}/${t.fileId}/${idx}.bin`;
   const blob=await put(pathname,buffer,{access:'private',addRandomSuffix:false,contentType:'application/octet-stream'});
   return json(res,200,{path:blob.pathname,index:idx});
  }
  if(action==='finish'){
   const b=await readBody(req);
   const paths=b.paths;
   if(!Array.isArray(paths)||paths.length!==t.parts)throw Error('أجزاء الملف ناقصة.');
   for(let i=0;i<paths.length;i++){
    if(paths[i]!==`etsy-products/${t.job}/${t.fileId}/${i}.bin`)throw Error('مسار غير متوقع.');
    const blob=await head(paths[i]);
    if(Number(blob.size)!==Math.min(CHUNK,t.size-i*CHUNK))throw Error('حجم محفوظ غير صحيح.');
   }
   return json(res,200,{manifest:{ticket:req.headers['x-upload-ticket'],paths}});
  }
  return json(res,400,{error:'Invalid action'});
 }catch(err){return json(res,400,{error:noSecrets(err)});}
}
