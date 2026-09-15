import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
const source = await readFile(new URL('../app/api/v1/[...path]/route.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
const { POST, GET } = await import('data:text/javascript;base64,' + Buffer.from(compiled).toString('base64'));
function request(method='GET', headers={}) {const req=new Request('http://localhost:3000/api/v1/admin/orders?page=2',{method,headers,...(method==='POST'?{body:'{"status":"ACCEPTED"}'}:{})});req.nextUrl=new URL(req.url);return req;}

test('proxy rejects non-admin paths and traversal before fetching', async()=>{
  for(const path of [['orders'],['admin','..'],['admin','a/b'],['admin','a\\b']]) {
    assert.equal((await GET(request(),{params:Promise.resolve({path})})).status,404);
  }
});
test('proxy preserves secure session cookie and strips untrusted forwarding headers',async()=>{
  const original=global.fetch;let captured;
  global.fetch=async(url,options)=>{captured={url,options};return new Response('{"ok":true}',{headers:{'content-type':'application/json','set-cookie':'gg_admin=opaque; HttpOnly; SameSite=Strict'}});};
  try {
    const response=await POST(request('POST',{'cookie':'gg_admin=opaque','origin':'http://localhost:3000','content-type':'application/json','authorization':'Bearer must-not-forward','x-forwarded-for':'forged'}),{params:Promise.resolve({path:['admin','orders','1','status']})});
    assert.equal(response.status,200);
    assert.match(captured.url,/\/api\/v1\/admin\/orders\/1\/status\?page=2$/);
    assert.equal(captured.options.headers.get('cookie'),'gg_admin=opaque');
    assert.equal(captured.options.headers.get('origin'),'http://localhost:3000');
    assert.equal(captured.options.headers.get('authorization'),null);
    assert.equal(captured.options.headers.get('x-forwarded-for'),null);
    assert.equal(new TextDecoder().decode(captured.options.body),'{"status":"ACCEPTED"}');
    assert.match(response.headers.get('set-cookie'),/HttpOnly/);
    assert.equal(response.headers.get('cache-control'),'no-store');
  } finally {global.fetch=original;}
});
test('upstream outage returns a consistent understandable error',async()=>{
  const original=global.fetch;global.fetch=async()=>{throw new Error('connection refused');};
  try {const response=await GET(request(),{params:Promise.resolve({path:['admin','orders']})});assert.equal(response.status,502);assert.equal((await response.json()).error.code,'API_UNAVAILABLE');}finally{global.fetch=original;}
});
