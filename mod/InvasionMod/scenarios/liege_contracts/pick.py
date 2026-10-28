"""update-liege-tribute-to-contracts: an offer, a pick, the refusals and the removed tribute command in the real game.

It needs no pak (no window). It saves nothing. Run with --new-game.
"""

from runlib.modstate import ModCommandError

NAME = "liege-contracts-pick"
DESCRIPTION = "Offer three named contracts, pick one, check that the others are gone and that bad picks and the old tribute command are refused."
LIMIT_S = 240
PREFIX = "InvasionMod."
IDS = "timber_for_the_walls.clear_the_roads.keep_the_peace"


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def refused(ctx, command: str, **fields) -> bool:
    try:
        ctx.mod.command(PREFIX + command, **fields)
    except ModCommandError:
        return True
    return False


def run(ctx) -> dict:
    state = contracts(ctx)
    ctx.check("K1 the table holds at least 8 contracts", state["contract_count"] >= 8, state["contract_count"])
    ctx.check("K2 no offer and no active contract at the start", state["offer"] == [] and state.get("active") is None, state)
    ctx.check("K3 a pick with no offer is refused", refused(ctx, "liege_contract_pick", id="clear_the_roads"))

    offered = ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=IDS)
    ctx.check("K4 the offer holds the three named ids", offered["offer"] == IDS.split("."), offered["offer"])
    ctx.check("K5 a pick outside the offer is refused", refused(ctx, "liege_contract_pick", id="feed_the_city"))

    ctx.mod.command(PREFIX + "liege_contract_pick", id="clear_the_roads")
    state = contracts(ctx)
    ctx.check("K6 the picked contract is active and the others are gone", state["offer"] == [] and state["active"]["id"] == "clear_the_roads", state)
    ctx.check("K7 a second pick is refused", refused(ctx, "liege_contract_pick", id="keep_the_peace"))
    ctx.check("K8 an incomplete contract cannot be completed", refused(ctx, "liege_contract_complete"))
    ctx.check("K9 the old tribute command is unknown", refused(ctx, "liege_send_tribute", amount=100))
    ctx.check("K10 the state is unchanged after the refusals", contracts(ctx)["active"]["id"] == "clear_the_roads", contracts(ctx))
    ctx.metric("contract_count", state["contract_count"])
    return ctx.result()
