# Runs mod/HarnessBoot against a fake game API (no game needed). Run from the repo root:
#   uv run --no-project --python 3.12 --with lupa python harness/tests/boot_state_machine.py [mode ...]
# With no mode, all modes run. It checks the state machine and the output files.
# It does not prove that the real game API behaves the same.
#
# Modes:
#   happy      the save loads, the clock stops after pauseGame, the end state is READY
#   slotlate   the slot list fills slowly; the wanted slot appears late; still READY
#   noslot     the wanted slot never appears; FAILED after the time limit
#   missing    DoesSaveGameExist is false; FAILED before the menu is touched
#   pausefails pauseGame has no effect; FAILED because the clock never stops
#   neverstarts the game never starts its clock; FAILED because the clock never started
#
# The fake game copies a real behavior: for a few seconds after the load the game holds the clock at 0.
# Then it starts the clock itself, and that undoes any pause made too early.
# After READY the test lets 10 more seconds pass and checks that the clock did not move.
import json
import os
import pathlib
import sys
import tempfile

from lupa import LuaRuntime

ALL_MODES = ["happy", "slotlate", "noslot", "missing", "pausefails", "neverstarts"]

# What each mode must end with: (state, text that the failure reason must contain)
EXPECTED = {
    "happy": ("READY", None),
    "slotlate": ("READY", None),
    "noslot": ("FAILED", "did not appear in the save list"),
    "missing": ("FAILED", "does not exist"),
    "pausefails": ("FAILED", "clock did not stop"),
    "neverstarts": ("FAILED", "clock never started"),
}

FAKE_GAME = r"""
-- Fake UE4SS API. Time is fake too: one call to advance() is one second.
calls = {}
local fakeNow = 1000
os.time = function() return fakeNow end

local tick = 0
local loadCalled, switched = false, false
local ticksSinceLoad = 0
local paused = false
local held = true -- the game holds the clock at 0 for a few seconds after the load
local GAME_START_TICK = 12 -- longer than the ready check, as in the real game (about 8 s)
local clock = 0.0

local function valid() return true end

local entry = { SlotIndex = 2, Descriptor = { IsValid = valid, saveSlot = "saveGame_0", LevelName = "Jagged_Cliffs" } }
local other = { SlotIndex = 5, Descriptor = { IsValid = valid, saveSlot = "saveGame_5", LevelName = "Divided" } }
if MODE == "noslot" then entry.Descriptor.saveSlot = "other" end

-- The list grows while the game scans the save folder. In "slotlate" the wanted slot comes last.
local slots = setmetatable({}, { __index = function(t, i)
    if MODE == "slotlate" and ticksSinceSwitch < 4 then
        if i == 1 then return other end
        return nil
    end
    if i == 1 then return other end
    if i == 2 then return entry end
    return nil
end })
ticksSinceSwitch = 0
slots.GetArrayNum = function()
    if MODE == "slotlate" and ticksSinceSwitch < 4 then return 1 end
    return 2
end
local screen = { IsValid = valid, SortedSlotsByDate = slots }

local widget = { IsValid = valid,
    SwitchToLoadScreen = function(self, saveMode) switched = true; calls[#calls + 1] = "SwitchToLoadScreen" end,
    LoadGame = function(self, e) loadCalled = true; calls[#calls + 1] = "LoadGame:" .. tostring(e.SlotIndex) end }

local player = { IsValid = valid, bIsPlayerPaused = true, -- this flag is stuck at true, like in the real game
    pauseGame = function(self)
        calls[#calls + 1] = "pauseGame"
        if MODE ~= "pausefails" then paused = true end
    end }

local engine = { IsValid = valid, playerRef = player,
    regions = { GetArrayNum = function() return 1 end, { isSettled = true } },
    TemporalComponent = { IsValid = valid, day = 61, month = 3, Year = 1, Season = 1 },
    getGameTimeAdjusted = function(self) return clock end }

local ioHandler = { IsValid = valid, DoesSaveGameExist = function(self, s) return MODE ~= "missing" end }

function StaticFindObject(path) return ioHandler end
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
    fakeNow = fakeNow + 1
    if switched then ticksSinceSwitch = ticksSinceSwitch + 1 end
    if loadCalled then ticksSinceLoad = ticksSinceLoad + 1 end
    if loadCalled and held and ticksSinceLoad >= GAME_START_TICK and MODE ~= "neverstarts" then
        held = false
        paused = false -- the game starts the clock itself and undoes an earlier pause
    end
    if loadCalled and not held and not paused then clock = clock + 1.0 end
    return LOOP()
end
function getclock() return clock end
"""


def run_mode(mode):
    out = tempfile.mkdtemp(prefix="boot-test-")
    os.environ["HARNESS_RUN_DIR"] = out
    os.environ["HARNESS_AUTOBOOT"] = "1"
    os.environ["HARNESS_TEST_SAVE"] = "saveGame_0"

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('package.path = "mod/shared/HarnessLog/?.lua;" .. package.path')
    lua.execute(f"MODE = '{mode}'")
    lua.execute(FAKE_GAME)
    lua.execute(pathlib.Path("mod/HarnessBoot/Scripts/main.lua").read_text(encoding="utf-8"))

    advance = lua.globals().advance
    ticks = 0
    for ticks in range(1, 400):
        if advance():
            break

    boot = json.loads(pathlib.Path(out, "boot.json").read_text())
    marker = pathlib.Path(out, "ready.marker")
    clock_at_ready = lua.globals().getclock()
    for _ in range(10):
        advance()
    clock_after = lua.globals().getclock()
    calls = list(lua.globals().calls.values())
    return boot, (marker.read_text().strip() if marker.exists() else None), calls, ticks, (clock_at_ready, clock_after)


def check(mode):
    boot, marker, calls, ticks, clocks = run_mode(mode)
    want_state, want_reason = EXPECTED[mode]
    problems = []
    if boot["state"] != want_state:
        problems.append(f"state is {boot['state']}, expected {want_state}")
    if want_reason and want_reason not in (boot["reason"] or ""):
        problems.append(f"reason {boot['reason']!r} does not contain {want_reason!r}")
    if want_state == "READY":
        if marker is None:
            problems.append("ready.marker is missing")
        elif json.loads(marker).get("paused") is not True:
            problems.append("ready.marker does not say paused")
        if "pauseGame" not in calls:
            problems.append("pauseGame was never called")
        if clocks[0] != clocks[1]:
            problems.append(f"the clock moved after READY ({clocks[0]} -> {clocks[1]}): the game was not really paused")
    elif marker is not None:
        problems.append("ready.marker exists after a failure")
    if mode == "missing" and calls:
        problems.append(f"menu was touched before the failure: {calls}")

    history = [h["state"] for h in boot["history"]]
    print(f"{'PASS' if not problems else 'FAIL'}  {mode:10} ticks={ticks:3} calls={calls} history={history}")
    for problem in problems:
        print("      -", problem)
    return not problems


if __name__ == "__main__":
    modes = sys.argv[1:] or ALL_MODES
    results = [check(mode) for mode in modes]
    sys.exit(0 if all(results) else 1)
