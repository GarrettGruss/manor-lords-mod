"""M06 iteration 01, A1 to A3 and A5: a forced sack takes a share of the town and the game goes on.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The scenario sacks the start village twice with the fatal switch off.
It saves nothing.
"""

import math

NAME = "sack-and-terms-sack"
DESCRIPTION = "A forced sack takes 20 to 50 percent of buildings, stock and families by difficulty; the village keeps people."
LIMIT_S = 240
SHARE = {1: 20.0, 2: 35.0, 3: 50.0}


def ceil_share(total: int, percent: float) -> int:
    return math.ceil(total * percent / 100 - 1e-9)


def stock_by_good(census: dict) -> dict:
    return {int(good): amount for good, amount in census["stock"]["by_good"].items()}


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    percent = SHARE[difficulty]
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.mod.command("InvasionMod.sack_set_fatal", enabled=False)
    before = ctx.actions.sack_census()
    ctx.check("start village has buildings and families", before["buildings"]["standing"] >= 3 and before["people"]["families"] >= 2, before["buildings"])

    result = ctx.mod.command("InvasionMod.sack_now", difficulty=difficulty)
    after = ctx.actions.sack_census()
    ctx.check("A1 the share is linear in the difficulty", result["percent"] == percent, result["percent"])
    expected_buildings = ceil_share(before["buildings"]["standing"], percent)
    lost_buildings = before["buildings"]["standing"] - after["buildings"]["standing"]
    ctx.check("A2 standing buildings fall by the rounded-up share (+/- 1)", abs(lost_buildings - expected_buildings) <= 1, [lost_buildings, expected_buildings])
    families_lost = before["people"]["families"] - after["people"]["families"]
    expected_families = min(ceil_share(before["people"]["families"], percent), before["people"]["families"] - 1)
    ctx.check("A2 families fall by the rounded-up share", families_lost == expected_families, [families_lost, expected_families])
    goods_before, goods_after = stock_by_good(before), stock_by_good(after)
    for good, held in goods_before.items():
        want = ceil_share(held, percent)
        took = held - goods_after.get(good, 0)
        ctx.check(f"A2 good {good} falls by the rounded-up share (+/- 1)", abs(took - want) <= 1, [took, want])
    ctx.check("A3 the village still has people", after["people"]["population"] > 0, after["people"])

    ctx.mod.command("InvasionMod.sack_now", difficulty=difficulty)
    second = ctx.mod.command("InvasionMod.sack_state")
    final = ctx.actions.sack_census()
    last = second["history"][-1]
    ctx.check("A5 the second sack in the window reaches the limit", last["limit_reached"] is True and last["window_count"] == 2, last)
    ctx.check("A5 with the fatal switch off the village keeps people", last["fatal"] is False and final["people"]["population"] > 0, final["people"])
    ctx.check("A6 two sacks are counted", second["sack_count"] == 2, second["sack_count"])
    ctx.metric("buildings_lost_first", lost_buildings)
    ctx.metric("families_lost_first", families_lost)
    ctx.metric("population_after_two", final["people"]["population"])
    return ctx.result()
