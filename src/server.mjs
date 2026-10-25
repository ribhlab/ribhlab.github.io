import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../dist');
const mime={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'application/javascript; charset=utf-8','.xml':'application/xml; charset=utf-8','.json':'application/json; charset=utf-8','.svg':'image/svg+xml','.txt':'text/plain; charset=utf-8'};
const port=Number(process.env.PORT||4173);
http.createServer(async(req,res)=>{
  try {
    const url = new URL(req.url||'/',`http://localhost:${port}`);
    let pathname=decodeURIComponent(url.pathname); if(pathname==='/') pathname='/ar/';
    let file=path.resolve(root,'.'+pathname);
    if(!file.startsWith(root+path.sep)&&file!==root) throw Error('not found');
    if((await stat(file)).isDirectory())file=path.join(file,'index.html');
    const bytes=await readFile(file);res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(bytes);
  }catch(err){res.writeHead(404,{'Content-Type':'text/plain'});res.end('404 — Page not found');}
}).listen(port,()=>console.log(`RibhLab preview: http://localhost:${port}`));
