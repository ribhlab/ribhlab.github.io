import {get,put} from '@vercel/blob';
import {admin,session,hasOrigin,noAuth,json,readBody,unticket,fetchEtsy,cookie,noSecrets} from '../lib/security.js';
export const config={api:{bodyParser:false},maxDuration:300};
const MAX=20*1024*1024;
async function getPayload(req) {return readBody(req,128*1024);}
async function unpack(manifest,job,kind){
 if(!manifest||typeof manifest!=='object')throw Error('ملف ناقص.');
 const t=unticket(manifest.ticket);
 if(!t||t.job!==job||t.kind!==kind||t.parts!==manifest.paths?.length)throw Error('معلومات الملف غير صحيحة.');
 const buffers=[];let total=0;
 for(let i=0;i<t.parts;i++){
  const expected=`etsy-products/${job}/${t.fileId}/${i}.bin`;
  if(manifest.paths[i]!==expected)throw Error('معلومات الملف لا تطابق الرفع.');
  const response=await get(expected,{access:'private'});
  if(!response?.stream)throw Error('جزء الملف غير موجود.');
  const bytes=Buffer.from(await new Response(response.stream).arrayBuffer());
  total+=bytes.length;if(total>MAX)throw Error('حجم الملف كبير.');
  buffers.push(bytes);
 }
 if(total!==t.size)throw Error('حجم الملف غير مكتمل.');
 return {name:t.name,buffer:Buffer.concat(buffers)};
}
async function registryRead(job){
 const response=await get('etsy-products/'+job+'/registry.json',{access:'private'});
 if(!response?.stream)return {status:'new',imageDone:0,fileDone:0};
 const raw=await new Response(response.stream).text();return JSON.parse(raw);
}
async function registryWrite(job,reg){
 await put('etsy-products/'+job+'/registry.json',JSON.stringify(reg),{access:'private',contentType:'application/json',allowOverwrite:true,addRandomSuffix:false});
}
async function call(path,token,key,secret,method='GET',body=null){
 return fetchEtsy(path,{method,headers:{'x-api-key':key+':'+secret,'Authorization':'Bearer '+token,...(body instanceof URLSearchParams?{'Content-Type':'application/x-www-form-urlencoded'}:{})},body});
}
export default async function handler(req,res){
 if(req.method!=='POST')return json(res,405,{error:'Method not allowed'});
 if(!hasOrigin(req))return json(res,403,{error:'Invalid origin'});
 if(!admin(req))return noAuth(res);
 const creds=session(req);if(!creds)return json(res,403,{error:'ربط Etsy أولاً من خانة الاتصال.'});
 let job='';let registry=null;
 try{
  const b=await getPayload(req);job=String(b.job||'');
  const title=String(b.title||'').trim(),description=String(b.description||'').trim();
  const price=Number(b.price),taxonomy=Number(b.taxonomy||2078);
  const tags=String(b.tags||'').split(',').map(x=>x.trim()).filter(Boolean);
  const images=b.images,files=b.files;
  const live=b.live===true;
  if(!/^[a-f0-9-]{36}$/.test(job)||title.length<3||title.length>140||!description||description.length>12000||!Number.isFinite(price)||price<=0||price>100000||!Number.isInteger(taxonomy)||taxonomy<1)throw Error('العنوان أو الوصف أو الثمن أو التصنيف غير صحيح.');
  if(!Array.isArray(images)||images.length<1||images.length>20||!Array.isArray(files)||files.length<1||files.length>5)throw Error('خاص صورة واحدة على الأقل وملف رقمي واحد (حتى 5).');
  if(tags.length>13||tags.some(t=>t.length>20||!/^[\p{L}\p{N}\p{Zs}\-'™©®]+$/u.test(t)))throw Error('الكلمات المفتاحية: 13 على الأكثر، كل واحدة 20 حرفاً على الأكثر.');
  // Validate uploaded manifests before making ANY Etsy write.
  for(const [array,kind] of [[images,'image'],[files,'file']])for(const item of array){const t=unticket(item?.ticket);if(!t||t.job!==job||t.kind!==kind||!Array.isArray(item.paths)||item.paths.length!==t.parts)throw Error('الملفات لم تكتمل.');}
  registry=await registryRead(job);
  if(registry.title && registry.title!==title)throw Error('نفس العملية بدأت بمنتج آخر؛ افتح منتج جديد.');
  if(registry.status==='active')return json(res,200,{status:'active',listingId:registry.listingId,url:'https://www.etsy.com/listing/'+registry.listingId});
  const refreshed=await fetchEtsy('/public/oauth/token',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams({grant_type:'refresh_token',client_id:creds.key,refresh_token:creds.refresh})});
  if(!refreshed.access_token)throw Error('فشل تحديث اتصال Etsy.');
  const cookieUpdates=[];
  if(refreshed.refresh_token && refreshed.refresh_token!==creds.refresh){creds.refresh=refreshed.refresh_token;cookieUpdates.push(cookie('etsy',creds,14*86400));}
  const base='/application/shops/'+creds.shopId+'/listings';
  if(!registry.listingId){
   const form=new URLSearchParams({quantity:'999',title,description,price:price.toFixed(2),who_made:'i_did',when_made:'2020_2026',taxonomy_id:String(taxonomy),type:'download',is_supply:'false',should_auto_renew:'false'});
   if(tags.length)form.set('tags',tags.join(','));
   const draft=await call(base,refreshed.access_token,creds.key,creds.shared,'POST',form);
   if(!draft.listing_id)throw Error('Etsy لم ترجع رقم المسودة.');
   registry={title,listingId:draft.listing_id,status:'draft',imageDone:0,fileDone:0};
   await registryWrite(job,registry);
  }
  const url=base+'/'+registry.listingId;
  for(let i=registry.imageDone;i<images.length;i++){
   const asset=await unpack(images[i],job,'image');
   const form=new FormData();form.set('rank',String(i+1));form.set('image',new Blob([asset.buffer],{type:'image/jpeg'}),asset.name);
   await call(url+'/images',refreshed.access_token,creds.key,creds.shared,'POST',form);
   registry.imageDone=i+1;await registryWrite(job,registry);
  }
  for(let i=registry.fileDone;i<files.length;i++){
   const asset=await unpack(files[i],job,'file');
   const form=new FormData();form.set('name',asset.name);form.set('file',new Blob([asset.buffer],{type:'application/octet-stream'}),asset.name);
   await call(url+'/files',refreshed.access_token,creds.key,creds.shared,'POST',form);
   registry.fileDone=i+1;await registryWrite(job,registry);
  }
  if(!registry.typeSet){await call(url,refreshed.access_token,creds.key,creds.shared,'PATCH',new URLSearchParams({type:'download'}));registry.typeSet=true;await registryWrite(job,registry);}
  if(live && registry.status!=='active'){
   const result=await call(url,refreshed.access_token,creds.key,creds.shared,'PATCH',new URLSearchParams({state:'active'}));
   if(result.state && result.state!=='active')throw Error('Etsy لم تفعّل الإعلان؛ المسودة محفوظة.');
   registry.status='active';await registryWrite(job,registry);
  }
  if(cookieUpdates.length)res.setHeader('Set-Cookie',cookieUpdates);
  return json(res,200,{status:registry.status,listingId:registry.listingId,url:'https://www.etsy.com/listing/'+registry.listingId});
 }catch(err){
  return json(res,400,{error:noSecrets(err),listingId:registry?.listingId||null,note:registry?.listingId?'تم إنشاء مسودة قبل الخطأ، ويمكن إعادة المحاولة بنفس المنتج.':null});
 }
}
