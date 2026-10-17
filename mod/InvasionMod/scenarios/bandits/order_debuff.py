"""M04 iteration 01, A1 to A4: low approval lowers Public Order, and the game does not erase or stack it.

The game moves Approval by itself, so each check compares the order with the natural order and the approval read in the same state answer.
It saves nothing.
"""

import math

NAME = "bandits-order-debuff"
LIMIT_S = 400
SPEED = 3
LONG_REASON = "Several single game-day steps at speed 3 (about 10 s each) plus the start."


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def expected(natural: int, approval: int, difficulty: int) -> int:
    return max(0, natural - math.ceil((100 - approval) * difficulty))


def check_debuff(ctx, label: str, tolerance: int) -> dict:
    now = state(ctx)
    want = expected(now["natural_order"], now["approval"], now["difficulty"])
    ctx.check(f"{label}: order {now['order']} is natural {now['natural_order']} minus the debuff (want {want}, +-{tolerance})",
              abs(now["order"] - want) <= tolerance, now)
    return now


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.bandits_set_approval", value=65)
    ctx.time.run_game_days(2, speed=SPEED)
    first = check_debuff(ctx, "A1 approval about 65, difficulty 1", 5)
    ctx.check("A1 the debuff is in effect (order under natural)", first["order"] < first["natural_order"], first)

    ctx.mod.command("InvasionMod.bandits_set_approval", value=65)
    ctx.time.run_game_days(5, speed=SPEED)
    second = check_debuff(ctx, "A2 five days later, no stacking", 10)
    ctx.check("A2 order is not under 0", second["order"] >= 0, second)
    ctx.log.info(f"BANDITS overwrites seen by the mod: {second['overwrites']}")

    off = ctx.mod.command("InvasionMod.bandits_set_approval", value=100)
    ctx.check("A3 approval 100 gives the natural order back at once", off["order"] == off["natural_order"], off)

    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=2)
    ctx.mod.command("InvasionMod.bandits_set_approval", value=65)
    ctx.time.run_game_days(1, speed=SPEED)
    hard = check_debuff(ctx, "A4 difficulty 2", 10)
    ctx.check("A4 order is at least 0", hard["order"] >= 0, hard)
    ctx.metric("overwrites", second["overwrites"])
    ctx.metric("natural_order", hard["natural_order"])
    return ctx.result()
