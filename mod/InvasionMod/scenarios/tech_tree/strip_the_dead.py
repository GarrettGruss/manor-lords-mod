"""Change update-tech-tree-yearly-picks: Strip the Dead. The corpse pit pays loot for bandit bodies only while the law is in force.

Fixture: the default `base-corpse-pit` (a built corpse pit). Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1).
Steps: assign a family to the pit, unlock Corpse Robbing, force a small NATIVE raid (roles off, Brigands), kill half of the raiders
and wait until their bodies reach the pit WITHOUT the law: the pit must gain no goods and the mod order must not change.
Then enact Strip the Dead, kill the rest and wait for the bodies: each looted body adds one variant of `raid_behavior.body_loot`
(sword 177 and small shield 270, and in half of the bodies a helmet 273) and lowers the mod order by 1.
It saves nothing.
"""

NAME = "tech-tree-strip-the-dead"
DESCRIPTION = "Without Strip the Dead a body at the pit pays nothing; with it each bandit body pays a loot variant and costs 1 order."
LIMIT_S = 1800
SPEED = 3
LONG_REASON = "The pit workers need up to 3 game days for the bodies, twice. At speed 3 this takes minutes."
DAY_LIMIT = 12
PIT_TYPE = 113
SWORD, SMALL_SHIELD, HELMET = 177, 270, 273
PREFIX = "InvasionMod."


def pit_state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "raid_behavior_pit_state")


def amount(goods: list, good: int) -> int:
    return next((row["amount"] for row in goods if row["good"] == good), 0)


def order(ctx) -> dict:
    return ctx.mod.command(PREFIX + "bandits_state")


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def wait_for_bodies(ctx, unpaid_start: int) -> int:
    """Run game days until a tracked body was consumed at the pit. Returns the number of bodies consumed."""
    for _ in range(DAY_LIMIT):
        if pit_state(ctx)["raids"][0]["unpaid_other"] < unpaid_start:
            break
        run_day(ctx)
    return unpaid_start - pit_state(ctx)["raids"][0]["unpaid_other"]


def kill(ctx, share: float) -> int:
    before = pit_state(ctx)["raids"][0]["unpaid_other"]
    killed = ctx.mod.command(PREFIX + "raid_behavior_test_kill_raiders", share=share)["killed"]
    ctx.run_until(lambda: pit_state(ctx)["raids"][0]["unpaid_other"] >= before + killed, 30, what="the deaths noted")
    return pit_state(ctx)["raids"][0]["unpaid_other"]


def run(ctx) -> dict:
    ctx.check("the fixture has one corpse pit", len(pit_state(ctx)["pits"]) == 1, pit_state(ctx))
    ctx.check("a family works at the pit", ctx.actions._command("building_assign_worker", type=PIT_TYPE).get("ok") is True)
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    ctx.check("S1 Corpse Robbing is unlocked", "corpse_robbing" in ctx.mod.command(PREFIX + "tech_tree_unlock", node="corpse_robbing")["unlocked"])
    ctx.mod.command(PREFIX + "invasion_set_difficulty", value=int(ctx.variant_option("INVASION_DIFFICULTY", "1")))
    ctx.mod.command(PREFIX + "invasion_set_roles", enabled=False)  # a native raid: Brigands from spawnRaiders
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command(PREFIX + "invasion_set_size", size="small")
    ctx.mod.command(PREFIX + "invasion_force_next")
    ctx.run_until(lambda: (pit_state(ctx)["raids"] or [{}])[0].get("id") is not None, 30, what="the raid record")
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "raid_behavior_state")["raids"][0]["initial"] > 0, 30, what="the raiders at the start")
    raid = ctx.mod.command(PREFIX + "raid_behavior_state")["raids"][0]
    ctx.check("S2 the raid is a native raid", raid.get("raid_type") is None, raid)

    # Without the law.
    pit_before = pit_state(ctx)["pits"][0]
    ctx.mod.command(PREFIX + "bandits_set_order", value=60)
    order_before = order(ctx)
    unpaid = kill(ctx, 0.5)
    ctx.metric("bodies_without_law", unpaid)
    consumed = wait_for_bodies(ctx, unpaid)
    ctx.check("S3 bodies reached the pit without the law", consumed >= 1, consumed)
    pit_mid = pit_state(ctx)["pits"][0]
    for good in (SWORD, SMALL_SHIELD, HELMET):
        ctx.check(f"S4 no good {good} was paid without the law", amount(pit_mid["goods"], good) == amount(pit_before["goods"], good),
                  [amount(pit_before["goods"], good), amount(pit_mid["goods"], good)])
    ticks_mid = order(ctx)["ticks"]
    if ticks_mid == order_before["ticks"]:
        ctx.check("S5 the order did not change without the law", order(ctx)["mod_order"] == 60, order(ctx)["mod_order"])
    else:
        ctx.notes.append("S5 skipped: a banditry tick ran in this phase")

    # With the law.
    enacted = ctx.mod.command(PREFIX + "tech_tree_enact_law", law="strip_the_dead")
    ctx.check("S6 the law is in force", "strip_the_dead" in enacted["laws"], enacted)
    ctx.mod.command(PREFIX + "bandits_set_order", value=60)
    ticks_start = order(ctx)["ticks"]
    pit_start = pit_state(ctx)["pits"][0]
    unpaid = kill(ctx, 1.0)
    ctx.metric("bodies_with_law", unpaid)
    ctx.screenshot("strip_pit_before")
    paid = wait_for_bodies(ctx, unpaid)
    ctx.metric("bodies_looted", paid)
    ctx.check("S7 bodies were looted under the law", paid >= 1, paid)
    after = pit_state(ctx)["pits"][0]
    gain = {good: amount(after["goods"], good) - amount(pit_start["goods"], good) for good in (SWORD, SMALL_SHIELD, HELMET)}
    ctx.metric("gain_sword", gain[SWORD])
    ctx.metric("gain_small_shield", gain[SMALL_SHIELD])
    ctx.metric("gain_helmet", gain[HELMET])
    ctx.check("S8 each looted body paid one sword and one small shield", gain[SWORD] == paid and gain[SMALL_SHIELD] == paid, [gain, paid])
    ctx.check("S9 at most one helmet for each looted body", 0 <= gain[HELMET] <= paid, [gain, paid])
    ctx.screenshot("strip_pit_after")
    if order(ctx)["ticks"] == ticks_start:
        ctx.check("S10 the order fell by 1 for each looted body", order(ctx)["mod_order"] == 60 - paid, [order(ctx)["mod_order"], paid])
    else:
        ctx.notes.append("S10 skipped: a banditry tick ran in this phase")
    stored = sum(row["amount"] for row in after["goods"])
    ctx.check("S11 the storage limit of the pit covers the stored goods", after["limit"] >= stored, (after["limit"], stored))
    return ctx.result()
