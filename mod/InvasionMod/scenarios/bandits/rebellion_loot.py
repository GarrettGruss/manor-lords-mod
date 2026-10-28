"""Change update-banditry-rebellion-raid, task 2.5: the corpse pit pays the loot override of a killed rebel brigand.

Fixture: `base-corpse-pit` (a built corpse pit, ten families whose homes hold weapons). Run:
  uv run python harness/run.py --scenario bandits-rebellion-loot --fixture base-corpse-pit --max-runs 1000
Steps: assign a family to the pit, start a rebellion (`bandits_leave_now`), check that the goods of the homes are loot overrides,
kill 4 brigands (just_die), wait until the workers deliver bodies, and check that the pit gained the override goods and the entries ended.
Pit bodies come in any order: the check counts the entries that ended and the goods they held. It saves nothing.
"""

NAME = "bandits-rebellion-loot"
DESCRIPTION = "Killed rebel brigands: their bodies give the override goods at the corpse pit."
LIMIT_S = 1800
SPEED = 3
LONG_REASON = "The pit workers need up to some game days to carry the bodies."
DAY_LIMIT = 14
PIT_TYPE = 113
KILLS = 4


def pit_state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_pit_state")


def overrides(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_override_state")


def entry_goods(state: dict) -> int:
    return sum(len(entry["goods"]) for entry in state["entries"])


def pit_goods(ctx) -> dict:
    return {row["good"]: row["amount"] for row in pit_state(ctx)["pits"][0]["goods"]}


def warm_up(ctx) -> None:
    for attempt in range(4):
        try:
            ctx.time.run_game_seconds(2, speed=SPEED)
            return
        except Exception as error:  # TimeControlError: the clock holds after a load
            ctx.log.info(f"warm-up {attempt} failed: {error}")
            ctx.popups()
    raise RuntimeError("the game clock did not start")


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    warm_up(ctx)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.bandits_state")["bandit_pawn"] is True, 90, what="the Outlaws pawn")
    ctx.check("the fixture has one corpse pit", len(pit_state(ctx)["pits"]) == 1, pit_state(ctx))
    assigned = ctx.actions._command("building_assign_worker", type=PIT_TYPE)  # before the rebellion: later no family is free
    ctx.check("a family works at the pit", assigned.get("ok") is True, assigned)
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    ctx.check("the fixture has armed families", homes["valid"] >= 6, homes["valid"])
    ctx.mod.command("InvasionMod.bandits_leave_now", count=6)
    leave = ctx.mod.command("InvasionMod.bandits_state")["last_leave"]
    ctx.check("the rebellion spawned a squad", leave["spawned"] is True and leave["bandit_units"] == 18, leave)
    before = overrides(ctx)
    goods_before = entry_goods(before)
    ctx.metric("override_goods", goods_before)
    ctx.check("the taken goods are overrides", goods_before == leave["taken"] and goods_before > 0, [goods_before, leave["taken"]])
    base_pit = pit_goods(ctx)
    killed = ctx.mod.command("InvasionMod.raid_behavior_test_kill_override_units", count=KILLS)
    ctx.check("units with an entry were killed", killed["killed"] == KILLS, killed)
    ctx.metric("killed", killed["killed"])
    ctx.run_until(lambda: any(entry.get("dead_day") is not None for entry in overrides(ctx)["entries"]), 30, what="a dead entry")
    dead_entries = sum(1 for entry in overrides(ctx)["entries"] if entry.get("dead_day") is not None)
    ctx.metric("dead_entries", dead_entries)
    ctx.check("killed units are marked dead in the override state", dead_entries >= 1, dead_entries)
    # The worker family may be among the families that left (6 of 10). Then no body reaches the pit and the check below fails: run again.
    # Adding a family with family_add and assigning it crashed the game in three runs (rb-loot-6 to 8), so the test does not do it.
    ctx.screenshot("loot_before_pit")
    days = 0
    while days < DAY_LIMIT and overrides(ctx)["paid_bodies"] < 1:
        run_day(ctx)
        days += 1
    after = overrides(ctx)
    ctx.metric("days_to_pay", days)
    ctx.metric("pit_corpses", pit_state(ctx)["pits"][0]["corpses"])
    ctx.metric("paid_bodies", after["paid_bodies"])
    ctx.metric("paid_goods", after["paid_goods"])
    ctx.check("at least one body was paid at the pit", after["paid_bodies"] >= 1, after["paid_bodies"])
    gained = sum(amount - base_pit.get(good, 0) for good, amount in pit_goods(ctx).items() if good in (133, 271, 163, 164, 177, 178, 205, 206, 270, 273, 288, 289))
    ctx.metric("pit_gain_weapon_goods", gained)
    ctx.check("the pit gained exactly the paid override goods", gained == after["paid_goods"], [gained, after["paid_goods"]])
    ctx.check("each paid body ended one entry", after["count"] <= before["count"] - after["paid_bodies"], [before["count"], after["count"], after["paid_bodies"]])
    ctx.screenshot("loot_after_pit")
    return ctx.result()
