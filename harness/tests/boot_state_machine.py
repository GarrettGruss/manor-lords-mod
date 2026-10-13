# Runs mod/HarnessBoot against a fake game API (no game needed). Run from the repo root:
#   uv run python harness/tests/boot_state_machine.py [mode ...]
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
#   autosavefails SetAutosavePeriodOnPawn answers true but the timer stays; FAILED before the game is paused
#   cinematic  the intro cinematic ends after the clock started; pauseGame must be called once, after the cinematic
#   nocinematic there is no intro; pauseGame is called once, at once
#   silentrestart the game restarts the clock with no sign (old behavior); the hold calls pauseGame twice; READY
#   cinematicstuck the cinematic never ends; pauseGame is called after the wait limit; READY
#   newgame    LoadGame starts a new game (savefileToLoad empty, the bug before 2026-10-11); FAILED, not READY
#   freshstart     fresh start mode: the map opens with no slot; READY, no load screen touched
#   freshnoopen    fresh start mode: the map never opens; FAILED, the game was not ready
#   freshloadsslot fresh start mode: a slot name stays in savefileToLoad; FAILED
#   freshbadmap    fresh start mode: a map name with a space is refused; FAILED before the console
#
# The fake game is the kit in harness/tests/fakegame. It copies a real behavior: for a few seconds after the load the game holds the clock at 0.
# Then it starts the clock itself, and that undoes any pause made too early.
# Later the game undoes the pause once more (as seen in the real game, 2 to 4 s after the pause).
# After READY the test lets 10 more seconds pass and checks that the clock did not move.
import json
import sys

import fakegame_path  # noqa: F401  (makes the fakegame package importable)
from fakegame import FakeGame, FakeGameClock, build_manor_lords_state

ALL_MODES = ["happy", "slotlate", "noslot", "missing", "pausefails", "neverstarts", "autosavefails",
             "cinematic", "nocinematic", "silentrestart", "cinematicstuck", "newgame",
             "freshstart", "freshnoopen", "freshloadsslot", "freshbadmap"]

# What each mode must end with: (state, text that the failure reason must contain)
EXPECTED = {
    "happy": ("READY", None),
    "slotlate": ("READY", None),
    "noslot": ("FAILED", "did not appear in the save list"),
    "missing": ("FAILED", "does not exist"),
    "pausefails": ("FAILED", "clock did not stop"),
    "neverstarts": ("FAILED", "clock never started"),
    "autosavefails": ("FAILED", "autosave timer was not pushed away"),
    "cinematic": ("READY", None),
    "nocinematic": ("READY", None),
    "silentrestart": ("READY", None),
    "cinematicstuck": ("READY", None),
    "newgame": ("FAILED", "did not load slot"),
    "freshstart": ("READY", None),
    "freshnoopen": ("FAILED", "game was not ready"),
    "freshloadsslot": ("FAILED", "a save was loaded"),
    "freshbadmap": ("FAILED", "not allowed"),
}
# Modes of the fresh start (spec 06, part E): HARNESS_NEW_GAME=1, no slot is loaded.
FRESH_MODES = {"freshstart", "freshnoopen", "freshloadsslot", "freshbadmap"}
# Exact number of pauseGame calls, where a mode checks it.
PAUSE_CALLS = {"happy": 1, "cinematic": 1, "nocinematic": 1, "silentrestart": 2}

# How each mode changes the fake game. Times are fake seconds.
SLOT_LIST_DELAY_S = 4
CLOCK_HOLD_S = 12  # longer than the ready check, as in the real game (about 8 s)
LATE_REVERT_S = 17  # the cinematic ends (or the silent restart happens) at this time after the load
CINEMATIC_START_S = 5
SETTLE_AFTER_READY_S = 10


