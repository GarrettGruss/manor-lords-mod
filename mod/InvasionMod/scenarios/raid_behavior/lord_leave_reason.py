"""M03.02 follow-up: a lord raid leaves by the reasons losses and time (A2, A3).

Option (run.py --env): LEAVE_REASON = losses | time (default losses).
Test commands set small leave values for this session: the loot rule is switched off, so the wanted rule decides.
The scenario runs game days until the raid has left, then checks the reason and that no raider stays. It saves nothing.
"""

import re

from runlib.units import side_count

NAME = "raid-behavior-lord-leave-reason"
DESCRIPTION = "A lord raid leaves by losses or by the time limit when small test values are set."
LIMIT_S = 900
SPEED = 3
LONG_REASON = "The time reason needs 3 game days plus the walk-off of the army (about 60 game seconds)."
DAY_LIMIT = 12
GRACE_DAYS = 3
KILL_SHARE = 0.7
MAX_DAYS_TEST = 3
NEVER = 10.0


def record(ctx) -> dict:
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
    reason = ctx.variant_option("LEAVE_REASON", "losses")
    ctx.check("the option is known", reason in ("losses", "time"), reason)
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    bandits_before = side_count(ctx.actions.units_census(), "bandit")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(record(ctx)), 30, what="the raid record")
    ctx.check("the raid is a lord raid", record(ctx).get("lord_raid") is True, record(ctx))

    if reason == "time":
        ctx.mod.command("InvasionMod.raid_behavior_test_set_leave", loot_per_raider=1000, loss_share=NEVER, max_days=MAX_DAYS_TEST)
    else:
        ctx.mod.command("InvasionMod.raid_behavior_test_set_leave", loot_per_raider=1000, max_days=1000)
        ctx.time.run_game_seconds(20, speed=SPEED)
        ctx.log.info(f"killed: {ctx.mod.command('InvasionMod.raid_behavior_test_kill_raiders', share=KILL_SHARE)}")

    raid, days = record(ctx), 0
    while raid["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        raid = record(ctx)
        ctx.log.info(f"day {days}: {raid}")
    ctx.check("the raid left", raid["state"] == "left", [raid["state"], days])
    ctx.check("the leave reason is the wanted one", raid.get("leave_reason") == reason, raid.get("leave_reason"))
    log = (ctx.run_dir / "mod.log").read_text(encoding="utf-8", errors="replace")
    fired = re.search(r"role raid must leave id=\d+ day=(\d+) reason=" + reason, log)
    ctx.check("the leave rule fired once in the log", fired is not None, reason)
    if fired and reason == "time":
        waited = int(fired.group(1)) - raid["start_day"]
        ctx.check("the time rule fired at max_days", waited == MAX_DAYS_TEST, waited)
    if fired:
        ctx.metric("walk_off_days", raid["start_day"] + days - int(fired.group(1)))
    for _ in range(GRACE_DAYS):
        if record(ctx)["living"] == 0:
            break
        run_day(ctx)
    raid = record(ctx)
    added = side_count(ctx.actions.units_census(), "bandit") - bandits_before
    ctx.check("A4 no raider stays on the map", raid["living"] == 0 and added <= 0, [raid["living"], added])
    owners = [row.get("owner") or "" for row in ctx.actions.regions_state().get("regions", [])]
    ctx.check("the player still owns a region", any("MyPawn" in owner for owner in owners), owners)
    ctx.metric("days", days)
    ctx.metric("deaths", raid["deaths"])
    ctx.metric("plundered", raid["plundered"])
    return ctx.result()
