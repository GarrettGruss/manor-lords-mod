"""M04 iteration 01, A5 to A8: low Public Order turns families into bandits through homeless_rebel.

Approval 0 gives Public Order 0 at difficulty 1, so the order is low without a game write. The dice are forced with bandits_tick_now.
It saves nothing.
"""

from runlib.units import side_count

NAME = "bandits-convert-families"
LIMIT_S = 500
SPEED = 3
LONG_REASON = "Ten game days at speed 3 after the conversion (about 60 s) plus the start."
SQUAD_UNITS = 18


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def bandits(ctx) -> int:
    return side_count(ctx.actions.units_census(), "bandit")


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.bandits_set_approval", value=100)
    high = state(ctx)
    before_units = bandits(ctx)
    after = ctx.mod.command("InvasionMod.bandits_tick_now", roll=0.0)
    ctx.check("A7 order is 80 or more", high["order"] >= 80, high["order"])
    ctx.check("A7 no family is removed above 75", after["converted_families"] == 0 and after["families"] == high["families"], after)
    ctx.check("A7 no bandit appears", bandits(ctx) == before_units, bandits(ctx))

    ctx.mod.command("InvasionMod.bandits_set_approval", value=0)
    low = state(ctx)
    ctx.check("order is under 25", low["order"] < 25, low["order"])
    lost = ctx.mod.command("InvasionMod.bandits_tick_now", roll=0.99)
    ctx.check("A6 a roll of 0.99 removes no family", lost["converted_families"] == 0 and lost["families"] == low["families"], lost)
    ctx.check("A6 no bandit appears", bandits(ctx) == before_units, bandits(ctx))

    won = ctx.mod.command("InvasionMod.bandits_tick_now", roll=0.0)
    ctx.run_until(lambda: bandits(ctx) > before_units, 20, what="the bandit squad")
    gained = bandits(ctx) - before_units
    ctx.check("A5 two families are removed", won["converted_families"] == 2 and won["families"] == low["families"] - 2, won)
    ctx.check("A5 one squad of 18 bandits appears", gained == SQUAD_UNITS, gained)

    ctx.time.run_game_days(10, speed=SPEED)
    final = state(ctx)
    ctx.check("A8 the game runs 10 days after the conversion", final["day"] >= won["day"] + 10, [won["day"], final["day"]])
    ctx.metric("families_before", low["families"])
    ctx.metric("families_after", final["families"])
    ctx.metric("bandit_units_gained", gained)
    return ctx.result()
