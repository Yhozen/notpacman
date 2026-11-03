"""Exercise the actual packaged game, storage and loading failures in Chromium."""
import json
import os
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get('GAME_URL', 'http://127.0.0.1:8082/dist/')
OUT = Path('evidence')
OUT.mkdir(exist_ok=True)
READ = '''async () => {
 const db = await new Promise((resolve,reject) => {
  const r=indexedDB.open('/home/web_user/love');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
 });
 return await new Promise((resolve,reject) => {
  const tx=db.transaction('FILE_DATA','readonly'), result={};
  const r=tx.objectStore('FILE_DATA').openCursor();
  r.onsuccess=()=>{const c=r.result;if(c){if(c.value.contents)result[c.key]=new TextDecoder().decode(c.value.contents);c.continue();}};
  tx.oncomplete=()=>{db.close();resolve(result);};tx.onerror=()=>reject(tx.error);
 });
}'''
WRITE = '''async text => {
 const db = await new Promise((resolve,reject) => {
  const r=indexedDB.open('/home/web_user/love');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
 });
 await new Promise((resolve,reject) => {
  const tx=db.transaction('FILE_DATA','readwrite'), store=tx.objectStore('FILE_DATA'), r=store.getAllKeys();
  r.onsuccess=()=>{const key=r.result.find(k=>k.endsWith('/highscoreA'));if(!key){reject(Error('No highscore file'));return;}
   store.put({timestamp:new Date(),mode:33206,contents:new TextEncoder().encode(text)},key);};
  tx.oncomplete=()=>{db.close();resolve();};tx.onerror=()=>reject(tx.error);
 });
}'''
AUDIO = '''window.analysers=[];const connect=AudioNode.prototype.connect;
AudioNode.prototype.connect=function(dest,...args){if(dest instanceof AudioDestinationNode){const a=this.context.createAnalyser();connect.call(this,a);analysers.push(a);}return connect.call(this,dest,...args);};
window.sampleAudio=()=>Math.max(0,...analysers.map(a=>{const d=new Float32Array(a.fftSize);a.getFloatTimeDomainData(d);return Math.max(...d.map(Math.abs));}));'''
errors = []
logs = []
report = {'url': URL}
with sync_playwright() as p:
    browser = p.chromium.launch(
        executable_path=os.environ.get('CHROMIUM') or shutil.which('google-chrome') or shutil.which('chromium'),
        headless=True, args=['--no-sandbox', '--enable-unsafe-swiftshader'])
    report['browser'] = browser.version
    context = browser.new_context(viewport={'width':1060,'height':1150})
    context.add_init_script(AUDIO)

    def page_for(ctx):
        page = ctx.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        def console(message):
            logs.append(message.type + ': ' + message.text)
            if message.text.startswith('Error:') or 'exception thrown:' in message.text:
                errors.append(message.text)
        page.on('console', console)
        return page

    def boot(page):
        page.goto(URL)
        page.locator('#start').click()
        page.wait_for_function('document.getElementById("overlay").hidden')

    def key(page, name, wait=120):
        page.keyboard.press(name)
        page.wait_for_timeout(wait)

    def shot(page, name):
        assert page.locator('#overlay').is_hidden(), page.locator('#status').inner_text()
        page.screenshot(path=str(OUT / (name+'.png')))

    owner = page_for(context)
    boot(owner)
    peaks = []
    for _ in range(24):
        peaks.append(owner.evaluate('sampleAudio()'))
        owner.wait_for_timeout(130)
    report['audioPeak'] = max(peaks)
    assert max(peaks) > 0, 'No rendered audio samples'
    owner.wait_for_timeout(3500)
    shot(owner, 'menu')
    key(owner, 'Enter', 800)
    shot(owner, 'game-start')
    owner.keyboard.down('ArrowRight')
    owner.wait_for_timeout(1100)
    owner.keyboard.up('ArrowRight')
    shot(owner, 'game-rotated')
    key(owner, 'Escape', 3300)
    key(owner, 'ArrowDown')
    key(owner, 'Enter', 500)
    shot(owner, 'options')
    # Browser starts with keyboard (row 2). Select mouse (row 1) and save.
    key(owner, 'ArrowUp')
    key(owner, 'Enter')
    key(owner, 'Escape', 300)
    assert owner.evaluate('Module.flushSaves()')
    saved = owner.evaluate(READ)
    assert any(v.startswith('mouse#2#') for v in saved.values()), saved
    report['savedControls'] = saved

    waiting = page_for(context)
    waiting.goto(URL)
    waiting.locator('#start').click()
    waiting.wait_for_function('document.getElementById("status").textContent.includes("another tab")')
    assert waiting.locator('#overlay').is_visible()
    assert waiting.evaluate('Module.flushSaves()') is False
    owner.close()
    waiting.bring_to_front()
    waiting.wait_for_function('document.getElementById("overlay").hidden')
    waiting.wait_for_timeout(6500)
    assert waiting.evaluate('Module.flushSaves()')
    assert waiting.evaluate(READ) == saved
    shot(waiting, 'save-handoff')
    report['tabHandoff'] = True
    # The saved mouse mode is selected on load. Switch back to keyboard.
    key(waiting, 'ArrowDown')
    key(waiting, 'Enter', 500)
    key(waiting, 'ArrowDown')
    key(waiting, 'Enter')
    key(waiting, 'Escape', 300)
    assert waiting.evaluate('Module.flushSaves()')
    assert any(v.startswith('keyboard#2#') for v in waiting.evaluate(READ).values())
    waiting.locator('#fullscreen').click()
    waiting.wait_for_timeout(200)
    assert waiting.evaluate('!!document.fullscreenElement')
    dims = waiting.locator('#canvas').bounding_box()
    assert abs(dims['width']/dims['height']-32/25) < .01
    key(waiting, 'Escape')
    report['fullscreen'] = True
    # Corrupted records must not crash menu, options or gameplay after reload.
    waiting.evaluate(WRITE, 'bad-control#0#999:inf:bad;2:nan:x;garbage')
    waiting.reload()
    waiting.locator('#start').click()
    waiting.wait_for_timeout(6500)
    key(waiting, 'Enter', 700)
    shot(waiting, 'corrupt-save-game')
    report['corruptSave'] = True
    context.close()

    for name, init in [
        ('denied-storage', "Object.defineProperty(window,'indexedDB',{get(){throw new DOMException('Blocked','SecurityError')}})"),
        ('missing-locks', "Object.defineProperty(navigator,'locks',{value:undefined})")]:
        ctx = browser.new_context(viewport={'width':1060,'height':1150})
        ctx.add_init_script(init)
        page = page_for(ctx)
        boot(page)
        assert 'unavailable' in page.locator('#storage').inner_text()
        assert page.evaluate('Module.flushSaves()') is False
        page.wait_for_timeout(6500)
        key(page, 'Enter', 1000)
        shot(page, name)
        ctx.close()
        report[name] = True

    # Expected failures use a separate page without the error collector.
    for asset in ['love.wasm', 'game.data', 'love.js']:
        ctx = browser.new_context()
        page = ctx.new_page()
        page.route('**/'+asset, lambda route: route.abort())
        page.goto(URL)
        if asset != 'love.js':
            page.locator('#start').click()
        page.wait_for_function('document.getElementById("start").textContent === "Reload"')
        assert page.locator('#overlay').is_visible()
        report[asset+'Failure'] = True
        ctx.close()
    browser.close()
assert not errors, errors
report['errors'] = errors
(OUT / 'browser-report.json').write_text(json.dumps(report, indent=2)+'\n')
(OUT / 'browser-console.log').write_text('\n'.join(logs)+'\n')
print(json.dumps(report, indent=2))
