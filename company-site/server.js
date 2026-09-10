import http from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';

const root=fileURLToPath(new URL('.',import.meta.url));
const port=Number(process.env.PORT||3000);
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.txt':'text/plain; charset=utf-8','.xml':'application/xml; charset=utf-8'};

const server=http.createServer(async(req,res)=>{
  try{
    const requested=new URL(req.url||'/',`http://${req.headers.host||'localhost'}`).pathname;
    const clean=normalize(decodeURIComponent(requested)).replace(/^(\.\.(\/|\\|$))+/, '');
    let relative=clean==='/'?'index.html':clean.replace(/^\/+/, '');
    let file=join(root,relative);
    if(!file.startsWith(root))throw new Error('Invalid path');
    let body;
    try{body=await readFile(file)}catch{
      if(extname(relative)){
        res.writeHead(404,{'content-type':'text/plain; charset=utf-8'});res.end('Not found');return;
      }
      file=join(root,'index.html');body=await readFile(file);
    }
    res.writeHead(200,{
      'content-type':types[extname(file)]||'application/octet-stream',
      'x-content-type-options':'nosniff',
      'referrer-policy':'strict-origin-when-cross-origin',
      'permissions-policy':'camera=(), microphone=(), geolocation=()',
      'content-security-policy':"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
      'cache-control':extname(file)==='.html'?'no-cache':'public, max-age=3600'
    });
    res.end(body);
  }catch{
    res.writeHead(500,{'content-type':'text/plain; charset=utf-8'});res.end('Server error');
  }
});

server.listen(port,'0.0.0.0',()=>console.log(`MNK Technologies site listening on ${port}`));
