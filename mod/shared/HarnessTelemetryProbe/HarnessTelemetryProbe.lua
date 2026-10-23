-- HarnessTelemetryProbe: spike code for change spike-playtest-telemetry (#384). NOT shipped. Harness only.
-- It answers engine questions about a player-safe log, crash detection, file access and a Lua zip.
-- Files go only under %LOCALAPPDATA%/ManorLords/Saved/ProbeTelemetry (in a run: the private appdata of the run).
-- It never calls a save function and never writes into SaveGames. It never reads a save from the real folder:
-- the scenario copies a fixture save into the private appdata first.
local M = {}

local LOCAL = (os.getenv("LOCALAPPDATA") or ""):gsub("\\", "/")
local BASE = LOCAL .. "/ManorLords/Saved/ProbeTelemetry"
local SAVED = LOCAL .. "/ManorLords/Saved"
M.base = BASE

local function winpath(p) return (p:gsub("/", "\\")) end

local function check_path(p)
    if type(p) ~= "string" or p:find("..", 1, true) or p:find("[^%w_%-%./: ~]") then error("unsafe path: " .. tostring(p), 2) end
    if p:lower():find("savegames", 1, true) then error("SaveGames paths are refused", 2) end
    return p
end

function M.mkdir(p)
    check_path(p)
    os.execute('mkdir "' .. winpath(p) .. '" >nul 2>&1')
end

local function exists(p)
    local f = io.open(p, "rb")
    if f then f:close() return true end
    return false
end

local function read_all(p)
    local f, err = io.open(p, "rb")
    if not f then return nil, err end
    local s = f:read("a")
    f:close()
    return s
end

-- Write a file atomically: .tmp then rename.
local function write_atomic(p, s)
    local tmp = p .. ".tmp"
    local f, err = io.open(tmp, "wb")
    if not f then return false, err end
    f:write(s)
    f:close()
    os.remove(p)
    local ok, rerr = os.rename(tmp, p)
    return ok and true or false, rerr
end

---------------------------------------------------------------------------------------------
-- 1.1 crash-safe log, 1.2 marker and heartbeat
---------------------------------------------------------------------------------------------
local S = { seq = 0, started = false }

function M.log_start()
    if S.started then return { ok = true, already = true } end
    M.mkdir(BASE)
    M.mkdir(BASE .. "/logs")
    local stamp = os.date("%Y%m%d-%H%M%S")
    S.log_path = BASE .. "/logs/session-" .. stamp .. ".log"
    S.ctl_path = BASE .. "/logs/control-noflush-" .. stamp .. ".log"
    S.marker = BASE .. "/session.marker"
    S.log = assert(io.open(S.log_path, "a"))
    S.ctl = assert(io.open(S.ctl_path, "a"))
    S.log:setvbuf("full") -- worst case for the buffer: we flush by hand after each line
    S.started = true
    S.beats = 0
    M.write_marker("running")
    LoopAsync(1000, function()
        S.beats = S.beats + 1
        M.line("tick", S.beats)
        if S.beats % 3 == 0 then M.write_marker("running") end
        return false
    end)
    return { ok = true, log = S.log_path, control = S.ctl_path, marker = S.marker }
end

function M.write_marker(state)
    local text = string.format('{"state":"%s","heartbeat":%d,"log":"%s"}', state, os.time(), S.log_path or "")
    return write_atomic(S.marker, text)
end

-- One numbered line to the flushed log and to the control log that is never flushed.
function M.line(kind, msg)
    S.seq = S.seq + 1
    local text = string.format("%d %d %s %s\n", os.time(), S.seq, kind, tostring(msg))
    S.log:write(text)
    S.log:flush()
    S.ctl:write(text)
    return S.seq
end

-- Many lines at once. Returns the cost per line (flush each) in microseconds.
function M.burst(n)
    local t0 = os.clock()
    for i = 1, n do M.line("burst", i) end
    local cost = (os.clock() - t0) / n * 1e6
    return { lines = n, last_seq = S.seq, us_per_line = cost }
end

function M.status() return { seq = S.seq, log = S.log_path, ctl = S.ctl_path } end

-- Delete the marker as a clean exit does.
function M.clean_exit()
    if S.marker then os.remove(S.marker) end
    return { ok = true }
end

-- Run at start: is a marker of an earlier session still there?
function M.detect_previous()
    local marker = BASE .. "/session.marker"
    local text = read_all(marker)
    if not text then return { crashed = false } end
    local hb = tonumber(text:match('"heartbeat":(%d+)'))
    local state = text:match('"state":"(%w+)"')
    local log = text:match('"log":"([^"]*)"')
    return { crashed = state == "running", state = state, heartbeat = hb, age_s = hb and (os.time() - hb) or nil, log = log, raw = text }
end

---------------------------------------------------------------------------------------------
-- 1.2 quit hooks
---------------------------------------------------------------------------------------------
local HOOK_CANDIDATES = {
    "/Script/Engine.GameInstance:ReceiveShutdown",
    "/Script/Engine.KismetSystemLibrary:QuitGame",
    "/Script/UMG.UserWidget:Destruct",
    "/Script/Engine.Actor:ReceiveEndPlay",
    "/Script/Engine.Actor:ReceiveDestroyed",
    "/Script/Engine.PlayerController:ClientReturnToMainMenuWithTextReason",
}

-- Lua closes the mod state when UE4SS ends ("Event loop end"). A table with __gc runs its finalizer then.
-- A kill or a crash never closes the state, so the finalizer is a clean-exit signal. It is made after the log files,
-- so it runs before their own finalizers (Lua finalizes in the reverse order of marking).
function M.gc_sentinel()
    S.sentinel = setmetatable({}, { __gc = function()
        pcall(function() M.line("gc", "sentinel finalizer ran") end)
        pcall(function() os.remove(S.marker) end)
    end })
    return { ok = true }
end
local MAX_HOOK_LINES = 400

function M.quit_hooks()
    local results = {}
    S.hook_counts = S.hook_counts or {}
    local hook_lines = 0
    for _, path in ipairs(HOOK_CANDIDATES) do
        local ok, err = pcall(function()
            RegisterHook(path, function(self)
                S.hook_counts[path] = (S.hook_counts[path] or 0) + 1
                if hook_lines < MAX_HOOK_LINES then
                    hook_lines = hook_lines + 1
                    local cls = ""
                    pcall(function() cls = self:get():GetFullName() end)
                    M.line("hook", path .. " n=" .. S.hook_counts[path] .. " " .. cls)
                end
            end)
        end)
        results[#results + 1] = { path = path, ok = ok, error = (not ok) and tostring(err) or nil }
    end
    return { hooks = results }
end

---------------------------------------------------------------------------------------------
-- 1.3 file access
---------------------------------------------------------------------------------------------
local function popen_lines(cmd)
    local p, err = io.popen(cmd)
    if not p then return nil, err end
    local out = {}
    for l in p:lines() do out[#out + 1] = (l:gsub("\r", "")) end
    p:close()
    return out
end

function M.newest_crash()
    local dir = SAVED .. "/Crashes"
    local names, err = popen_lines('dir /b /ad /o-d "' .. winpath(dir) .. '" 2>nul')
    if not names then return { ok = false, error = tostring(err) } end
    if #names == 0 then return { ok = true, folders = 0 } end
    local newest = names[1]
    local files = popen_lines('dir /b /a-d "' .. winpath(dir .. "/" .. newest) .. '" 2>nul') or {}
    local sizes = {}
    for _, name in ipairs(files) do
        local f = io.open(dir .. "/" .. newest .. "/" .. name, "rb")
        if f then sizes[#sizes + 1] = name .. "=" .. f:seek("end"); f:close() end
    end
    local head
    local f = io.open(dir .. "/" .. newest .. "/CrashContext.runtime-xml", "rb")
    if f then head = f:read(300); f:close() end
    return { ok = true, folders = #names, newest = newest, files = sizes, head = head }
end

local CRC = {}
for i = 0, 255 do
    local c = i
    for _ = 1, 8 do
        if c & 1 == 1 then c = 0xEDB88320 ~ (c >> 1) else c = c >> 1 end
    end
    CRC[i] = c
end

local function crc32_update(crc, s)
    local byte = string.byte
    for i = 1, #s, 4096 do
        local j = math.min(i + 4095, #s)
        local t = { byte(s, i, j) }
        for k = 1, #t do crc = CRC[(crc ~ t[k]) & 0xFF] ~ (crc >> 8) end
    end
    return crc
end
M.crc32_update = crc32_update

function M.read_test(rel)
    local path = check_path(BASE .. "/" .. rel)
    local t0 = os.clock()
    local f, err = io.open(path, "rb")
    if not f then return { ok = false, error = tostring(err) } end
    local size = f:seek("end")
    f:seek("set", 0)
    local magic = (f:read(4) or ""):gsub(".", function(c) return string.format("%02x", c:byte()) end)
    f:seek("set", 0)
    local crc, n = 0xFFFFFFFF, 0
    while true do
        local chunk = f:read(65536)
        if not chunk then break end
        n = n + #chunk
        crc = crc32_update(crc, chunk)
    end
    f:close()
    return { ok = true, size = size, read = n, crc32 = crc ~ 0xFFFFFFFF, magic = magic, ms = (os.clock() - t0) * 1000 }
end

function M.write_report_folder()
    local stamp = os.date("%Y%m%d-%H%M%S")
    local dir = BASE .. "/reports/report-" .. stamp
    M.mkdir(BASE .. "/reports")
    M.mkdir(dir)
    local files = {}
    local ok1 = write_atomic(dir .. "/report.json", '{"probe":true,"time":' .. os.time() .. "}")
    files[#files + 1] = "report.json"
    local log = S.log_path and read_all(S.log_path)
    if log then write_atomic(dir .. "/session.log", log); files[#files + 1] = "session.log" end
    local note = write_atomic(dir .. "/tester-text.txt", "Tester text, ASCII only\r\nline two\r\n")
    files[#files + 1] = "tester-text.txt"
    return { ok = ok1 and note, dir = dir, files = files, exists = exists(dir .. "/report.json") }
end

---------------------------------------------------------------------------------------------
-- 1.4 stored zip
---------------------------------------------------------------------------------------------
local function le16(n) return string.pack("<I2", n) end
local function le32(n) return string.pack("<I4", n) end

local function dos_time()
    local t = os.date("*t")
    local time = (t.hour << 11) | (t.min << 5) | (t.sec // 2)
    local date = ((math.max(t.year, 1980) - 1980) << 9) | (t.month << 5) | t.day
    return time, date
end

local Z = nil

local function zip_open(out, entries)
    local f = assert(io.open(out, "wb"))
    Z = { f = f, entries = entries, idx = 0, offset = 0, central = {}, done = false, out = out,
          bytes = 0, ticks = 0, max_tick_ms = 0, t0 = os.clock() }
end

-- Process up to `budget` bytes. Return true when finished.
local function zip_work(budget)
    local z = Z
    local tick0 = os.clock()
    while budget > 0 do
        if not z.cur then
            z.idx = z.idx + 1
            local e = z.entries[z.idx]
            if not e then
                local start = z.offset
                local size = 0
                for _, c in ipairs(z.central) do z.f:write(c); size = size + #c end
                z.f:write("PK\5\6" .. le16(0) .. le16(0) .. le16(#z.central) .. le16(#z.central) .. le32(size) .. le32(start) .. le16(0))
                z.f:close()
                z.done = true
                z.total_ms = (os.clock() - z.t0) * 1000
                break
            end
            local src = assert(io.open(e.path, "rb"))
            local size = src:seek("end")
            src:seek("set", 0)
            -- the CRC must be in the header, so the file is read once for the CRC and once to copy
            z.cur = { e = e, src = src, size = size, crc = 0xFFFFFFFF, phase = "crc" }
        end
        local c = z.cur
        local chunk = c.src:read(math.min(65536, math.max(1024, budget)))
        if c.phase == "crc" then
            if chunk then
                c.crc = crc32_update(c.crc, chunk)
                budget = budget - #chunk
            else
                c.crc = c.crc ~ 0xFFFFFFFF
                c.src:seek("set", 0)
                local time, date = dos_time()
                local name = c.e.name
                local header = "PK\3\4" .. le16(20) .. le16(0) .. le16(0) .. le16(time) .. le16(date) .. le32(c.crc) .. le32(c.size) .. le32(c.size) .. le16(#name) .. le16(0) .. name
                z.f:write(header)
                c.header_offset = z.offset
                z.offset = z.offset + #header
                c.phase = "copy"
            end
        else
            if chunk then
                z.f:write(chunk)
                z.offset = z.offset + #chunk
                z.bytes = z.bytes + #chunk
                budget = budget - #chunk
            else
                c.src:close()
                local name = c.e.name
                local time, date = dos_time()
                z.central[#z.central + 1] = "PK\1\2" .. le16(20) .. le16(20) .. le16(0) .. le16(0) .. le16(time) .. le16(date) .. le32(c.crc) .. le32(c.size) .. le32(c.size) .. le16(#name) .. le16(0) .. le16(0) .. le16(0) .. le16(0) .. le32(0) .. le32(c.header_offset) .. name
                z.cur = nil
            end
        end
    end
    local ms = (os.clock() - tick0) * 1000
    z.ticks = z.ticks + 1
    if ms > z.max_tick_ms then z.max_tick_ms = ms end
    return z.done
end

-- step_kb 0 = one go. Otherwise a loop does step_kb KB each 20 ms and the result is read with zip_status.
function M.zip_start(out_rel, entries, step_kb)
    check_path(out_rel)
    M.mkdir(BASE .. "/reports")
    local list = {}
    for _, e in ipairs(entries) do list[#list + 1] = { name = e.name, path = check_path(BASE .. "/" .. e.path) } end
    zip_open(BASE .. "/" .. out_rel, list)
    if step_kb <= 0 then
        zip_work(math.huge)
        return M.zip_status()
    end
    local budget = step_kb * 1024
    LoopAsync(20, function() return zip_work(budget) end)
    return { ok = true, started = true }
end

function M.zip_status()
    if not Z then return { ok = false, error = "no zip" } end
    return { ok = true, done = Z.done, out = Z.out, ticks = Z.ticks, max_tick_ms = Z.max_tick_ms, total_ms = Z.total_ms, bytes = Z.bytes }
end


---------------------------------------------------------------------------------------------
-- 1.5 report menu: a text box and a check box in a widget that is built at run time (no pak widget)
---------------------------------------------------------------------------------------------
local W = { steps = {} }

local function valid(object)
    if object == nil then return false end
    local ok, v = pcall(function() return object:IsValid() end)
    return ok and v == true
end

local function step(name, fn)
    local ok, value = pcall(fn)
    W.steps[#W.steps + 1] = name .. ": " .. (ok and "ok" or tostring(value):sub(1, 160))
    if ok then return value end
    return nil
end

local function make(class_path, owner, name)
    return step("construct " .. name, function()
        return StaticConstructObject(StaticFindObject(class_path), owner, FName(name))
    end)
end

function M.menu_close()
    if valid(W.widget) then pcall(function() W.widget:RemoveFromParent() end) end
    W.widget = nil
    return { ok = true }
end

function M.menu_open(checked)
    M.menu_close()
    W.steps = {}
    local controller = FindFirstOf("PlayerController")
    local userClass = StaticFindObject("/Script/UMG.UserWidget")
    local library = StaticFindObject("/Script/UMG.Default__WidgetBlueprintLibrary")
    local widget = step("Create UserWidget", function() return library:Create(controller, userClass, controller) end)
    if not valid(widget) then return { ok = false, steps = W.steps } end
    local tree = make("/Script/UMG.WidgetTree", widget, "PTree")
    step("set WidgetTree", function() widget.WidgetTree = tree end)
    local border = make("/Script/UMG.Border", tree, "PBorder")
    step("tree.RootWidget", function() tree.RootWidget = border end)
    step("Border color", function() border:SetBrushColor({ R = 0.05, G = 0.05, B = 0.08, A = 0.92 }) end)
    step("Border padding", function() border:SetPadding({ Left = 16, Top = 16, Right = 16, Bottom = 16 }) end)
    local vbox = make("/Script/UMG.VerticalBox", tree, "PVBox")
    step("Border:SetContent", function() border:SetContent(vbox) end)
    local title = make("/Script/UMG.TextBlock", tree, "PTitle")
    step("title text", function() title:SetText(FText("Report a bug")) end)
    step("add title", function() vbox:AddChildToVerticalBox(title) end)
    local size = make("/Script/UMG.SizeBox", tree, "PSize")
    step("SizeBox width", function() size:SetWidthOverride(640) end)
    step("SizeBox height", function() size:SetHeightOverride(180) end)
    local edit = make("/Script/UMG.MultiLineEditableTextBox", tree, "PEdit")
    step("hint text", function() edit:SetHintText(FText("Describe what went wrong")) end)
    step("SizeBox:SetContent", function() size:SetContent(edit) end)
    step("add edit", function() vbox:AddChildToVerticalBox(size) end)
    local row = make("/Script/UMG.HorizontalBox", tree, "PRow")
    local check = make("/Script/UMG.CheckBox", tree, "PCheck")
    step("check state", function() check:SetIsChecked(checked and true or false) end)
    step("add check", function() row:AddChildToHorizontalBox(check) end)
    local label = make("/Script/UMG.TextBlock", tree, "PLabel")
    step("label text", function() label:SetText(FText("Include my save game")) end)
    step("add label", function() row:AddChildToHorizontalBox(label) end)
    step("add row", function() vbox:AddChildToVerticalBox(row) end)
    local button = make("/Script/UMG.Button", tree, "PButton")
    local btext = make("/Script/UMG.TextBlock", tree, "PButtonText")
    step("button text", function() btext:SetText(FText("Create report")) end)
    step("button content", function() button:SetContent(btext) end)
    step("add button", function() vbox:AddChildToVerticalBox(button) end)
    W.widget, W.edit, W.check = widget, edit, check
    step("AddToViewport", function() widget:AddToViewport(100) end)
    step("position", function() widget:SetPositionInViewport({ X = 300, Y = 200 }, false) end)
    local inview = step("IsInViewport", function() return widget:IsInViewport() end)
    return { ok = true, in_viewport = inview, steps = W.steps }
end

function M.menu_set_text(text)
    W.steps = {}
    step("SetText", function() W.edit:SetText(FText(text)) end)
    return { steps = W.steps }
end

function M.menu_set_checked(on)
    W.steps = {}
    step("SetIsChecked", function() W.check:SetIsChecked(on and true or false) end)
    return { steps = W.steps }
end

function M.menu_focus()
    W.steps = {}
    step("SetKeyboardFocus", function() W.edit:SetKeyboardFocus() end)
    local focus = step("HasKeyboardFocus", function() return W.edit:HasKeyboardFocus() end)
    return { steps = W.steps, has_focus = focus }
end

function M.menu_state()
    local text = step("GetText", function() return W.edit:GetText():ToString() end)
    local checked = step("IsChecked", function() return W.check:IsChecked() end)
    return { text = text, checked = checked, steps = W.steps }
end

return M
