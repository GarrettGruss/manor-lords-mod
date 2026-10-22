"""M06 iteration 01, A4: a role raid that wins (loot or time) sacks the town once. A raid that loses many raiders does not.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The raid is a small forced role raid. It saves nothing.
"""

NAME = "sack-and-terms-raid-sack"
DESCRIPTION = "A role raid that leaves with its loot sacks the town once; the village keeps people."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "A role raid leaves after up to 25 game days. At speed 3 this takes up to 300 s plus the start."
DAY_LIMIT = 40
GRACE_DAYS = 2


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    ctx.check("the raid is a role raid", tracker(ctx)["roles"] is True, tracker(ctx))

    days = 0
    while tracker(ctx)["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
    for _ in range(GRACE_DAYS):
        run_day(ctx)
    raid = tracker(ctx)
    sack = ctx.mod.command("InvasionMod.sack_state")
    reason = raid.get("leave_reason")
    ctx.check("the raid left with a reason", reason in ("loot", "losses", "time"), reason)
    expected = 1 if reason in ("loot", "time") else 0
    ctx.check("A4 one sack for a won battle, none for a lost raid", sack["sack_count"] == expected, [reason, sack["sack_count"]])
    if expected:
        ctx.check("A4 the sack reason is the leave reason", sack["history"][0]["reason"] == reason, sack["history"])
    population = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.check("A3 the village still has people after the raid and the sack", population is not None and population > 0, population)
    ctx.metric("days", days)
    ctx.metric("sack_count", sack["sack_count"])
    ctx.metric("population", population)
    return ctx.result()
