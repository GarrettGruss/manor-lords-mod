-- Fake UE4SS API for mod tests. FakeGame (game.py) loads this file into a fresh Lua state.
-- It returns the table `fg`, which Python uses to control the fake game.
-- The code uses only Lua 5.4 features, because the game uses 5.4 (lupa embeds 5.5).
--
-- Objects, arrays and wrappers are Lua tables with metatables, not Python objects.
-- This way a mod sees the same kind of failure as in the game (an error), and the error carries
-- a Lua traceback. A nil key must fail: the real game can fail on it, so a test must catch it.

local fg = {
    now = 1000,            -- fake time in seconds; the test moves it
    start = 1000,
    counter = 0,
    loops = {}, queue = {}, hooks = {}, keybinds = {}, watchers = {},
    objects = {}, finders = {}, statics = {}, printed = {},
    in_game_thread = true, -- true while code that is allowed to touch game objects runs
    strict_threads = false,
    array_wrap = false,    -- true: TArray elements come as wrappers that need :get()
    fstring_mode = true,   -- true: text properties are FString-like (need :ToString())
}

---------------------------------------------------------------------------------------------
-- Thread model
---------------------------------------------------------------------------------------------

-- Run fn with the thread flag set. The flag is always restored, also after an error.
local function in_thread(is_game_thread, fn, ...)
    local before = fg.in_game_thread
    fg.in_game_thread = is_game_thread
    local ok, result = pcall(fn, ...)
    fg.in_game_thread = before
    if not ok then error(result, 0) end
    return result
end

local function check_thread(what)
    if fg.strict_threads and not fg.in_game_thread then
        error("game object used outside the game thread: " .. what, 3)
    end
end

---------------------------------------------------------------------------------------------
-- Wrappers: RemoteUnrealParam (:get()) and FString (:ToString())
---------------------------------------------------------------------------------------------

local param_store = setmetatable({}, { __mode = "k" })
local param_mt = {}
function param_mt.__index(self, key)
    if key == nil then error("indexed a RemoteUnrealParam with a nil key", 2) end
    local d = param_store[self]
    if key == "get" then return function() return d.value end end
    if key == "set" then return function(_, value) d.value = value end end
    error("RemoteUnrealParam has no member '" .. tostring(key) .. "'; call :get() first", 2)
end
function fg.param(value)
    local p = setmetatable({}, param_mt)
    param_store[p] = { value = value }
    return p
end

local fstring_store = setmetatable({}, { __mode = "k" })
local fstring_mt = {}
function fstring_mt.__index(self, key)
    if key == nil then error("indexed an FString with a nil key", 2) end
    if key == "ToString" then return function() return fstring_store[self] end end
    error("FString has no member '" .. tostring(key) .. "'; call :ToString() first", 2)
end
function fstring_mt.__tostring(self) return fstring_store[self] end
function fg.fstring(text)
    local s = setmetatable({}, fstring_mt)
    fstring_store[s] = tostring(text)
    return s
end
-- Text as the current mode wants it. Builders use this for every text property.
function fg.text(text)
    if fg.fstring_mode then return fg.fstring(text) end
    return text
end

---------------------------------------------------------------------------------------------
-- Objects
---------------------------------------------------------------------------------------------

local store = setmetatable({}, { __mode = "k" })
local class_objects = {}

local builtins = {
    IsValid = function(self) return store[self].valid end,
    GetFullName = function(self) local d = store[self]; return d.class .. " " .. d.path end,
    GetFName = function(self) return fg.fstring(store[self].name) end,
    GetClass = function(self) return fg.class_object(store[self].class) end,
}

local object_mt = {}
function object_mt.__index(self, key)
    if key == nil then error("indexed a game object with a nil key", 2) end
    local d = store[self]
    if d.methods[key] == nil and builtins[key] then return builtins[key] end
    check_thread("read '" .. tostring(key) .. "'")
    if not d.valid then
        error("read '" .. tostring(key) .. "' of an invalid " .. d.class .. " object", 2)
    end
    if d.methods[key] then return d.methods[key] end
    return d.props[key]
end
function object_mt.__newindex(self, key, value)
    if key == nil then error("assigned a game object property with a nil key", 2) end
    local d = store[self]
    check_thread("write '" .. tostring(key) .. "'")
    if not d.valid then
        error("write '" .. tostring(key) .. "' of an invalid " .. d.class .. " object", 2)
    end
    d.props[key] = value
