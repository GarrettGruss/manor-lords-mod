# Runs mod/HarnessBoot against a fake game API (no game needed). Run from the repo root:
#   uv run --no-project --python 3.12 --with lupa python harness/tests/boot_state_machine.py [happy|noslot|missing]
# It checks the state machine and the output files. It does not prove the real game API behaves the same.
import os, sys, json, tempfile, pathlib
from lupa import LuaRuntime

out = tempfile.mkdtemp(prefix="boot-test-")
os.environ["HARNESS_RUN_DIR"] = out
os.environ["HARNESS_AUTOBOOT"] = "1"
os.environ["HARNESS_TEST_SAVE"] = "saveGame_0"
mode = sys.argv[1] if len(sys.argv) > 1 else "happy"

lua = LuaRuntime(unpack_returned_tuples=True)
lua.execute('package.path = "mod/shared/HarnessLog/?.lua;" .. package.path')
lua.execute(f"MODE = '{mode}'")
lua.execute(r'''
calls = {}
local tick = 0
local loadCalled, switched = false, false
local ticksSinceLoad = 0
local function valid() return true end

local entry = { SlotIndex = 2, Descriptor = { IsValid = valid, saveSlot = "saveGame_0", LevelName = "Jagged_Cliffs" } }
local slots = { GetArrayNum = function() return 1 end, entry }
if MODE == "noslot" then
    entry.Descriptor.saveSlot = "other"
end
local screen = { IsValid = valid, SortedSlotsByDate = slots }
local widget = { IsValid = valid,
    SwitchToLoadScreen = function(self, saveMode) switched = true; calls[#calls+1] = "SwitchToLoadScreen" end,
    LoadGame = function(self, e) loadCalled = true; calls[#calls+1] = "LoadGame:" .. tostring(e.SlotIndex) end }
local player = { IsValid = valid, bIsPlayerPaused = true }
local engine = { IsValid = valid, playerRef = player,
    regions = { GetArrayNum = function() return 1 end, { isSettled = true } },
    TemporalComponent = { IsValid = valid, day = 61, month = 3, Year = 1, Season = 1 } }
local io_handler = { IsValid = valid, DoesSaveGameExist = function(self, s) return MODE ~= "missing" end }

function StaticFindObject(path) return io_handler end
function FindFirstOf(name)
    if name == "mainMenu_widget_C" then
        if tick < 2 or loadCalled then return nil end
        return widget
    elseif name == "W_MainMenu_SaveLoadScreenV2_C" then
        if switched and not loadCalled then return screen end
        return nil
    elseif name == "RTSMultiEngineCPP" then
        if loadCalled and ticksSinceLoad >= 2 then return engine end
        return nil
    end
end
function ExecuteInGameThread(fn) fn() end
function LoopAsync(ms, fn) LOOP = fn end
function advance()
    tick = tick + 1
    if loadCalled then ticksSinceLoad = ticksSinceLoad + 1 end
    return LOOP()
end
''')
lua.execute(pathlib.Path("mod/HarnessBoot/Scripts/main.lua").read_text(encoding="utf-8"))
advance = lua.globals().advance
for i in range(40):
    if advance():
        break
print("mode:", mode, "| ticks:", i + 1)
print("calls:", list(lua.globals().calls.values()))
boot = json.loads(pathlib.Path(out, "boot.json").read_text())
print("state:", boot["state"], "| reason:", boot["reason"])
print("history:", [h["state"] for h in boot["history"]])
marker = pathlib.Path(out, "ready.marker")
print("ready.marker:", marker.read_text().strip() if marker.exists() else "none")
