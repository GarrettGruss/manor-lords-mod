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
#   autosavefails SetAutosavePeriodOnPawn answers true but the timer stays; FAILED before the game is paused
#
# The fake game is the kit in harness/tests/fakegame. It copies a real behavior: for a few seconds after the load the game holds the clock at 0.
# Then it starts the clock itself, and that undoes any pause made too early.
# Later the game undoes the pause once more (as seen in the real game, 2 to 4 s after the pause).
# After READY the test lets 10 more seconds pass and checks that the clock did not move.
import json
import sys

import fakegame_path  # noqa: F401  (makes the fakegame package importable)
from fakegame import FakeGame, FakeGameClock, build_manor_lords_state

ALL_MODES = ["happy", "slotlate", "noslot", "missing", "pausefails", "neverstarts", "autosavefails"]

# What each mode must end with: (state, text that the failure reason must contain)
EXPECTED = {
    "happy": ("READY", None),
    "slotlate": ("READY", None),
    "noslot": ("FAILED", "did not appear in the save list"),
    "missing": ("FAILED", "does not exist"),
    "pausefails": ("FAILED", "clock did not stop"),
    "neverstarts": ("FAILED", "clock never started"),
    "autosavefails": ("FAILED", "autosave timer was not pushed away"),
}

# How each mode changes the fake game. Times are fake seconds.
SLOT_LIST_DELAY_S = 4
CLOCK_HOLD_S = 12  # longer than the ready check, as in the real game (about 8 s)
LATE_REVERT_S = 17  # the game restarts the clock once more, shortly after our pause
SETTLE_AFTER_READY_S = 10


def state_options(mode):
    options = {}
    if mode == "slotlate":
        options["slot_list_delay"] = SLOT_LIST_DELAY_S
    if mode == "noslot":
        options["wanted_slot_listed"] = False
    if mode == "missing":
        options["save_exists"] = False
    clock = {"hold_seconds": CLOCK_HOLD_S, "late_revert_after": LATE_REVERT_S}
    if mode == "pausefails":
        clock["pause_works"] = False
    if mode == "neverstarts":
        clock["starts"] = False
    options["clock"] = FakeGameClock(**clock)
    if mode == "autosavefails":
        options["autosave_works"] = False
    return options


def run_mode(mode, boot_script=None, **game_options):
    """boot_script: path of another main.lua (to prove that an old, buggy version is caught)."""
    env = {"HARNESS_AUTOBOOT": "1", "HARNESS_TEST_SAVE": "saveGame_0"}
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
        if clocks[0] != clocks[1]:
            problems.append(f"the clock moved after READY ({clocks[0]} -> {clocks[1]}): the game was not really paused")
    elif marker is not None:
        problems.append("ready.marker exists after a failure")
    if mode == "missing" and calls:
        problems.append(f"menu was touched before the failure: {calls}")

    history = [h["state"] for h in boot["history"]]
    print(f"{'PASS' if not problems else 'FAIL'}  {mode:10} seconds={seconds:5.1f} calls={calls} history={history}")
    for problem in problems:
        print("      -", problem)
    return not problems


if __name__ == "__main__":
    modes = sys.argv[1:] or ALL_MODES
    results = [check(mode) for mode in modes]
    sys.exit(0 if all(results) else 1)
