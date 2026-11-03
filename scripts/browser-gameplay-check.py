"""Add telemetry and a collision fixture in memory to check the game-over/save path.
The deployed archive is never modified. Normal keys drive movement; F9 places a
ghost on Pacman to trigger the real collision detection and death transitions.
"""
import hashlib
import io
import json
import os
import re
import shutil
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get('GAME_URL', 'http://127.0.0.1:8082/dist/')
OUT = ROOT / 'evidence'
OUT.mkdir(exist_ok=True)
original = (ROOT / 'dist/game.data').read_bytes()
output = io.BytesIO()
telemetry = '''
local originalUpdate = love.update
local nextLog = 0
function love.update(dt)
 originalUpdate(dt)
 if love.timer.getTime() >= nextLog then
  nextLog = love.timer.getTime() + 0.25
  print("TEST_STATE", gamestate, eatored or -1, lives or -1, rotation or 0,
    gametime or 0, pacmanbody and pacmanbody:getX() or 0, pacmanbody and pacmanbody:getY() or 0)
 end
end
local originalKeypressed = love.keypressed
function love.keypressed(key)
 if key == "f9" and gamestate == "normal" then
  powerup = false
  ghosttimer[1] = 0
  ghostbody[1]:setPosition(pacmanbody:getPosition())
 else originalKeypressed(key) end
end
'''
with ZipFile(io.BytesIO(original)) as source, ZipFile(output, 'w', ZIP_DEFLATED) as patched:
    for name in source.namelist():
        data = source.read(name)
        if name == 'main.lua':
            data += telemetry.encode()
        patched.writestr(name, data)
data = output.getvalue()
loader = (ROOT / 'dist/game.js').read_text().replace(str(len(original)), str(len(data)))
loader = re.sub(r'"package_uuid":"[^"]+"', '"package_uuid":"'+hashlib.sha256(data).hexdigest()+'"', loader)
logs, states, errors = [], [], []
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=shutil.which('google-chrome') or shutil.which('chromium'),
                               args=['--no-sandbox','--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width':1060,'height':1150})
    def console(message):
        logs.append(message.text)
        if message.text.startswith('TEST_STATE'):
            states.append(message.text.split())
        if message.text.startswith('Error:') or 'exception thrown:' in message.text:
            errors.append(message.text)
    page.on('console', console)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.route('**/game.data', lambda route: route.fulfill(body=data, content_type='application/octet-stream'))
    page.route('**/game.js', lambda route: route.fulfill(body=loader, content_type='application/javascript'))
    page.goto(URL)
    page.locator('#start').click()
    page.wait_for_timeout(6500)
    for _ in range(5):
        page.keyboard.press('Enter')
        page.wait_for_timeout(450)
        if states and states[-1][1] == 'normal':
            break
    assert states[-1][1] == 'normal', states[-5:]
    page.keyboard.down('ArrowRight')
    page.wait_for_timeout(4000)
    page.keyboard.up('ArrowRight')
    for remaining in [2, 1, 0]:
        page.keyboard.press('F9')
        for _ in range(100):
            page.wait_for_timeout(100)
            assert not errors, errors
            if states and (states[-1][1] == 'highscoreentry' or int(states[-1][3]) == remaining):
                break
        print('Collision result:', states[-1], flush=True)
    gameplay = [s for s in states if s[1] == 'normal']
    assert gameplay and max(float(s[2]) for s in gameplay) > 0, states[-10:]
    assert len({s[6] for s in gameplay}) > 2, 'Pacman did not move'
    assert len({s[4] for s in gameplay}) > 2, 'Maze did not rotate'
    assert states[-1][1] == 'highscoreentry', states[-5:]
    page.screenshot(path=str(OUT/'game-over.png'))
    page.keyboard.type('gab')
    page.keyboard.press('Enter')
    page.wait_for_timeout(700)
    assert page.evaluate('Module.flushSaves()')
    saved = page.evaluate('''async () => {
     const db=await new Promise((resolve,reject)=>{const r=indexedDB.open('/home/web_user/love');r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
     return await new Promise((resolve,reject)=>{const tx=db.transaction('FILE_DATA','readonly'),r=tx.objectStore('FILE_DATA').getAll();r.onsuccess=()=>resolve(r.result.map(v=>v.contents?new TextDecoder().decode(v.contents):''));r.onerror=()=>reject(r.error);tx.oncomplete=()=>db.close();});
    }''')
    assert any(':gab' in text for text in saved), saved
    assert not errors, errors
    report = {'url':URL,'observedStates':states,'savedHighscores':saved,'errors':errors}
    (OUT/'gameplay-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'savedHighscores':saved,'errors':errors},indent=2))
    browser.close()
