"""Loot drops where a looter dies and is recovered, on a stand-in ledger (spec 10, spike R3, criterion R3)."""

from runlib.commands import CommandRefused
from runlib.units import loot_total

NAME = "loot-drop-recovery"
DESCRIPTION = "Kill looters. A ledger pile appears at each death place with the loot. Recovering a pile adds its goods to the stock."
COVERS = ["R3"]  # the base game has no ground loot (spike R3): the pile is a stand-in ledger. See criteria.json spike_note
LIMIT_S = 120

CARRIERS = 3
AMOUNT = 7
PLANKS = 17


def stock_of_planks(ctx) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [PLANKS, False, False])


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.spawn_raid(squads=1)
    ctx.actions.set_unit_loot("bandit", CARRIERS, AMOUNT)
    expect.equals("looters carry the loot", loot_total(ctx.actions.units_census()), CARRIERS * AMOUNT)
    expect.equals("no piles before", ctx.actions.loot_piles(), [])

    record = ctx.actions.drop_loot(CARRIERS, PLANKS)
    piles = record["answer"]["piles"]
    expect.equals("one pile for each dead looter", len(piles), CARRIERS)
    expect.equals("the ledger holds the piles", ctx.actions.loot_piles(), piles)
    expect.equals("each pile holds the loot of its looter", sorted(pile["amount"] for pile in piles), [AMOUNT] * CARRIERS)
    expect.equals("each pile has a place", all(pile["x"] != 0 or pile["y"] != 0 for pile in piles), True)
    expect.equals("the looters carry nothing now", loot_total(ctx.actions.units_census()), 0)

    stock_before = stock_of_planks(ctx)
    ctx.actions.recover_loot(piles[0]["id"])
    expect.equals("one recovery adds the pile", stock_of_planks(ctx) - stock_before, AMOUNT)
    expect.equals("the pile is gone", len(ctx.actions.loot_piles()), CARRIERS - 1)
    for pile in piles[1:]:
        ctx.actions.recover_loot(pile["id"])
    expect.equals("all recovered: the stock grew by the whole loot", stock_of_planks(ctx) - stock_before, CARRIERS * AMOUNT)
    expect.equals("the ledger is empty", ctx.actions.loot_piles(), [])
    try:
        ctx.commands.send("recover_loot", pile=piles[0]["id"])
        expect.record("a pile cannot be recovered twice", False, "accepted", "refused")
    except CommandRefused as error:
        expect.record("a pile cannot be recovered twice", True, error.reason[:50], "refused")
    return ctx.result()
