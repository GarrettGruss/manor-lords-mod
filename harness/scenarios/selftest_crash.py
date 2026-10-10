"""Test scenario. It makes the real game crash on purpose, to test the crash verdict and the crash report copy."""

import os

NAME = "selftest-crash"
LIMIT_S = 60
HIDDEN = True

# Both calls ended the game process in the spec 07 probes (actions-catalog.md). Neither one saves.
CRASH_CALLS = {
    "getItem": lambda ctx: ctx.bridge.call_function(ctx.bridge.engine_path(), "getItem", [1]),
    "playEventMessage": lambda ctx: ctx.bridge.call_function(
        ctx.bridge.player_path(), "playEventMessage", ["Default", "Crash test", "Crash test"]),
}


def run(ctx) -> dict:
    call_name = os.environ.get("HARNESS_CRASH_CALL", "getItem")
    ctx.log.info(f"selftest-crash: calling {call_name}, the game should end")
    CRASH_CALLS[call_name](ctx)
    ctx.log.info("selftest-crash: the call returned, so the game did not crash")
    return ctx.check("game crashed", False, "the call returned")
