import { chromium } from 'playwright';
import { PDFDocument } from 'pdf-lib';
import { readFile, mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';
const base=process.env.RIVO_WEB_URL||'https://ribhlab.github.io';
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({acceptDownloads:true,viewport:{width:393,height:852}});
const p=await context.newPage();
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const out='growth-qa-output';await mkdir(out,{recursive:true});
const fixture=async (name,w)=>{const d=await PDFDocument.create();d.addPage([w,400]);return {name,mimeType:'application/pdf',buffer:Buffer.from(await d.save())}};
const a=await fixture('A.pdf',300),b=await fixture('B.pdf',500);
async function go(mode){await p.goto(base+'/rivoscan/tools/'+mode+'/',{waitUntil:'load'});await p.locator('#run').waitFor()}
async function download(name){const pending=p.waitForEvent('download',{timeout:20000});await p.locator('#run').click();const d=await pending;await d.saveAs(out+'/'+name);return readFile(out+'/'+name)}
try{
 await go('merge-pdf');await p.locator('#files').setInputFiles([a,b]);await p.getByRole('button',{name:'Move up B.pdf'}).click();
 const merged=await download('merge.pdf');const pdf=await PDFDocument.load(merged);assert.deepEqual(pdf.getPages().map(x=>x.getWidth()),[500,300]);console.log('PASS merge and reorder');
 await go('split-pdf');await p.locator('#files').setInputFiles({name:'combined.pdf',mimeType:'application/pdf',buffer:merged});await p.locator('#pages').fill('2');
 const split=await PDFDocument.load(await download('split.pdf'));assert.equal(split.getPageCount(),1);assert.equal(split.getPage(0).getWidth(),300);console.log('PASS split actual page');
 await go('compress-pdf');await p.locator('#files').setInputFiles({name:'combined.pdf',mimeType:'application/pdf',buffer:merged});const opt=await download('optimized.pdf');assert.ok(opt.length<=merged.length);assert.equal((await PDFDocument.load(opt)).getPageCount(),2);console.log('PASS optimize original or smaller');
 const png=Buffer.from(await p.evaluate(()=>{const c=document.createElement('canvas');c.width=40;c.height=60;const x=c.getContext('2d');x.fillStyle='#123456';x.fillRect(0,0,40,60);return c.toDataURL('image/png').split(',')[1]}),'base64');
 await go('images-to-pdf');await p.locator('#files').setInputFiles({name:'fixture.png',mimeType:'image/png',buffer:png});const image=await PDFDocument.load(await download('images.pdf'));assert.equal(image.getPageCount(),1);console.log('PASS image to PDF');
 await go('qr-code');await p.locator('#text').fill('https://example.com/qa');const qr=await download('qr.png');assert.equal(qr.subarray(0,8).toString('hex'),'89504e470d0a1a0a');console.log('PASS actual QR PNG produced');
 assert.deepEqual(errors,[]);
 console.log('PASS 5 browser tools on deployed site; actual files inspected');
}finally{await browser.close()}
