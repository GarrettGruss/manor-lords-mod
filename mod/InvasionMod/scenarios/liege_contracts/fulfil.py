"""update-liege-contracts-tiers: fulfil contracts in the real game (spike: regional wealth write, season start days).

Needs the pak and the default fixture (a built manor): `run.py --scenario liege-contracts-fulfil --pak InvasionMod`. It saves nothing.
- Fulfils a Small contract that pays regional wealth (spike task 1.1): the wealth of the player region must rise by the reward and
  still hold after one game day.
- Fulfils a Medium contract (silver) and a Large contract (tech point): goods leave the stores, rewards arrive.
- Checks that the config season start days match the game calendar (notes/season-days.md).
"""

import time

from runlib.modstate import ModCommandError

NAME = "liege-contracts-fulfil"
DESCRIPTION = "Fulfil a regional wealth, a silver and a tech point contract; the wealth holds after a day; the season start days match the calendar."
LIMIT_S = 300
PREFIX = "InvasionMod."
BERRIES, CUT_STONE, HELMETS = 171, 283, 273
OFFER = "s-171-70-r-0-60-0.s-17-50-g-146-30-0.s-145-30-g-17-25-0.m-283-30-s-0-200-0.m-35-24-w-177-15-0.m-6-15-g-35-20-0.l-273-9-t-0-1-0.l-293-5-i-0-1000-0.l-320-18-t-0-1-0"


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def stock(ctx, good: int) -> int:
    return int(ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False]))


def wealth(ctx) -> int:
    return int(ctx.bridge.read_property(ctx.bridge.player_region_path(), "regionalWealth"))


def run(ctx) -> dict:
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=OFFER)
    ctx.check("F0 a manor is built", contracts(ctx)["manor"] is True, contracts(ctx))
    ctx.actions.give_item(BERRIES, 70)
    ctx.actions.give_item(CUT_STONE, 30)
    ctx.actions.give_item(HELMETS, 12)  # the stock number can count a unit that is not in a store yet (run 20261030-183513-6d47: 8 of 9 found)

    berries, before = stock(ctx, BERRIES), wealth(ctx)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="small-1")
    after = wealth(ctx)
    ctx.metric("wealth_before", before)
    ctx.metric("wealth_after", after)
    ctx.check("F1 70 berries left the stores", berries - stock(ctx, BERRIES) == 70, [berries, stock(ctx, BERRIES)])
    ctx.check("F2 the regional wealth rose by 60", after - before == 60, [before, after])
    ctx.check("F3 no reward failed", contracts(ctx)["failed_rewards"] == 0, contracts(ctx))
    ctx.time.run_game_days(1)
    held = wealth(ctx)
    ctx.metric("wealth_after_a_day", held)
    ctx.check("F4 the wealth holds after one game day (the game may change it a little)", held >= after - 5, [after, held])

    silver = int(ctx.mod.command(PREFIX + "liege_state")["silver"])
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="medium-1")
    ctx.check("F5 the silver rose by 200", int(ctx.mod.command(PREFIX + "liege_state")["silver"]) - silver == 200)
    picks = ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    ctx.check("F6 the tech point reward adds one pick", ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] - picks == 1)
    state = contracts(ctx)
    ctx.check("F7 three contracts are done, one in each tier", state["done"] == 3 and all(row["used"] == 1 for row in state["tiers"].values()), state["tiers"])
    refused = False
    try:
        ctx.mod.command(PREFIX + "liege_contract_fulfil", id="small-2")
    except ModCommandError:
        refused = True
    ctx.check("F8 a second Small contract is refused by the tier limit", refused)

    # Season start days: set_day takes the day of the year.
    for day, season in ((334, 3), (335, 0), (59, 0), (60, 1)):
        ctx.actions.set_day(day)
        time.sleep(3)
        seen = contracts(ctx)["season"]
        ctx.log.info(f"SEASON day={day} season={seen}")
        ctx.check(f"F9 day {day} is season {season}", seen == season, seen)
    return ctx.result()
