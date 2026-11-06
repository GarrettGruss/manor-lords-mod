"""fix-removed-families-bodies: removed families leave no visible body and no rise in the game's body count.

Run: `uv run python harness\\run.py --scenario removed-families-bodies --fixture playtest-noai --slot 1`.
It removes 2 families with the same call the contracts, bandits and vassals use (ManorCore.remove_families, through the
harness test command `loan_probe` mode `famremove`), looks at the spot where the first person stood, and reads
Region.corpses (the game's body count) at once and some game days later. It saves nothing.
"""

import os

NAME = "removed-families-bodies"
DESCRIPTION = "Remove 2 families; the bodies are hidden and Region.corpses does not rise (pictures before and after)."
LIMIT_S = 300
FAMILIES = 2
PEEK_DAYS = 3


def cmd(ctx, **fields) -> dict:
    return ctx.actions._command("loan_probe", **fields)  # noqa: SLF001


def run(ctx) -> dict:
    ctx.time.run_game_seconds(5, speed=3)
    before_bodies = cmd(ctx, mode="corpses")
    before_state = cmd(ctx, mode="familystate", count=FAMILIES)
    ctx.log.info(f"BODIES before: bodies={before_bodies} members={before_state}")
    rows = before_state["state"]["rows"]
    spot = rows[0]["real"] if rows else None
    if spot:
        ctx.bridge.centre_camera_on(spot["x"], spot["y"])
        ctx.time.run_game_seconds(3, speed=1)
    ctx.screenshot("before")

    # HARNESS_CONTROL=1 uses the old behaviour (just_die only) to show what the fix changes. The checks B2 to B5 then fail.
    answer = cmd(ctx, mode="famkillraw" if os.environ.get("HARNESS_CONTROL") == "1" else "famremove", count=FAMILIES)
    ctx.log.info(f"BODIES removed: {answer}")
    after_now = cmd(ctx, mode="corpses")
    ctx.time.run_game_seconds(4, speed=1)
    after_4s = cmd(ctx, mode="corpses")
    ctx.screenshot("after")
    ctx.check("B1 the people died", answer.get("people", 0) > 0, answer)
    ctx.check("B2 each new body is hidden", after_now["dead_hidden"] - before_bodies["dead_hidden"] == answer.get("people"),
              (before_bodies, after_now, answer))
    ctx.check("B3 the body count did not rise at once", after_now["corpses"] <= before_bodies["corpses"], (before_bodies, after_now))
    ctx.check("B4 the body count did not rise after 4 s", after_4s["corpses"] <= before_bodies["corpses"], (before_bodies, after_4s))

    for day in range(PEEK_DAYS):
        ctx.time.run_game_seconds(40, speed=3)
        later = cmd(ctx, mode="corpses")
        ctx.log.info(f"BODIES day {day + 1}: {later}")
        ctx.check(f"B5.{day + 1} the body count is still not above the start", later["corpses"] <= before_bodies["corpses"], (before_bodies, later))
    ctx.screenshot("after_days")
    return ctx.result()
