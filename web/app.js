/* Generated game.js extends this global object before Love starts. */
var Module;
(function () {
  'use strict';
  const canvas = document.getElementById('canvas');
  const overlay = document.getElementById('overlay');
  const status = document.getElementById('status');
  const start = document.getElementById('start');
  let started = false, failed = false, waitingForStorage = false, timeout;
  window.failGame = function (message) {
    if (failed) return;
    failed = true;
    clearTimeout(timeout);
    overlay.hidden = false;
    status.textContent = message + ' Reload the page to try again.';
    start.disabled = false;
    start.textContent = 'Reload';
    start.onclick = () => location.reload();
  };
  window.engineReady = function () {
    if (failed) return;
    status.textContent = 'Ready. Click Play to start and enable audio.';
    start.disabled = false;
  };
  Module = {
    arguments: ['./game.love'], INITIAL_MEMORY: 134217728, canvas,
    locateFile: path => new URL(path, document.baseURI).href,
    print: (...args) => console.log(...args),
    printErr: (...args) => console.error(...args),
    onAbort: reason => failGame('The game stopped: ' + reason),
    onStorageWarning: function () {
      document.getElementById('storage').textContent = 'Storage is unavailable. You can play, but progress may not survive a reload.';
    },
    onStorageWaiting: function () {
      waitingForStorage = true;
      clearTimeout(timeout);
      status.textContent = 'The game is open in another tab. Close that tab to continue here with your latest save.';
    },
    onStorageAcquired: function () {
      if (waitingForStorage) {
        waitingForStorage = false;
        status.textContent = 'Loading your latest save…';
        timeout = setTimeout(() => failGame('Startup timed out.'), 60000);
      }
    },
    setStatus: text => { if (!failed && !waitingForStorage && text) status.textContent = text; },
    onRuntimeInitialized: function () {
      clearTimeout(timeout);
      if (!failed) { overlay.hidden = true; canvas.focus(); }
    }
  };
  start.onclick = function () {
    if (started || failed || typeof Love !== 'function') return;
    started = true;
    start.disabled = true;
    status.textContent = 'Starting…';
    timeout = setTimeout(() => failGame('Startup timed out.'), 60000);
    try {
      const ready = Love(Module);
      if (ready && typeof ready.catch === 'function') ready.catch(error => failGame(String(error)));
    } catch (error) { failGame(String(error)); }
  };
  canvas.addEventListener('pointerdown', () => canvas.focus());
  canvas.addEventListener('contextmenu', event => event.preventDefault());
  canvas.addEventListener('keydown', event => {
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', ' '].includes(event.key)) event.preventDefault();
  });
  canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); failGame('Graphics context lost.'); });
  document.getElementById('fullscreen').onclick = () => {
    const request = document.getElementById('stage').requestFullscreen;
    if (request) request.call(document.getElementById('stage')).catch(() => { status.textContent = 'Fullscreen is unavailable.'; });
  };
  window.addEventListener('error', event => failGame(event.message || 'A game asset failed to load.'));
  window.addEventListener('unhandledrejection', event => failGame(String(event.reason)));
})();
