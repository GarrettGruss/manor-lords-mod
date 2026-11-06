"""update-liege-contracts-tier-goods: fulfil contracts in the real game (a goods contract of each kind and one Large cost).

Needs the pak and a fixture with a built manor and at least 4 families: `run.py --scenario liege-contracts-fulfil --fixture playtest-noai --pak InvasionMod --slot 1`.
It saves nothing. The environment variable HARNESS_LARGE picks the Large contract (the tier limit is 1 each year, so one run checks one):
- `loan` (default): the cost is one squad for 60 days, the reward is King's Favour +10. A squad is spawned first. The loan is made due at once
  (test command `liege_contracts_loans_due_now`; a real loan is 60 game days) and a new squad of the same template must appear.
- `families`: the cost is 3 families for good, the reward is a law (unlocked by the contract).
- `tribute`: the cost needs a vassal; the test game has none, so the call must be refused and nothing may change.
It also checks that the config season start days match the game calendar (notes/season-days.md of update-liege-contracts-tiers).
"""

import os
import time

from runlib.modstate import ModCommandError

NAME = "liege-contracts-fulfil"
DESCRIPTION = "Fulfil a Small, a Medium and a Large contract (squad loan, families or tribute); King's Favour, a law and the squad return are checked."
LIMIT_S = 300
PREFIX = "InvasionMod."
PLANKS, CLAY, SAUSAGES, TOOLS = 17, 146, 320, 6
LARGE = os.environ.get("HARNESS_LARGE", "loan")
# The saved text form: <tier>-<good or cost code>-<amount>-<reward>-<reward good>-<reward amount>-<done>. Cost codes: loan 1, families 2, tribute 3.
LARGE_CONTRACTS = {
    "loan": "l-1-1-k-0-10-0",
    "families": "l-2-3-l-0-1-0",
    "tribute": "l-3-3-p-0-5-0",
}
OFFER = ".".join(["s-17-50-g-146-30-0", "m-320-24-g-6-15-0", LARGE_CONTRACTS[LARGE]])
SPEAR_MILITIA = "spearMilitia"


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def stock(ctx, good: int) -> int:
    return int(ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False]))


def kings_favour(ctx) -> int:
    return int(ctx.bridge.read_property(ctx.bridge.player_path(), "kingsFavour"))


def families(ctx) -> int:
    return int(ctx.actions.sack_census()["people"]["families"])


def player_men(ctx) -> int:
    """Squads in the commandedSquads list of the player pawn (the mod and the harness have separate Lua states, so the harness
    registry does not know the squad that the mod spawns)."""
    return len(ctx.bridge.read_property(ctx.bridge.player_path(), "commandedSquads"))


def goods_contracts(ctx) -> None:
    ctx.actions.give_item(PLANKS, 55)
    ctx.actions.give_item(SAUSAGES, 30)
    planks, clay, sausages, tools = stock(ctx, PLANKS), stock(ctx, CLAY), stock(ctx, SAUSAGES), stock(ctx, TOOLS)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="small-1")
    ctx.check("F1 50 planks left the stores and 30 clay arrived", (planks - stock(ctx, PLANKS), stock(ctx, CLAY) - clay) == (50, 30),
              [planks, stock(ctx, PLANKS), clay, stock(ctx, CLAY)])
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="medium-1")
    ctx.check("F2 24 sausages left the stores and 15 tools arrived", (sausages - stock(ctx, SAUSAGES), stock(ctx, TOOLS) - tools) == (24, 15),
              [sausages, stock(ctx, SAUSAGES), tools, stock(ctx, TOOLS)])
    ctx.check("F3 no reward failed", contracts(ctx)["failed_rewards"] == 0, contracts(ctx))


def loan_contract(ctx) -> None:
    spawned = ctx.actions.spawn_units("player", SPEAR_MILITIA, 1)
    ctx.check("L0 a squad was spawned for the loan", bool(((spawned or {}).get("answer") or {}).get("squads")), spawned)
    ctx.time.run_game_seconds(3, speed=1)
    men, favour = player_men(ctx), kings_favour(ctx)
    ctx.metric("squads_before_loan", men)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    ctx.time.run_game_seconds(5, speed=1)
    state = contracts(ctx)
    ctx.metric("kings_favour_before", favour)
    ctx.metric("kings_favour_after", kings_favour(ctx))
    ctx.check("L1 King's Favour rose by 10 or more", kings_favour(ctx) - favour >= 10, [favour, kings_favour(ctx)])
    ctx.check("L2 the squad left the player (one squad less)", player_men(ctx) == men - 1, [men, player_men(ctx)])
    ctx.check("L3 one loan is written down", state["loans_started"] == 1 and state["loans_text"] != "", state["loans_text"])
    ctx.mod.command(PREFIX + "liege_contracts_loans_due_now")
    ctx.run_until(lambda: contracts(ctx)["loans_returned"] >= 1, 20, what="the loaned squad returns", poll_s=1)
    ctx.time.run_game_seconds(10, speed=1)
    back = player_men(ctx)
    ctx.metric("squads_after_return", back)
    ctx.check("L4 a squad is back (the squad count is the same as before the loan)", back == men, [men, back])
    ctx.check("L5 the loan record is gone", contracts(ctx)["loans_text"] == "", contracts(ctx)["loans_text"])
    ctx.screenshot("loan-returned")


def families_contract(ctx) -> None:
    before = families(ctx)
    ctx.metric("families_before", before)
    ctx.check("P0 the village has at least 4 families", before >= 4, before)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    ctx.time.run_game_seconds(3, speed=1)
    after = families(ctx)
    ctx.metric("families_after", after)
    ctx.check("P1 three families are gone", before - after == 3, [before, after])
    laws = ctx.mod.command(PREFIX + "tech_tree_state")["laws_unlocked_by_contract"]
    ctx.check("P2 one law was unlocked by the contract", len(laws) == 1, laws)
    ctx.check("P3 no reward failed", contracts(ctx)["failed_rewards"] == 0, contracts(ctx))


def tribute_contract(ctx) -> None:
    refused = ""
    try:
        ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    except ModCommandError as error:
        refused = str(error)
    ctx.check("T1 the call is refused: no vassal pays tribute", "no vassal pays tribute" in refused, refused)
    ctx.check("T2 nothing changed", contracts(ctx)["done"] == 0 and contracts(ctx)["relief_bonus_squads"] == 0, contracts(ctx))


def run(ctx) -> dict:
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=OFFER)
    ctx.check("F0 a manor is built", contracts(ctx)["manor"] is True, contracts(ctx))
    if LARGE == "tribute":
        tribute_contract(ctx)
    else:
        goods_contracts(ctx)
        {"loan": loan_contract, "families": families_contract}[LARGE](ctx)
    refused = False
    try:
        ctx.mod.command(PREFIX + "liege_contract_fulfil", id="small-2")
    except ModCommandError:
        refused = True
    ctx.check("F8 a second Small contract is refused", refused)

    # Season start days: set_day takes the day of the year.
    for day, season in ((334, 3), (335, 0), (59, 0), (60, 1)):
        ctx.actions.set_day(day)
        time.sleep(3)
        seen = contracts(ctx)["season"]
        ctx.log.info(f"SEASON day={day} season={seen}")
        ctx.check(f"F9 day {day} is season {season}", seen == season, seen)
    return ctx.result()
