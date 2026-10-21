"""Boot timing regression test: after READY the clock stays still for 30 s, and boot.json and the log are in the known ranges.

Ranges come from 413 past READY runs (boot 29 to 105.5 s, 1 or 2 pause calls). See the change add-boot-timing-regression-tests.
"""

import json

from runlib.game import count_pause_calls

NAME = "boot-timing"
DESCRIPTION = "HarnessBoot timing: still clock for 30 s, boot.json state order, boot seconds and pause calls in range."
LIMIT_S = 90

CLOCK_WAIT_S = 30
BOOT_SECONDS_RANGE = (20, 120)
PAUSE_CALLS_RANGE = (1, 3)
SAVE_STATES = ["WAITING_FOR_MENU", "LOADING_SAVE", "WAITING_FOR_READY", "DISABLING_AUTOSAVE", "PAUSING", "READY"]


def run(ctx) -> dict:
    boot = json.loads(ctx.run.boot_path.read_text(encoding="utf-8"))
    states = [change["state"] for change in boot.get("history", [])]
    ctx.check("boot.json history has the save states in order, each once", states == SAVE_STATES, states)
    ctx.check("boot.json state is READY", boot.get("state") == "READY", boot.get("state"))
    seconds = boot["updated"] - boot["started"]
    ctx.check_range("boot seconds", seconds, *BOOT_SECONDS_RANGE)
    pause_calls = count_pause_calls(ctx.run.path / "mod.log")
    ctx.check_range("pause calls", pause_calls, *PAUSE_CALLS_RANGE)
    ctx.metric("boot_seconds", seconds)
    ctx.metric("pause_calls", pause_calls)

    clock = ctx.read_clock(wait_s=CLOCK_WAIT_S)
    ctx.check("clock stays still", clock["paused"], clock["change"], [0, 0.001])
    result = ctx.result()
    result["clock"] = clock
    return result
