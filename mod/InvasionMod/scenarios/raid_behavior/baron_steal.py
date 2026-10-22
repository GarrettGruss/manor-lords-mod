"""Change add-raid-storage-tiers: the units of a baron (lord) raid steal from tier 1 stores while they are far from the battle marker.

Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The raid is a small forced raid, so the steal goal is 100.
The scenario runs game days until the raid ends or DAY_LIMIT. Each day it reads the steal total of the tracker. The total must never fall,
never pass the goal, and must stop at the goal. It saves nothing.
"""

NAME = "raid-behavior-baron-steal"
DESCRIPTION = "A baron raid steals from tier 1 stores, at most the steal goal."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "A lord raid needs game days to march and to fight. At speed 3 up to 40 game days take up to 400 s plus the start."
DAY_LIMIT = 40


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_state")


def tracker(ctx) -> dict:
    raids = state(ctx)["raids"]
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
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=int(ctx.variant_option("INVASION_DIFFICULTY", "1")))
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    config = state(ctx)["steal"]
    goal = config["goals"]["plunder"]
    ctx.check("the raid is a baron (lord) raid", tracker(ctx).get("lord_raid") is True, tracker(ctx))
    totals, days = [], 0
    while tracker(ctx)["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        totals.append(tracker(ctx)["stolen"])
        ctx.log.info(f"day {days}: stolen {totals[-1]}")
    raid = tracker(ctx)
    ctx.check("the raiders stole goods while they were far from the marker", raid["stolen"] > 0, totals)
    ctx.check("the steal total never falls", all(b >= a for a, b in zip(totals, totals[1:])), totals)
    ctx.check("the steal total is not above the goal", max(totals + [0]) <= goal, [totals, goal])
    reached = next((i for i, value in enumerate(totals) if value >= goal), None)
    if reached is not None:
        ctx.check("no goods are taken after the goal", all(value == totals[reached] for value in totals[reached:]), totals)
    ctx.metric("days", days)
    ctx.metric("stolen", raid["stolen"])
    ctx.metric("steal_goal", goal)
    ctx.metric("threshold", config["threshold"])
    return ctx.result()
