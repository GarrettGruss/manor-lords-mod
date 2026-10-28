"""update-liege-tribute-to-contracts: the progress of objectives in the real game (spike: raider kills, bandit camp kills).

Fixture: the default. It saves nothing.
Part 1: kill_raiders counts the dead of a tracked raid (a forced small raid; raid_behavior_test_kill_raiders kills a share).
Part 2 (spike, only recorded): do the dead of a bandit camp count? The metric camp_kills_counted holds the answer.
Part 3: hold_public_order counts game days at or above the minimum.
Part 4: the active contract fails when winter begins (set_season winter; the season value is recorded).
"""

NAME = "liege-contracts-progress"
DESCRIPTION = "Pick kill and hold-order contracts and check that raider deaths and public order days count; record if bandit camp deaths count."
LIMIT_S = 300
PREFIX = "InvasionMod."


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def progress(ctx, index: int = 0) -> int:
    return contracts(ctx)["active"]["objectives"][index]["progress"]


def tracker(ctx) -> dict:
    raids = ctx.mod.command(PREFIX + "raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def kill_part(ctx) -> None:
    ctx.mod.command(PREFIX + "invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command(PREFIX + "invasion_set_size", size="small")
    ctx.mod.command(PREFIX + "invasion_force_next")
    ctx.run_until(lambda: tracker(ctx).get("initial", 0) > 0, 60, what="the raiders at the start")
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="clear_the_roads.keep_the_peace.feed_the_city")
    ctx.mod.command(PREFIX + "liege_contract_pick", id="clear_the_roads")
    ctx.check("P1 the kill count starts at 0 after the pick", progress(ctx) == 0, contracts(ctx)["active"])
    killed = ctx.mod.command(PREFIX + "raid_behavior_test_kill_raiders", share=0.5)["killed"]
    ctx.metric("raid_killed", killed)
    ctx.run_until(lambda: progress(ctx) > 0, 30, what="the deaths are counted", poll_s=1.0)
    counted = progress(ctx)
    ctx.metric("raid_kills_counted", counted)
    ctx.check("P2 the dead raiders are counted", killed > 0 and abs(counted - killed) <= 1, [killed, counted])


def camp_part(ctx) -> None:
    before = progress(ctx)
    ctx.actions.spawn_bandit_camp()
    ctx.actions.kill_units(side="bandit", count=5)
    import time
    time.sleep(8)
    gained = progress(ctx) - before
    ctx.metric("camp_kills_counted", gained)
    ctx.log.info(f"SPIKE bandit camp kills counted: {gained}")


def hold_part(ctx) -> None:
    ctx.mod.command(PREFIX + "liege_contracts_test_progress", index=1, value=999)
    ctx.mod.command(PREFIX + "liege_contract_complete")
    ctx.mod.command(PREFIX + "bandits_set_order", value=80)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="keep_the_peace.clear_the_roads.feed_the_city")
    ctx.mod.command(PREFIX + "liege_contract_pick", id="keep_the_peace")
    try:
        ctx.time.run_game_days(4, speed=3)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"days failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(4, speed=3)
    ctx.run_until(lambda: progress(ctx) >= 3, 30, what="the order days count", poll_s=1.0)
    counted = progress(ctx)
    ctx.metric("hold_days_counted", counted)
    ctx.check("P3 about 4 days count while the order is at least 60", 3 <= counted <= 6, counted)


def deadline_part(ctx) -> None:
    """The active contract (keep_the_peace, 4 of 90 days) fails when winter begins; the influence is 0, so the floor holds."""
    ctx.check("P4 a contract is active before winter", contracts(ctx).get("active") is not None, contracts(ctx))
    ctx.actions.set_season("winter")
    ctx.run_until(lambda: contracts(ctx).get("active") is None, 30, what="the winter deadline", poll_s=1.0)
    state = contracts(ctx)
    ctx.metric("winter_value", state["season"])
    ctx.check("P5 the contract failed at the start of winter", state["failed"] == 1 and state["done"] == 1, state)
    ctx.check("P6 the influence did not go below 0", state["influence"] >= 0, state["influence"])


def run(ctx) -> dict:
    kill_part(ctx)
    camp_part(ctx)
    hold_part(ctx)
    deadline_part(ctx)
    return ctx.result()
