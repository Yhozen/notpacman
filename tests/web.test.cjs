'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = name => fs.readFileSync(path.join(__dirname, '../web', name), 'utf8');
function launcher() {
  const elements = {};
  for (const name of ['canvas','overlay','status','start','storage','stage','fullscreen']) elements[name] = {addEventListener(){},focus(){},disabled:true};
  const events = {}, timers = new Map(); let calls=0, nextTimer=0;
  const ctx = {document:{getElementById:id=>elements[id],baseURI:'https://example.test/sub/'},console,URL,
    setTimeout(fn){timers.set(++nextTimer,fn);return nextTimer;},clearTimeout(id){timers.delete(id);},location:{reload(){}},Love(){calls++;return Promise.resolve();}};
  ctx.window = ctx; ctx.addEventListener = (name,fn) => {events[name]=fn;};
  vm.runInNewContext(source('app.js'),ctx);
  return {ctx,elements,events,timers,calls:()=>calls};
}
test('launch requires a gesture and runs once; assets remain relative', () => {
  const {ctx,elements,calls}=launcher();
  assert.equal(calls(),0); ctx.engineReady(); assert.equal(elements.start.disabled,false);
  elements.start.onclick(); elements.start.onclick(); assert.equal(calls(),1);
  assert.equal(ctx.Module.locateFile('love.wasm'),'https://example.test/sub/love.wasm');
});
test('async errors show recovery and storage failure is nonfatal', () => {
  const {ctx,elements,events}=launcher();
  ctx.Module.onStorageWarning(); assert.match(elements.storage.textContent,/unavailable/);
  events.error({message:'download failed'}); assert.match(elements.status.textContent,/download failed/);
  assert.equal(elements.start.textContent,'Reload'); assert.equal(elements.overlay.hidden,false);
});
function persistence(failHydration=false, locks={request:(_,options,callback)=>Promise.resolve(callback({}))}) {
  const callbacks=[];let released=0,hydrations=0,waiting=0;
  const ctx={Module:{addRunDependency(){},removeRunDependency(){released++;},onStorageWarning(){},onStorageWaiting(){waiting++;}},FS:{mkdirTree(){},mount(){},syncfs(populate,cb){if(populate){hydrations++;cb(failHydration?Error('denied'):null);}else callbacks.push(cb);}},IDBFS:{},navigator:{locks},setInterval(){},document:{addEventListener(){}},window:{addEventListener(){}},console:{warn(){}}};
  vm.runInNewContext(source('persistence.js'),ctx);
  return {ctx,callbacks,released:()=>released,hydrations:()=>hydrations,waiting:()=>waiting};
}
test('denied storage releases startup and allows session-only play',async()=>{
  const {ctx,released}=persistence(true); assert.equal(released(),1); assert.equal(await ctx.Module.flushSaves(),false);
});
test('flush requested during an active write is queued',async()=>{
  const {ctx,callbacks}=persistence();
  const first=ctx.Module.flushSaves(),second=ctx.Module.flushSaves();
  assert.equal(callbacks.length,1); callbacks.shift()(null); assert.equal(await first,true);
  assert.equal(callbacks.length,1); callbacks.shift()(null); assert.equal(await second,true);
});
test('a second tab waits for ownership before loading or writing saves',async()=>{
  let grant;
  const locks={request(name,options,callback){
    if(typeof options==='function'){grant=options;return new Promise(()=>{});}
    return Promise.resolve(callback(null));
  }};
  const {ctx,hydrations,released,waiting}=persistence(false,locks);
  assert.equal(waiting(),1);assert.equal(hydrations(),0);assert.equal(released(),0);
  assert.equal(await ctx.Module.flushSaves(),false);
  grant({});assert.equal(hydrations(),1);assert.equal(released(),1);
});
test('without Web Locks the game starts without writing shared storage',async()=>{
  const {ctx,hydrations,released}=persistence(false,null);
  assert.equal(hydrations(),0);assert.equal(released(),1);
  assert.equal(await ctx.Module.flushSaves(),false);
});
test('waiting for another tab preserves its message and cancels startup timeout',()=>{
  const {ctx,elements,timers}=launcher();
  elements.start.onclick();assert.equal(timers.size,1);
  ctx.Module.onStorageWaiting();ctx.Module.setStatus('Downloading...');
  assert.match(elements.status.textContent,/another tab/);assert.equal(timers.size,0);
  ctx.Module.onStorageAcquired();assert.equal(timers.size,1);
  ctx.Module.onRuntimeInitialized();assert.equal(timers.size,0);
});
test('a rejected storage lock allows session-only play',async()=>{
  const {ctx,released}=persistence(false,{request(){return Promise.reject(Error('denied'));}});
  await Promise.resolve();assert.equal(released(),1);
  assert.equal(await ctx.Module.flushSaves(),false);
});
