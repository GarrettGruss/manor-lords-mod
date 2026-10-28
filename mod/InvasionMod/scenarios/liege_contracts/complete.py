"""update-liege-tribute-to-contracts: complete a goods contract in the real game (spike: the goods leave the stores).

The contract timber_for_the_walls wants 60 wood. The scenario gives 70 wood, picks, completes and checks the stock of the region
(the goods are taken from a store), the silver and the influence. It saves nothing. Run with the default fixture.
"""

from runlib.modstate import ModCommandError

NAME = "liege-contracts-complete"
DESCRIPTION = "Pick the wood contract, give 70 wood, complete it: 60 wood leave the stores, silver +100, influence +15, the contract is closed."
LIMIT_S = 300
PREFIX = "InvasionMod."
WOOD = 16
IDS = "timber_for_the_walls.clear_the_roads.keep_the_peace"


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def stock(ctx) -> int:
    return int(ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [WOOD, False, False]))


def run(ctx) -> dict:
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=IDS)
    ctx.mod.command(PREFIX + "liege_contract_pick", id="timber_for_the_walls")
    start = stock(ctx)
    ctx.actions.give_item(WOOD, 70)
    have = stock(ctx)
    ctx.metric("stock_before", have)
    ctx.check("W1 the stock rose by 70", have - start == 70, [start, have])
    ctx.run_until(lambda: contracts(ctx)["active"]["complete"], 20, what="the progress reads the stock", poll_s=1.0)
    ctx.check("W2 the progress counts the wood", contracts(ctx)["active"]["objectives"][0]["progress"] >= 60, contracts(ctx)["active"])

    before = ctx.mod.command(PREFIX + "liege_state")
    ctx.mod.command(PREFIX + "liege_contract_complete")
    after = ctx.mod.command(PREFIX + "liege_state")
    left = stock(ctx)
    ctx.metric("stock_after", left)
    ctx.check("W3 60 wood left the stores (getStockOfGood fell by 60)", have - left == 60, [have, left])
    ctx.check("W4 the silver rose by 100", int(after["silver"]) - int(before["silver"]) == 100, [before["silver"], after["silver"]])
    ctx.check("W5 the influence rose by 15", abs(after["influence"] - before["influence"] - 15) < 0.01, [before["influence"], after["influence"]])
    state = contracts(ctx)
    ctx.check("W6 the contract is closed and counted", state.get("active") is None and state["done"] == 1 and state["failed_rewards"] == 0, state)

    try:
        ctx.mod.command(PREFIX + "liege_contract_complete")
        again = False
    except ModCommandError:
        again = True
    ctx.check("W7 a second complete is refused", again)

    # The tech pick reward (change update-tech-tree-yearly-picks): keep_the_peace pays one pick to the tech tree.
    picks_before = ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids="keep_the_peace.clear_the_roads.feed_the_city")
    ctx.mod.command(PREFIX + "liege_contract_pick", id="keep_the_peace")
    ctx.mod.command(PREFIX + "liege_contracts_test_progress", index=1, value=90)
    ctx.mod.command(PREFIX + "liege_contract_complete")
    picks_after = ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    ctx.metric("tech_picks_gained", picks_after - picks_before)
    ctx.check("W8 the tech pick reward adds one pick to the tech tree", picks_after - picks_before == 1, [picks_before, picks_after])
    ctx.check("W9 no reward failed", contracts(ctx)["failed_rewards"] == 0, contracts(ctx))
    return ctx.result()
