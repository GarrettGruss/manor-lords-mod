"""update-liege-contracts-tier-goods: fulfil contracts in the real game (a goods contract of each kind and one Large cost).

Needs the pak and a fixture with a built manor and at least 4 families: `run.py --scenario liege-contracts-fulfil --fixture playtest-noai --pak InvasionMod --slot 1`.
It saves nothing. The environment variable HARNESS_LARGE picks the Large contract (the tier limit is 1 each year, so one run checks one):
- `loan` (default; fixture manor-bailey, which has a native retinue squad of 5 men): the cost is one retinue squad for 60 days, the reward is
  King's Favour +10. A militia squad is spawned first and must stay. The loan is made due at once (test command `liege_contracts_loans_due_now`;
  a real loan is 60 game days) and a new native squad of 5 men must appear, with the return banner.
- `retinue`: the cost is 3 families, the reward is a native retinue squad of 5 men (change add-contract-retinue-reward).
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
    "retinue": "l-2-3-r-0-1-0",
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


def squads(ctx) -> dict:
    """Living men of each commanded squad of the player, by id (spike probe mode rsquads: counts units, reads no Squad struct)."""
    answer = ctx.actions._command("loan_probe", mode="rsquads")  # noqa: SLF001
    return {row["id"]: row["men"] for row in answer["squads"]}


def silver(ctx) -> float:
    return float(ctx.actions._command("loan_probe", mode="rsquads")["silver"])  # noqa: SLF001


def log_text(ctx) -> str:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""


def loan_contract(ctx) -> None:
    """The loan takes the native retinue squad (5 men on the fixture manor-bailey), never the militia squad, and gives it back with a banner."""
    start = squads(ctx)
    ctx.check("L00 the fixture has a retinue squad of 5 men", 5 in start.values(), start)
    spawned = ctx.actions.spawn_units("player", SPEAR_MILITIA, 1)
    ctx.check("L0 a militia squad was spawned", bool(((spawned or {}).get("answer") or {}).get("squads")), spawned)
    ctx.time.run_game_seconds(3, speed=1)
    before = squads(ctx)
    militia = [squad for squad in before if squad not in start]
    retinue = [squad for squad, men in start.items() if men == 5]
    favour = kings_favour(ctx)
    ctx.metric("squads_before_loan", len(before))
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    ctx.time.run_game_seconds(5, speed=1)
    state, after = contracts(ctx), squads(ctx)
    ctx.metric("kings_favour_before", favour)
    ctx.metric("kings_favour_after", kings_favour(ctx))
    ctx.check("L1 King's Favour rose by 10 or more", kings_favour(ctx) - favour >= 10, [favour, kings_favour(ctx)])
    ctx.check("L2 the retinue squad left and the militia squad stayed", all(s not in after for s in retinue) and all(s in after for s in militia), [before, after])
    ctx.check("L3 one retinue loan is written down", state["loans_started"] == 1 and state["loans_text"].startswith("retinue-5-"), state["loans_text"])
    ctx.mod.command(PREFIX + "liege_contracts_loans_due_now")
    ctx.run_until(lambda: contracts(ctx)["loans_returned"] >= 1, 20, what="the loaned squad returns", poll_s=1)
    time.sleep(0.3)
    ctx.screenshot("loan-returned-banner")
    ctx.time.run_game_seconds(10, speed=1)
    back = squads(ctx)
    ctx.metric("squads_after_return", len(back))
    ctx.check("L4 a new native squad of 5 men is back and the militia squad is still there", len(back) == len(before) and [s for s, m in back.items() if s not in before and m == 5], [before, back])
    ctx.check("L5 the loan record is gone", contracts(ctx)["loans_text"] == "", contracts(ctx)["loans_text"])
    log = log_text(ctx)
    ctx.check("L6 the return banner ran (no banner failure in the log)", "loan ended" in log and "loan banner failed" not in log, log[-300:])


def retinue_contract(ctx) -> None:
    """Cost 3 families, reward: a native retinue squad of 5 men, paid by the mod (the silver is not charged)."""
    before_squads, before_silver = squads(ctx), silver(ctx)
    ctx.mod.command(PREFIX + "liege_contract_fulfil", id="large-1")
    ctx.time.run_game_seconds(5, speed=1)
    after = squads(ctx)
    new = {squad: men for squad, men in after.items() if squad not in before_squads}
    state = contracts(ctx)
    ctx.metric("squads_before", len(before_squads))
    ctx.metric("squads_after", len(after))
    ctx.check("R1 one new squad of 5 men", list(new.values()) == [5], [before_squads, after])
    ctx.check("R2 the reward did not fail and the count is 1", state["failed_rewards"] == 0 and state["retinue_squads"] == 1, state)
    ctx.check("R3 the new squad id is in the retinue ids", str(next(iter(new), None)) in state["retinue_ids"].split("."), state["retinue_ids"])
    ctx.check("R4 the silver did not change", abs(silver(ctx) - before_silver) < 1, [before_silver, silver(ctx)])
    ctx.screenshot("retinue-reward-paid")


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
        if LARGE not in ("loan", "retinue"):  # these runs use fixtures with a manor but no storehouse for the goods rewards
            goods_contracts(ctx)
        {"loan": loan_contract, "families": families_contract, "retinue": retinue_contract}[LARGE](ctx)
    if LARGE not in ("loan", "retinue"):
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