end
function object_mt.__tostring(self) return store[self].class .. ":" .. store[self].name end

function fg.object(class, props, path)
    fg.counter = fg.counter + 1
    local name = class .. "_" .. fg.counter
    local self = setmetatable({}, object_mt)
    store[self] = {
        class = class, name = name, path = path or ("/Game/Fake/" .. name),
        props = props or {}, methods = {}, valid = true,
    }
    fg.objects[#fg.objects + 1] = self
    return self
end

function fg.class_object(class)
    if not class_objects[class] then
        class_objects[class] = fg.object("Class", { name = class }, "/Script/ManorLords." .. class)
    end
    return class_objects[class]
end

-- A method gets the object as its first argument, as in obj:Name(...).
function fg.set_method(object, name, fn)
    store[object].methods[name] = function(self, ...) return fn(self, ...) end
end
function fg.invalidate(object) store[object].valid = false end

---------------------------------------------------------------------------------------------
-- TArray
---------------------------------------------------------------------------------------------

local array_store = setmetatable({}, { __mode = "k" })
local array_mt = {}

local function array_count(d)
    local n = #d.items
    if d.visible then n = math.min(n, d.visible()) end
    return n
end

function array_mt.__index(self, key)
    if key == nil then error("indexed a TArray with a nil key", 2) end
    local d = array_store[self]
    if key == "GetArrayNum" then return function() return array_count(d) end end
    if key == "ForEach" then
        -- As in the game, the callback gets (index, wrapper). Returning true stops the loop.
        return function(_, callback)
            for i = 1, array_count(d) do
                if callback(i, fg.param(d.items[i])) then break end
            end
        end
    end
    if type(key) == "number" then
        local count = array_count(d)
        if key < 1 or key > count or key % 1 ~= 0 then
            error("TArray index " .. tostring(key) .. " is out of range (1.." .. count .. ")", 2)
        end
        if d.wrap then return fg.param(d.items[key]) end
        return d.items[key]
    end
    error("TArray has no member '" .. tostring(key) .. "'", 2)
end
function array_mt.__newindex(self, key, value)
    if key == nil then error("assigned a TArray element with a nil key", 2) end
    array_store[self].items[key] = value
end
function array_mt.__len(self) return array_count(array_store[self]) end

-- opts.wrap: nil means "use the game default". opts.visible: function that returns how many
-- items are visible now. This mimics a list that the game fills over time.
function fg.array(items, opts)
    opts = opts or {}
    local wrap = opts.wrap
    if wrap == nil then wrap = fg.array_wrap end
    local self = setmetatable({}, array_mt)
    array_store[self] = { items = items or {}, wrap = wrap, visible = opts.visible }
    return self
end
function fg.array_add(array, item)
    local items = array_store[array].items
    items[#items + 1] = item
end

---------------------------------------------------------------------------------------------
-- Time and print
---------------------------------------------------------------------------------------------

local real_time, real_date = os.time, os.date
os.time = function(t)
    if t ~= nil then return real_time(t) end
    return math.floor(fg.now)
end
os.clock = function() return fg.now - fg.start end
os.date = function(format, t) return real_date(format, t or math.floor(fg.now)) end

print = function(...)
    local parts = {}
    for i = 1, select("#", ...) do parts[i] = tostring((select(i, ...))) end
    fg.printed[#fg.printed + 1] = table.concat(parts, "\t")
end

---------------------------------------------------------------------------------------------
-- Finding objects
---------------------------------------------------------------------------------------------

function FindFirstOf(class)
    check_thread("FindFirstOf")
    local finder = fg.finders[class]
    if finder then return finder() end
    for _, object in ipairs(fg.objects) do
        local d = store[object]
        if d.class == class and d.valid then return object end
    end
    return nil
end

function FindAllOf(class)
    check_thread("FindAllOf")
    local found = {}
    local finder = fg.finders[class]
    if finder then
        local one = finder()
        if one ~= nil then found[1] = one end
    else
        for _, object in ipairs(fg.objects) do
            local d = store[object]
            if d.class == class and d.valid then found[#found + 1] = object end
        end
    end
    if #found == 0 then return nil end
    return found
end

function StaticFindObject(path)
    check_thread("StaticFindObject")
    if fg.statics[path] then return fg.statics[path] end
    for _, object in ipairs(fg.objects) do
        if store[object].path == path then return object end
    end
    return nil
end

---------------------------------------------------------------------------------------------
-- Threads, loops, hooks, key binds, new-object watchers
---------------------------------------------------------------------------------------------

function ExecuteInGameThread(fn) fg.queue[#fg.queue + 1] = fn end

local function add_loop(ms, fn, once)
    local seconds = math.max(ms / 1000, 0.001)
    local loop = { interval = seconds, due = fg.now + seconds, fn = fn, once = once, dead = false }
    fg.loops[#fg.loops + 1] = loop
    return loop
end
function LoopAsync(ms, fn) return add_loop(ms, fn, false) end
function ExecuteWithDelay(ms, fn) return add_loop(ms, fn, true) end
function ExecuteAsync(fn) return add_loop(0, fn, true) end

local function run_due_loops()
    for _, loop in ipairs({ table.unpack(fg.loops) }) do
        while not loop.dead and loop.due <= fg.now + 1e-9 do
            local stop = in_thread(false, loop.fn)
            if loop.once or stop == true then loop.dead = true end
            loop.due = loop.due + loop.interval
        end
    end
    local alive = {}
    for _, loop in ipairs(fg.loops) do
        if not loop.dead then alive[#alive + 1] = loop end
    end
    fg.loops = alive
end

local function drain_game_thread_queue()
    while #fg.queue > 0 do
        in_thread(true, table.remove(fg.queue, 1))
    end
end

-- One step of fake time: async loops run first, then the work they queued for the game thread.
function fg.step(seconds)
    fg.now = fg.now + seconds
    run_due_loops()
    drain_game_thread_queue()
end
function fg.live_loops() return #fg.loops end

local next_hook_id = 0
function RegisterHook(path, pre, post)
    next_hook_id = next_hook_id + 1
    fg.hooks[path] = fg.hooks[path] or {}
    table.insert(fg.hooks[path], { pre = pre, post = post })
    return next_hook_id, next_hook_id
end
-- Every hook argument is a wrapper, as in the game.
function fg.fire_hook(path, ...)
    local count = select("#", ...)
    local params = {}
    for i = 1, count do params[i] = fg.param((select(i, ...))) end
    for _, hook in ipairs(fg.hooks[path] or {}) do
        if hook.pre then in_thread(true, hook.pre, table.unpack(params, 1, count)) end
        if hook.post then in_thread(true, hook.post, table.unpack(params, 1, count)) end
    end
end

function NotifyOnNewObject(class, fn)
    fg.watchers[class] = fg.watchers[class] or {}
    table.insert(fg.watchers[class], fn)
end
function fg.spawn(object)
    for _, fn in ipairs(fg.watchers[store[object].class] or {}) do in_thread(true, fn, object) end
end

Key = setmetatable({}, { __index = function(_, name)
    -- A typo in a key name must fail here. In the game it is a nil key, which fails later.
    error("unknown Key." .. tostring(name), 2)
end })
ModifierKey = setmetatable({ SHIFT = 1, CONTROL = 2, ALT = 3 }, getmetatable(Key))
do
    local names = { "SPACE", "ENTER", "ESCAPE", "TAB", "BACKSPACE", "HOME", "END", "PAGE_UP", "PAGE_DOWN",
        "UP_ARROW", "DOWN_ARROW", "LEFT_ARROW", "RIGHT_ARROW", "LEFT_MOUSE_BUTTON", "RIGHT_MOUSE_BUTTON",
        "ZERO", "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE" }
    for i = 1, 12 do names[#names + 1] = "F" .. i end
    for code = string.byte("A"), string.byte("Z") do names[#names + 1] = string.char(code) end
    for i, name in ipairs(names) do rawset(Key, name, i) end
end

function RegisterKeyBind(key, a, b)
    if key == nil then error("RegisterKeyBind called with a nil key", 2) end
    local modifiers, fn = {}, a
    if type(a) ~= "function" then modifiers, fn = a, b end
    table.insert(fg.keybinds, { key = key, modifiers = modifiers, fn = fn })
end

local function same_modifiers(a, b)
    local set = {}
    for _, m in ipairs(a) do set[m] = true end
    for _, m in ipairs(b) do
        if not set[m] then return false end
        set[m] = nil
    end
    return next(set) == nil
end

-- Returns how many binds ran.
function fg.press(key, modifiers)
    local ran = 0
    for _, bind in ipairs({ table.unpack(fg.keybinds) }) do
        if bind.key == key and same_modifiers(bind.modifiers, modifiers or {}) then
            in_thread(true, bind.fn)
            ran = ran + 1
        end
    end
    return ran
end

return fg
