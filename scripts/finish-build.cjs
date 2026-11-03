'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const dist = path.join(root, 'dist');
const pkg = require('../node_modules/love.js/package.json');
if (pkg.version !== '11.4.1') throw new Error('Unexpected love.js version; review runtime patch before upgrading.');
const runtimePath = path.join(dist, 'love.js');
let runtime = fs.readFileSync(runtimePath, 'utf8').replace(/\r\n/g, '\n');
const startMarker = 'if(typeof ENVIRONMENT_IS_PTHREAD==="undefined"||!ENVIRONMENT_IS_PTHREAD){Module.addRunDependency("IDBFS_sync")';
const endMarker = '\n\n\n  return Love.ready';
const start = runtime.indexOf(startMarker);
const end = runtime.indexOf(endMarker, start);
if (start < 0 || end < 0 || runtime.indexOf(startMarker, start + 1) !== -1) {
  throw new Error('Pinned runtime IDBFS markers changed; refusing an unreviewed patch.');
}
runtime = runtime.slice(0, start) + fs.readFileSync(path.join(root, 'web/persistence.js'), 'utf8') + runtime.slice(end);
fs.writeFileSync(runtimePath, runtime);
for (const name of ['index.html', 'style.css', 'app.js']) fs.copyFileSync(path.join(root, 'web', name), path.join(dist, name));
fs.copyFileSync(path.join(root, 'LICENSE.txt'), path.join(dist, 'LICENSE.txt'));
fs.copyFileSync(path.join(root, 'node_modules/love.js/LICENSE'), path.join(dist, 'love.js-LICENSE.txt'));
// Upstream uses a random package cache UUID. Content addressing makes rebuilds stable.
const data = fs.readFileSync(path.join(dist, 'game.data'));
const hash = crypto.createHash('sha256').update(data).digest('hex');
const gamePath = path.join(dist, 'game.js');
let game = fs.readFileSync(gamePath, 'utf8');
if (!/"package_uuid":"[^"]+"/.test(game)) throw new Error('Missing preload cache UUID');
game = game.replace(/"package_uuid":"[^"]+"/, '"package_uuid":"' + hash + '"');
// Accessing indexedDB itself can throw in restricted browser contexts.
const cacheMarker = 'var indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB;';
if (!game.includes(cacheMarker)) throw new Error('Preload storage marker changed');
game = game.replace(cacheMarker, 'var indexedDB; try { indexedDB = window.indexedDB || window.mozIndexedDB || window.webkitIndexedDB || window.msIndexedDB; } catch (error) { console.warn("Preload cache unavailable", error); }');
fs.writeFileSync(gamePath, game);
fs.writeFileSync(path.join(dist, '.nojekyll'), '');
fs.writeFileSync(path.join(dist, 'build-info.json'), JSON.stringify({packager:pkg.version, mode:'compatibility', archiveSha256:hash}, null, 2)+'\n');
console.log('Static build finalized; runtime persistence patch applied.');
