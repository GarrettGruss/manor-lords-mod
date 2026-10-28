"""Bandits: low order starts a 60 game day timer, the timer resets, and the armed families rebel when it expires.

The expiry is brought forward with `bandits_set_timer_days_left`, so the test needs a few game days, not 60.
The rebellion needs 6 families that hold weapons at home (fewer when the village is small). The fixture `base` has them. On `playtest-noai` the test
puts weapons into the homes first. One Brigands squad (18 units) of the pawn Outlaws spawns; no camp is made.
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


def warm_up(ctx) -> None:
    for attempt in range(4):
        try:
            ctx.time.run_game_seconds(2, speed=SPEED)
            return
        except Exception as error:  # the clock holds for a while after a load
            ctx.log.info(f"warm-up {attempt} failed: {error}")
            ctx.popups()
    raise RuntimeError("the game clock did not start")


def run(ctx) -> dict:
    warm_up(ctx)
    ctx.run_until(lambda: state(ctx)["bandit_pawn"] is True, 90, what="the Outlaws pawn")
    for _ in range(12):  # the camp cleanup of the Outlaws init needs game time
        if not state(ctx)["outlaws"]["camp_cleanup"]:
            break
        ctx.time.run_game_seconds(20, speed=SPEED)
    low = ctx.mod.command("InvasionMod.bandits_set_order", value=20)
    ctx.check("order 20 starts the timer", low["timer"]["active"] is True, low["timer"])
    ctx.check("the timer has 55 to 65 game days", 55 <= low["timer"]["days_left"] <= 65, low["timer"])

    reset = ctx.mod.command("InvasionMod.bandits_set_order", value=25)
    ctx.check("order 25 stops the timer", reset["timer"]["active"] is False, reset["timer"])
    ctx.check("no family left", reset["converted_families"] == 0, reset)

    ctx.mod.command("InvasionMod.bandits_set_order", value=20)
    before = state(ctx)
    wanted = min(6, before["families"] - 1)
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    units_before = bandits(ctx)
    if homes["valid"] < wanted:
        # The game takes unused weapons out of homes after about a game day. So the timer expires at once (days=0) while the game is paused.
        ctx.mod.command("InvasionMod.bandits_stock_homes", good=133, amount=2, homes=before["families"])
        ctx.mod.command("InvasionMod.bandits_set_timer_days_left", days=0)
    else:
        ctx.mod.command("InvasionMod.bandits_set_timer_days_left", days=2)
        ctx.time.run_game_days(3, speed=SPEED)
    ctx.run_until(lambda: state(ctx)["leaves"] >= 1, 60, what="the rebellion")
    after = state(ctx)
    leave = after["last_leave"]
    ctx.check("up to 6 families left", 1 <= leave["removed"] <= 6 and leave["removed"] == wanted, [leave, wanted])
    ctx.check("the village keeps at least 1 family", after["families"] >= 1, after)
    ctx.check("the families dropped by the number that left", after["families"] <= before["families"] - leave["removed"] + 5, [before["families"], after["families"], leave])
    ctx.check("the order rose by 25 (a tick may add 10)", 45 <= after["mod_order"] <= 55, after["mod_order"])
    ctx.check("the timer is off because the order is 25 or more", after["timer"]["active"] is False, after["timer"])
    ctx.run_until(lambda: bandits(ctx) > units_before, 20, what="the squad")
    ctx.check("bandit units appeared", bandits(ctx) > units_before, [units_before, bandits(ctx)])
    ctx.check("one Brigands squad of 18 spawned", leave["squads"] == 1 and leave["bandit_units"] == 18, leave)
    ctx.check("the pawn was not made by the leave event", leave["pawn_created"] is False, leave)
    ctx.check("the bandit pawn exists afterward", after["bandit_pawn"] is True, after)
    ctx.metric("families_left", leave["removed"])
    ctx.metric("goods_taken", leave["taken"])
    ctx.time.run_game_days(10, speed=1)  # the game resets a higher speed while the new bandits are near
    final = state(ctx)
    ctx.check("the game runs 10 more game days", final["day"] >= after["day"] + 10, [after["day"], final["day"]])
    return ctx.result()
