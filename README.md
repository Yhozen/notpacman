# Not Pacman

**Play in your browser: https://notpacman.rccpr.tech**

Pacman with physics, by Maurice Guégan / [Stabyourself.net](https://stabyourself.net/notpacman/).
Cloned from the [official repository](https://github.com/Stabyourself/notpacman) at
`af20bd8`, then ported from LÖVE 0.7.2 to LÖVE 11.4 and the browser. Original game,
graphics, sound and WTFPL license are included. This is an unofficial browser port.
The [patched source download](https://notpacman.rccpr.tech/source.zip) includes the
port, tests, build scripts and Alchemy deployment configuration.

## Play

Click **Play** to load the game and enable audio, then press Enter at its menu.
Left and Right rotate the maze; hold Shift to turn faster. Escape returns to the
menu. Up and Down select Play or Options; Enter confirms. Options includes mouse,
controller, scale and volume settings. Mouse mode consumes motion events instead
of cursor warping; keyboard is the default in browsers. Use the page's Fullscreen
button for browser fullscreen. The game needs a desktop keyboard; touch controls
have not been added.

High scores, control method and scale are stored in this browser and site origin.
A second tab waits for the first to close before loading the latest saves. If
IndexedDB or Web Locks are unavailable, the game allows session-only play.
Periodic writes and page-hide flushing reduce save loss, but abrupt termination
can lose recent changes. Clearing site data removes saves.

## Build and test

Requires Node.js 22+, npm, Python 3 and Lua 5.4 (for save tests):

```sh
npm ci --ignore-scripts
npm test
npm run build
npm run serve
```

Open http://127.0.0.1:8080. The build creates a reproducible, allowlisted
`build/notpacman.love` and a static site in `dist/`. It uses pinned
`love.js@11.4.1` compatibility mode (the engine reports LÖVE 11.4.0), without
SharedArrayBuffer or cross-origin isolation requirements. Serve through HTTP(S)
and serve `.wasm` as `application/wasm`; asset URLs also support subdirectories.
The game source also targets native LÖVE 11.4+, though native play has not been
tested here. Box2D has changed since the original 0.7.2 release, so this port does
not claim identical physics to that engine.

The window, colors, fonts, physics fixtures, joystick access, wake-up calls and
high-score text entry use the modern APIs. Bodies keep the original maze geometry,
collision filters, mass and inertia. Missing saves are checked before reading,
and damaged records fall back to defaults. Game audio sources stop individually
to avoid a love.js bulk-stop failure. The launcher and coordinated IndexedDB
persistence are adapted from the Ortho Robot browser port; runtime patches fail
closed if the pinned generated code changes.

Run the browser integration check with Python Playwright and Chrome installed
while serving the repository (the test defaults to `http://127.0.0.1:8082/dist/`):

```sh
python3 -m http.server 8082 --bind 127.0.0.1
# In another terminal:
python3 scripts/browser-check.py
# Or against a deployment:
GAME_URL=https://notpacman.rccpr.tech/ python3 scripts/browser-check.py
```

`scripts/browser-gameplay-check.py` adds temporary console telemetry and a
collision fixture in browser requests, leaving `dist/` unchanged. It checks real
maze rotation, pellet collection, three death transitions, name entry and the
persisted high-score record.

Validated in Chromium 156 against the local build and the live deployment:
keyboard play, audio output, options and save reload, tab ownership transfer,
fullscreen, corrupt saves, unavailable storage and failed asset recovery. The
collision fixture also exercised game over and saved a named score. Firefox,
Safari, physical controllers and native LÖVE have not been exercised.

The GitHub workflow builds and uploads artifacts; it does not deploy.

## Deploy with Alchemy

`infra/alchemy.run.ts` manages the Cloudflare Worker and `notpacman.rccpr.tech`
custom domain. Deployment needs Node.js 24.11.1+ and Cloudflare credentials in
`CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`:

```sh
npm ci --ignore-scripts
npm test && npm run build
npm --prefix infra ci --ignore-scripts
CI=1 npm --prefix infra run deploy
```

The first deployment bootstraps the isolated remote state Worker
`alchemy-state-store-notpacman`. Subsequent `npm --prefix infra run plan` calls
preview changes. Do not commit credentials, local state, dependencies or built
artifacts. The source archive includes only game assets and an explicit allowlist
of source, documentation, tests and configuration files.
