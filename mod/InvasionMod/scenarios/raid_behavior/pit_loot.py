"""Change add-corpse-pit-loot: the corpse pit gets the body share of the goods that a Hussite raid plundered.

Fixture: the default `base-corpse-pit` (a built corpse pit, no workers). Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1).
Steps: assign a family to the pit (building_assign_worker type=113), force a small Hussite raid, run game days until the plunder
tick has recorded goods, kill the raiders (just_die), then wait until the workers deliver bodies. Each delivered body of the raid
must add floor(record / raiders at the start) of each recorded good to the pit. A body of an animal or a villager is ignored.
It saves nothing.
"""

NAME = "raid-behavior-pit-loot"
DESCRIPTION = "A body of a Hussite raider that reaches the corpse pit adds its share of the plundered goods to the pit."
LIMIT_S = 1800
SPEED = 3
LONG_REASON = "The plunder needs game days, and the pit workers need up to 3 game days for the bodies. At speed 3 this takes minutes."
DAY_LIMIT = 12
PIT_TYPE = 113
CORPSE_ITEM = 233


def pit_state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_pit_state")


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def amount(goods: list, good: int) -> int:
    return next((row["amount"] for row in goods if row["good"] == good), 0)


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    ctx.check("the fixture has one corpse pit", len(pit_state(ctx)["pits"]) == 1, pit_state(ctx))
    assigned = ctx.actions._command("building_assign_worker", type=PIT_TYPE)
    ctx.check("a family works at the pit", assigned.get("ok") is True, assigned)
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=int(ctx.variant_option("INVASION_DIFFICULTY", "1")))
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: tracker(ctx).get("initial", 0) > 0, 30, what="the raiders at the start")
    raid = tracker(ctx)
    ctx.check("the raid is a Hussite raid", raid.get("raid_type") == "hussite", raid)
    initial = raid["initial"]
    days = 0
    while days < DAY_LIMIT and not pit_state(ctx)["raids"][0]["goods"]:
        run_day(ctx)
        days += 1
    record = pit_state(ctx)["raids"][0]["goods"]
    ctx.metric("days_to_record", days)
    ctx.check("the plunder tick recorded goods", bool(record), record)
    base_pit = pit_state(ctx)["pits"][0]
    ctx.screenshot("pit_before")
    killed = ctx.mod.command("InvasionMod.raid_behavior_test_kill_raiders", share=0.5)["killed"]
    ctx.metric("killed", killed)
    ctx.check("raiders were killed", killed >= 1, killed)
    ctx.run_until(lambda: pit_state(ctx)["pits"][0]["corpses"] > base_pit["corpses"], 600, what="a body at the pit")
    ctx.run_until(lambda: pit_state(ctx)["raids"][0]["unpaid"] < killed, 60, what="a paid body")
    ctx.screenshot("pit_after")
    after = pit_state(ctx)
    paid = killed - after["raids"][0]["unpaid"]
    ctx.metric("bodies_paid", paid)
    for row in record:
        share = row["amount"] // initial
        gained = amount(after["pits"][0]["goods"], row["good"]) - amount(base_pit["goods"], row["good"])
        ctx.metric(f"gain_good_{row['good']}", gained)
        ctx.check(f"good {row['good']}: the pit gained {paid} shares of {share}", gained >= paid * share, (gained, paid, share))
    return ctx.result()
