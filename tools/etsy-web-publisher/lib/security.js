import crypto from 'node:crypto';

const isProd = true;
const COOKIE_PREFIX = '__Host-';
const secret = () => {
  if (!process.env.RP_SECRET || !/^[a-f\d]{64}$/i.test(process.env.RP_SECRET)) throw new Error('Missing RP_SECRET');
  return Buffer.from(process.env.RP_SECRET, 'hex');
};
export const cookieName = (name) => COOKIE_PREFIX + 'rp_' + name;
export function readCookies(req) {
  const jar = {};
  for (const segment of String(req.headers.cookie || '').split(';')) {
    const idx = segment.indexOf('=');
    if (idx > 0) jar[segment.slice(0, idx).trim()] = segment.slice(idx + 1).trim();
  }
  return jar;
}
export function encrypt(value) {
  const nonce = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', secret(), nonce);
  const blob = Buffer.concat([cipher.update(JSON.stringify(value)), cipher.final()]);
  return Buffer.concat([nonce,cipher.getAuthTag(),blob]).toString('base64url');
}
export function decrypt(encoded) {
  try {
    const b=Buffer.from(encoded, 'base64url');
    if (b.length<30) return null;
    const decipher=crypto.createDecipheriv('aes-256-gcm', secret(), b.subarray(0,12));
    decipher.setAuthTag(b.subarray(12,28));
    return JSON.parse(Buffer.concat([decipher.update(b.subarray(28)), decipher.final()]).toString('utf8'));
  } catch {return null;}
}
export function getCookie(req, name) {return decrypt(readCookies(req)[cookieName(name)] || '');}
export function admin(req) {const data = getCookie(req,'admin');return data?.v===1 && Number(data.exp)>Date.now();}
export function session(req) {const data=getCookie(req,'etsy');return data?.exp>Date.now()?data:null;}
export function cookie(name, value, ageSeconds) {
  const base = `${cookieName(name)}=${value?encrypt(value):''}; Path=/; Secure; HttpOnly; SameSite=Lax`;
  return base + `; Max-Age=${value?ageSeconds:0}`;
}
export function hasOrigin(req) {
  const origin=req.headers.origin;
  const host=req.headers.host;
  return origin && new URL(origin).host === host && new URL(origin).protocol==='https:';
}
export function json(res, status, data, cookies=[]) {
  res.setHeader('Cache-Control', 'no-store, private');
  res.setHeader('X-Content-Type-Options','nosniff');
  res.setHeader('Referrer-Policy','no-referrer');
  if(cookies.length)res.setHeader('Set-Cookie',cookies);
  return res.status(status).json(data);
}
export function safeEq(a,b){const aa=crypto.createHash('sha256').update(String(a)).digest();const bb=crypto.createHash('sha256').update(String(b)).digest();return crypto.timingSafeEqual(aa,bb);}
export async function readBody(req, max=65536) {
  if(req.body && typeof req.body==='object' && !Buffer.isBuffer(req.body))return req.body;
  const raw=await readRaw(req,max);
  return JSON.parse(raw.toString('utf8'));
}
export async function readRaw(req, max) {
  if(Buffer.isBuffer(req.body)){if(req.body.length>max)throw Error('too_large');return req.body;}
  const chunks=[];let size=0;
  for await(const chunk of req){size+=chunk.length;if(size>max)throw Error('too_large');chunks.push(chunk);}
  return Buffer.concat(chunks);
}
export function hmac(value){return crypto.createHmac('sha256',secret()).update(value).digest('base64url');}
export function ticket(data){const raw=Buffer.from(JSON.stringify(data)).toString('base64url');return raw+'.'+hmac(raw);}
export function unticket(raw){
 if(typeof raw!=='string'||raw.length>2000)return null;
 const i=raw.lastIndexOf('.');if(i<0)return null;
 const p=raw.slice(0,i),sig=raw.slice(i+1);
 if(!safeEq(sig,hmac(p)))return null;
 try{const d=JSON.parse(Buffer.from(p,'base64url').toString('utf8'));return d.exp>Date.now()?d:null;}catch{return null;}
}
export function noAuth(res){return json(res,401,{error:'الولوج غير مسموح. سجل الدخول أولاً.'});}
export const SHELF='https://api.etsy.com/v3';
export async function fetchEtsy(path,options={}){
 let response;
 try{response=await fetch(SHELF+path,{...options,redirect:'error',signal:AbortSignal.timeout(60000)});}catch{throw Error('تعذر الاتصال بخادم Etsy.');}
 if(!response.ok)throw Error('Etsy رفضت العملية (HTTP '+response.status+').');
 try{return await response.json();}catch{throw Error('رد غير مفهوم من Etsy.');}
}
export function noSecrets(err){return err instanceof Error?String(err.message).slice(0,170):'خطأ غير متوقع';}
