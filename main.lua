-- Fixtures replaced body-owned shapes in LÖVE 0.8; keep the original geometry.
function rectanglefixture(body, x, y, width, height)
    return love.physics.newFixture(body, love.physics.newRectangleShape(x, y, width, height), 1)
end

function rollingbody(world, x, y, radius)
    local body = love.physics.newBody(world, x, y, "dynamic")
    local fixture = love.physics.newFixture(body, love.physics.newCircleShape(radius), 1)
    body:setBullet(true)
    body:setMassData(0, 0, 0.1, 0.001)
    return body, fixture
end

function joystickaxis(index, axis)
    local joystick = love.joystick.getJoysticks()[index + 1]
    return joystick and joystick:getAxis(axis + 1) or 0
end

function love.load()
	
	require "normal"
	require "menu"
	require "highscoreentry"
	require "options"
	require "intro"
	
	------------
	--SETTINGS--
	------------
	soundenabled = true
	fullscreen = false
	joystickdeadzone = 0.5
	
	numhighscores = 9
	
	gravitymul = 260
	
	scale = 2
	zoom = 1
	
	controlmethods = {"mouse", "keyboard", "mouse direction", "joystick", "wheel steering", "wheel direct"}
	controldescriptions = {	mouse="move the mouse\n\nleft and right",
							keyboard="use arrow keys to\n\nrotate, shift to\n\nspeed up",
							['mouse direction']="point with your\n\nmouse towards a\n\ndirection",
							joystick="point with your\n\njoystick",
							['wheel steering']="drive like a car",
							['wheel direct']="1:1 wheel to\n\ngame translation"}
	controlmethod = love.system.getOS() == "Web" and "keyboard" or "mouse"
	
	pacfocus = false
	superpower = "normal" --clone, walls, normal
	powerupduration = 6
	superpelletblinkrate = 0.5
	wakkatimer = 0
	highscore = 0
	deathtime = 1.5
	deathdelay = 1
	mouse2rate = 0.05
	mouse2speed = 20 --50 for my macbook because who knows why, 20 else
	volume = 10
	
	pacmouthlimit = 0.25
	mouthduration = 0.22
	
	whitelist = "abcdefghijklmnopqrstuvwxyz 0123456789"
	
	scale = 2
	
	----END----
	
	loadhighscores()
	
	icon = love.image.newImageData("graphics/icon.png")
	changescale(scale)
	
	boardwidth = 220
	boardheight = 216
	
	--GRAPHICS--
	
	mainfield = love.graphics.newImage("graphics/field.png");mainfield:setFilter("nearest", "nearest") 
	mainfieldoverlay = love.graphics.newImage("graphics/fieldoverlay.png");mainfieldoverlay:setFilter("nearest", "nearest") 
	superpellet = love.graphics.newImage("graphics/superpellet.png");superpellet:setFilter("nearest", "nearest") 
	pacman = love.graphics.newImage("graphics/pacmanman.png")
	ghost1 = love.graphics.newImage("graphics/ghost1.png")
	ghost2 = love.graphics.newImage("graphics/ghost2.png")
	ghost3 = love.graphics.newImage("graphics/ghost3.png")
	ghostscared1 = love.graphics.newImage("graphics/ghostscared1.png")
	ghostscared2 = love.graphics.newImage("graphics/ghostscared2.png")
	ghosteyes = love.graphics.newImage("graphics/eyes.png")
	spinnyeyes = love.graphics.newImage("graphics/spinnyeyes.png")
	title = love.graphics.newImage("graphics/title.png");title:setFilter("nearest", "nearest") 
	gamescoreimg = love.graphics.newImage("graphics/gamescore.png");gamescoreimg:setFilter("nearest", "nearest") 
	highscoreimg = love.graphics.newImage("graphics/highscore.png");highscoreimg:setFilter("nearest", "nearest") 
	gameoverimg = love.graphics.newImage("graphics/gameover.png");gameoverimg:setFilter("nearest", "nearest") 
	clockimg = love.graphics.newImage("graphics/clock.png");clockimg:setFilter("nearest", "nearest") 
	optionsimg = love.graphics.newImage("graphics/options.png");optionsimg:setFilter("nearest", "nearest") 
	logo = love.graphics.newImage("graphics/logo.png")
	logoblood = love.graphics.newImage("graphics/logoblood.png")
	
	
	pacmanfont = love.graphics.newImageFont("graphics/font.png", "0123456789abcdefghijklmnopqrstuvwxyz.:/,'C-_> <")
	pacmanfont:setFilter("nearest", "nearest")
	love.graphics.setFont(pacmanfont)
	
	--SOUNDS--
	wakka1 = love.audio.newSource("sounds/pacman_waka_wa.ogg", "static")
	wakka2 = love.audio.newSource("sounds/pacman_waka_ka.ogg", "static")
	eatghost = love.audio.newSource("sounds/eat_ghost.ogg", "static"); eatghost:setVolume(0.5)
	ghostsiren = love.audio.newSource("sounds/ghosts_siren.ogg", "static"); ghostsiren:setVolume(0); ghostsiren:setLooping(true)
	ghostrunaway = love.audio.newSource("sounds/ghosts_runaway.ogg", "static"); ghostrunaway:setVolume(0); ghostrunaway:setLooping(true)
	beginning = love.audio.newSource("sounds/pacman_beginning.ogg", "static")
	gamewin = love.audio.newSource("sounds/win.ogg", "static")
	death = love.audio.newSource("sounds/pacman_death.ogg", "static")
	stabsound = love.audio.newSource("sounds/stab.ogg", "static")
	
	intro_load()