def state_options(mode):
    options = {}
    if mode == "slotlate":
        options["slot_list_delay"] = SLOT_LIST_DELAY_S
    if mode == "noslot":
        options["wanted_slot_listed"] = False
    if mode == "missing":
        options["save_exists"] = False
    clock = {"hold_seconds": CLOCK_HOLD_S, "cinematic": (CINEMATIC_START_S, LATE_REVERT_S)}
    if mode == "nocinematic":
        clock["cinematic"] = None
    if mode == "silentrestart":
        clock.update(cinematic=None, late_revert_after=LATE_REVERT_S)
    if mode == "cinematicstuck":
        clock["cinematic"] = (CINEMATIC_START_S, None)
    if mode == "pausefails":
        clock["pause_works"] = False
    if mode == "neverstarts":
        clock["starts"] = False
    options["clock"] = FakeGameClock(**clock)
    if mode == "autosavefails":
        options["autosave_works"] = False
    if mode == "newgame":
        options["load_starts_new_game"] = True
    if mode == "freshnoopen":
        options["open_map_works"] = False
    if mode == "freshloadsslot":
        options["open_map_loads_slot"] = "saveGame_3"
    return options


def mode_env(mode):
    env = {"HARNESS_AUTOBOOT": "1", "HARNESS_TEST_SAVE": "saveGame_0"}
    if mode in FRESH_MODES:
        env["HARNESS_NEW_GAME"] = "1"
        env["HARNESS_NEW_GAME_MAP"] = "bad map!" if mode == "freshbadmap" else "Jagged_Cliffs"
    return env


def run_mode(mode, boot_script=None, **game_options):
    """boot_script: path of another main.lua (to prove that an old, buggy version is caught)."""
    env = mode_env(mode)
    with FakeGame(env=env, **game_options) as game:
        state = build_manor_lords_state(game, **state_options(mode))
        if boot_script:
            game.load_script(boot_script)
        else:
            game.load_mod("HarnessBoot")
        seconds = game.run_until_idle()

        boot = game.read_json("boot.json")
        marker = game.read_text("ready.marker").strip() if "ready.marker" in game.files() else None
        clock_at_ready = state.clock.time
        game.advance(SETTLE_AFTER_READY_S)  # the game may restart the clock after READY
        return boot, marker, list(state.calls) + state.clock.calls + list(state.autosave.calls), seconds, (
        clock_at_ready, state.clock.time, state.autosave.remaining())


def check(mode, boot_script=None):
    boot, marker, calls, seconds, clocks = run_mode(mode, boot_script)
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
        if not any(call.startswith("SetAutosavePeriodOnPawn") for call in calls):
            problems.append("the autosave timer was never restarted")
        if clocks[2] < 1000000:
            problems.append(f"the autosave timer has only {clocks[2]:.0f} s left")
        if [h["state"] for h in boot["history"]].index("DISABLING_AUTOSAVE") > [h["state"] for h in boot["history"]].index("PAUSING"):
            problems.append("autosave was disabled after the pause")
        wanted = PAUSE_CALLS.get(mode)
        if wanted is not None and calls.count("pauseGame") != wanted:
            problems.append(f"pauseGame was called {calls.count('pauseGame')} times, expected {wanted}")
        if clocks[0] != clocks[1]:
            problems.append(f"the clock moved after READY ({clocks[0]} -> {clocks[1]}): the game was not really paused")
    elif marker is not None:
        problems.append("ready.marker exists after a failure")
    if mode == "missing" and calls:
        problems.append(f"menu was touched before the failure: {calls}")
    if mode in FRESH_MODES:
        if any(call.startswith(("LoadGame", "SwitchToLoadScreen")) for call in calls):
            problems.append(f"the fresh start touched the load screen: {calls}")
    if mode == "freshstart" and "ConsoleCommand:open /Game/NotStronghold/Maps/NewMapSets/Jagged_Cliffs" not in calls:
        problems.append(f"the map was not opened as expected: {calls}")
    if mode == "freshbadmap" and any(call.startswith("ConsoleCommand") for call in calls):
        problems.append("a bad map name reached the console")

    history = [h["state"] for h in boot["history"]]
    print(f"{'PASS' if not problems else 'FAIL'}  {mode:10} seconds={seconds:5.1f} calls={calls} history={history}")
    for problem in problems:
        print("      -", problem)
    return not problems


if __name__ == "__main__":
    modes = sys.argv[1:] or ALL_MODES
    results = [check(mode) for mode in modes]
    sys.exit(0 if all(results) else 1)
