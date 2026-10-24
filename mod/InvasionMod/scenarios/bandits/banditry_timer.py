"""Bandits: low order starts a 90 game day timer, the timer resets, and the villagers leave when it expires.

The expiry is brought forward with `bandits_set_timer_days_left`, so the test needs a few game days, not 90.
It works with and without the game's bandit pawn: the villagers must leave in both worlds, and the mod must log it.
Run on the default fixture and on `--fixture playtest-noai`. It saves nothing.
"""

from runlib.units import side_count

NAME = "bandits-banditry-timer"
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "About 3 game days at speed 3, then 10 game days at speed 1 (the game forces speed 1 while bandits are near), plus the start."


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def bandits(ctx) -> int:
    return side_count(ctx.actions.units_census(), "bandit")


def run(ctx) -> dict:
    low = ctx.mod.command("InvasionMod.bandits_set_order", value=20)
    ctx.check("order 20 starts the timer", low["timer"]["active"] is True, low["timer"])
    ctx.check("the timer has 85 to 95 game days", 85 <= low["timer"]["days_left"] <= 95, low["timer"])

    reset = ctx.mod.command("InvasionMod.bandits_set_order", value=25)
    ctx.check("order 25 stops the timer", reset["timer"]["active"] is False, reset["timer"])
    ctx.check("no family left", reset["converted_families"] == 0, reset)

    ctx.mod.command("InvasionMod.bandits_set_order", value=20)
    before = state(ctx)
    units_before = bandits(ctx)
    ctx.mod.command("InvasionMod.bandits_set_timer_days_left", days=2)
    ctx.time.run_game_days(3, speed=SPEED)
    ctx.run_until(lambda: state(ctx)["leaves"] >= 1, 60, what="the leave")
    after = state(ctx)
    leave = after["last_leave"]
    ctx.check("between 1 and 18 families left", 1 <= leave["removed"] <= 18, leave)
    ctx.check("the village keeps at least 1 family", after["families"] >= 1, after)
    ctx.check("the families dropped by the number that left", after["families"] <= before["families"] - leave["removed"] + 5, [before["families"], after["families"], leave])
    ctx.check("the order rose by 25 (a tick may add 10)", 45 <= after["mod_order"] <= 55, after["mod_order"])
    ctx.check("the timer is off because the order is 25 or more", after["timer"]["active"] is False, after["timer"])
    if after["bandit_pawn"]:
        ctx.run_until(lambda: bandits(ctx) > units_before, 20, what="the bandit squads")
        ctx.check("bandit units appeared", bandits(ctx) > units_before, [units_before, bandits(ctx)])
    else:
        ctx.check("no bandit pawn: no bandit spawned and it is logged", leave["spawned"] is False and bandits(ctx) == units_before, leave)
        log = ctx.run_dir / "mod.log"
        text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        ctx.check("the log says that no bandits spawned", "no bandits spawned" in text, "log line missing")

    ctx.time.run_game_days(10, speed=1)  # the game resets a higher speed while the new bandits are near
    final = state(ctx)
    ctx.check("the game runs 10 more game days", final["day"] >= after["day"] + 10, [after["day"], final["day"]])
    ctx.metric("families_left", leave["removed"])
    ctx.metric("bandit_pawn", 1 if after["bandit_pawn"] else 0)
    return ctx.result()