end

function love.update(dt)
	if skipupdate then
		skipupdate = false
		return
	end
	
	dt = math.min(dt, 1/30)
	if _G[gamestate .. "_update"] then
		_G[gamestate .. "_update"](dt)
	end
end

function love.draw()
	if _G[gamestate .. "_draw"] then
		_G[gamestate .. "_draw"]()
	end
end

function love.keypressed(key)
	if _G[gamestate .. "_keypressed"] then
		_G[gamestate .. "_keypressed"](key)
	end
end

function love.mousepressed(x, y, button)
	if _G[gamestate .. "_mousepressed"] then
		_G[gamestate .. "_mousepressed"](x, y, button)
	end
end

function love.joystickpressed(joystick, button)
	if _G[gamestate .. "_joystickpressed"] then
		_G[gamestate .. "_joystickpressed"](joystick, button)
	end
end

function string:split(delimiter) --Not by me
	local result = {}
	local from  = 1
	local delim_from, delim_to = string.find( self, delimiter, from  )
	while delim_from do
		table.insert( result, string.sub( self, from , delim_from-1 ) )
		from = delim_to + 1
		delim_from, delim_to = string.find( self, delimiter, from  )
	end
	table.insert( result, string.sub( self, from  ) )
	return result
end

function changescale(s)
	local grabbed = love.mouse.isGrabbed()
	scale = s
	
	windowwidth = 320*scale
	windowheight = 250*scale

	screenwidth = windowwidth
	screenheight = windowheight
	
	
	fsaa = 16
	vsync = true
	love.graphics.setLineWidth(5/3*scale)
	
	if gamestate == "options" then
		options_createdemoworld()
	end
	
	if love.graphics.getWidth() ~= windowwidth or love.graphics.getHeight() ~= windowheight then
		love.window.setMode(windowwidth, windowheight, {fullscreen=fullscreen, vsync=1, msaa=0})
	end
	
	love.window.setIcon(icon)
	
	love.mouse.setGrabbed(grabbed)
end

function print_r (t, indent) --Not by me
	local indent=indent or ''
	for key,value in pairs(t) do
		io.write(indent,'[',tostring(key),']') 
		if type(value)=="table" then io.write(':\n') print_r(value,indent..'\t')
		else io.write(' = ',tostring(value),'\n') end
	end
end

function loadhighscores()
    highscoreA = {}
    for i = 1, numhighscores do highscoreA[i] = {0, 0, "------"} end
    if not love.filesystem.getInfo("highscoreA", "file") then return end
    local ok, text = pcall(love.filesystem.read, "highscoreA")
    if not ok or type(text) ~= "string" or #text > 65536 then return end
    local method, size, rows = text:match("^([^#]+)#([^#]+)#(.*)$")
    if method then
        for _, candidate in ipairs(controlmethods) do
            if method == candidate then controlmethod = method; break end
        end
        size = tonumber(size)
        if size and size >= 1 and size <= 4 and size % 1 == 0 then scale = size end
    else
        rows = text -- Legacy scores did not have the settings prefix.
    end
    local i = 0
    for row in rows:gmatch("[^;]+") do
        i = i + 1
        if i > numhighscores then break end
        local pellets, elapsed, name = row:match("^([^:]+):([^:]+):([^:]*)$")
        pellets, elapsed = tonumber(pellets), tonumber(elapsed)
        if pellets and pellets >= 0 and pellets <= 244 and pellets % 1 == 0
            and elapsed and elapsed >= 0 and elapsed < math.huge
            and name and #name <= 6 and not name:find("[^a-z 0-9%-]") then
            highscoreA[i] = {pellets, elapsed, name}
        end
    end
end

function savehighscoresA()
    local rows = {}
    for i = 1, numhighscores do
        local row = highscoreA[i]
        rows[i] = row[1] .. ":" .. row[2] .. ":" .. row[3]
    end
    local text = controlmethod .. "#" .. scale .. "#" .. table.concat(rows, ";")
    local ok, result = pcall(love.filesystem.write, "highscoreA", text)
    if not ok or not result then print("Could not save highscores; continuing without storage.") end
end

-- Modern LÖVE supplies typed characters separately from key names.
function love.textinput(text)
    if gamestate == "highscoreentry" and high ~= 0 then
        for char in text:lower():gmatch(".") do
            if whitelist:find(char, 1, true) and #highscoreA[high][3] < 6 then
                highscoreA[high][3] = highscoreA[high][3] .. char
                cursorblink = true
                local sound = _G["wakka" .. (#highscoreA[high][3] % 2 + 1)]
                sound:stop(); sound:play()
            end
        end
    end
end

-- Mouse warping is unavailable in browsers. Consume real motion events instead.
function love.mousemoved(x, y, dx, dy)
    if controlmethod ~= "mouse" then return end
    if gamestate == "normal" then targetrotation = targetrotation + dx / 3
    elseif gamestate == "options" then demotargetrotation = demotargetrotation + dx / 3 end
end

function addzeros(s, i)
	for j = string.len(s)+1, i do
		s = "0" .. s
	end
	return s
end
