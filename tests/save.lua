-- Save corruption must never prevent the game or score screen from loading.
love = {filesystem = {}}
dofile('main.lua')
local contents
love.filesystem.getInfo = function() return contents and {type="file"} end
love.filesystem.read = function() return contents end
love.filesystem.write = function(_, text) contents = text; return true end
controlmethods = {'mouse', 'keyboard', 'mouse direction', 'joystick', 'wheel steering', 'wheel direct'}
numhighscores = 9
local function load(text)
    contents = text; controlmethod = 'keyboard'; scale = 2; loadhighscores()
    assert(#highscoreA == 9)
    for _, row in ipairs(highscoreA) do
        assert(type(row[1]) == 'number' and type(row[2]) == 'number' and type(row[3]) == 'string')
    end
end
load(nil); assert(highscoreA[1][1] == 0)
-- Missing-file reads stall this pinned browser runtime even when wrapped in pcall.
local read = love.filesystem.read
love.filesystem.read = function() error('Missing files must not be read') end
load(nil)
love.filesystem.read = read
load('mouse#3#244:12.5:gab;12:40.3:abc'); assert(controlmethod == 'mouse' and scale == 3)
assert(highscoreA[1][1] == 244 and highscoreA[2][2] == 40.3)
savehighscoresA(); load(contents); assert(highscoreA[1][3] == 'gab')
load('20:18.4:legacy'); assert(highscoreA[1][1] == 20)
for _, text in ipairs({'garbage', 'mouse#0#oops', 'evil#nan#999:inf:bad;-1:0:bad;2:nan:bad', 'keyboard#4#2:3:TOOLONG', string.rep('x', 65537)}) do
    load(text); assert(highscoreA[1][1] == 0); assert(scale >= 1 and scale <= 4)
end
load(nil); love.filesystem.read = function() error('denied') end; loadhighscores()
love.filesystem.write = function() error('denied') end; savehighscoresA()
-- LÖVE 11 sends textinput separately; key names must not be read as Unicode.
whitelist = 'abcdefghijklmnopqrstuvwxyz 0123456789'
gamestate = 'highscoreentry'; high = 1; highscoreA[1][3] = ''
wakka1 = {stop=function() end, play=function() end}; wakka2 = wakka1
love.textinput('GaB!012345'); assert(highscoreA[1][3] == 'gab012')
print('Save and text-entry checks passed.')
