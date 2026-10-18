"""M03 iteration 02, A1 to A4 and A6: a Hussite role raid (spawnArmy squads) leaves by itself.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The raid is a small forced role raid. The scenario adds no steering.
It runs game days until the raid leaves, and checks the reason, the time and that no raider stays. It saves nothing.
"""

from runlib.units import side_count

NAME = "raid-behavior-role-leave"
DESCRIPTION = "A role raid ends by loot, losses or time and no raider stays on the map."
LIMIT_S = 900
SPEED = 3
LONG_REASON = "A role raid leaves after up to 25 game days. At speed 3 this takes up to 300 s plus the start."
DAY_LIMIT = 30  # config max_days is 25; A3 allows 40
REASONS = ("loot", "losses", "time")
GRACE_DAYS = 3


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
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    bandits_before = side_count(ctx.actions.units_census(), "bandit")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    raid = tracker(ctx)
    ctx.check("A5 the raid is a role raid", raid["roles"] is True, raid)

    days = 0
    while raid["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        raid = tracker(ctx)
        ctx.log.info(f"day {days}: {raid}")
    ctx.check("A1-A3 the role raid left within the day limit", raid["state"] == "left", [raid["state"], days])
    ctx.check("A1-A3 the leave reason is loot, losses or time", raid.get("leave_reason") in REASONS, raid.get("leave_reason"))

    for _ in range(GRACE_DAYS):
        if tracker(ctx)["living"] == 0:
            break
        run_day(ctx)
    raid = tracker(ctx)
    added = side_count(ctx.actions.units_census(), "bandit") - bandits_before
    ctx.check("A4 no raider of the raid stays on the map", raid["living"] == 0 and added <= 0, [raid["living"], added])
    population = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.check("A6 the village still has people", population is not None and population > 0, population)
    ctx.metric("days", days)
    ctx.metric("leave_reason", raid.get("leave_reason"))
    ctx.metric("looted_total", raid["looted_total"])
    ctx.metric("deaths", raid["deaths"])
    ctx.metric("carried_out", raid["carried_out"])
    return ctx.result()
