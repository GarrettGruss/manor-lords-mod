"""Bandits: the mod public order ticks every 30 game days (+10 manor, -5 for each homeless family) and the mod writes it to the game.

A forced tick checks the six telemetry fields. A 65 game day run checks the tick interval. It saves nothing.
Run on the default fixture or on `--fixture playtest-noai`.
"""

NAME = "bandits-order-tick"
LIMIT_S = 1500
SPEED = 3
LONG_REASON = "65 game days at speed 3 (about 13 s per game day) to count the natural ticks, plus the start."
TICK_FIELDS = ("day", "order_before", "manor_term", "homeless_count", "homeless_term", "order_after")


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def run(ctx) -> dict:
    start = state(ctx)
    ctx.check("the mod order starts at a value from 0 to 100", 0 <= start["mod_order"] <= 100, start)
    ctx.mod.command("InvasionMod.bandits_set_order", value=50)
    ctx.run_until(lambda: state(ctx)["game_order"] == 50, 30, what="the mod writing the game order")
    ctx.check("the game order is the mod order", state(ctx)["game_order"] == 50, state(ctx))

    forced = ctx.mod.command("InvasionMod.bandits_tick_now")
    tick = forced["last_tick"]
    ctx.check("the tick record has the six fields", all(field in tick for field in TICK_FIELDS), tick)
    ctx.check("the manor term is 10", tick["manor_term"] == 10, tick)
    ctx.check("the homeless term is 5 for each homeless family", tick["homeless_term"] == 5 * tick["homeless_count"], tick)
    want = max(0, min(100, 50 + tick["manor_term"] - tick["homeless_term"]))
    ctx.check("the order after is order before plus manor term minus homeless term", tick["order_after"] == want, [tick, want])
    ctx.run_until(lambda: state(ctx)["game_order"] == want, 30, what="the new order in the game")
    ctx.check("the game order follows the tick", state(ctx)["game_order"] == want, state(ctx))

    ticks_before = state(ctx)["ticks"]
    ctx.time.run_game_days(65, speed=SPEED)
    final = state(ctx)
    ran = final["ticks"] - ticks_before
    ctx.check("between 2 and 3 natural ticks ran in 65 game days", 2 <= ran <= 3, [ticks_before, final["ticks"]])
    ctx.metric("natural_ticks", ran)
    ctx.metric("mod_order_end", final["mod_order"])
    return ctx.result()
