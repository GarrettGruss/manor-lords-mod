"""After a world load in the same session, the autosave timer of the new player pawn must be far away again.

The load is a fresh start on a map (console command `open`). It calls no save function.
"""

import time

NAME = "autosave-after-load"
DESCRIPTION = "A world load restarts the game autosave timer. HarnessBoot must push it away again."
LIMIT_S = 180
MAP = "/Game/NotStronghold/Maps/NewMapSets/Jagged_Cliffs"
MIN_REMAINING_S = 1_000_000
WAIT_AFTER_LOAD_S = 20


def run(ctx) -> dict:
    expect = ctx.expect
    before = ctx.actions.autosave_status()
    expect.at_least("autosave timer is far away at READY (s)", before.get("remaining_s", 0), MIN_REMAINING_S)

    ctx.bridge._result("console", command="open " + MAP)
    time.sleep(WAIT_AFTER_LOAD_S)

    after = None
    for _ in range(20):
        try:
            after = ctx.actions.autosave_status()
            if after.get("timer_exists") and after.get("handle_id") != before.get("handle_id"):
                break
        except Exception:  # the world is still loading
            pass
        time.sleep(2)
    expect.equals("a new timer exists after the load", bool(after) and after.get("handle_id") != before.get("handle_id"), True)
    expect.at_least("autosave timer is far away after the load (s)", (after or {}).get("remaining_s", 0), MIN_REMAINING_S)
    return ctx.result()
