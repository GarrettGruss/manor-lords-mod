"""M04 iteration 02, B1 to B3 and B7: the conversion roll happens once per season change.

The scenario jumps the calendar with set_season (spring, summer, autumn, winter) and counts the rolls.
The dice are real. Public Order stays near 71 (chance 10 percent), so a conversion is possible but rare. The forced conversion is tested in bandits-convert-families.
It saves nothing.
"""

from runlib.units import side_count

NAME = "bandits-season-tick"
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Several single game-day steps and 10 more game days at speed 3 (about 13 s per day) plus the start."
SQUAD_UNITS = 18


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


SEASONS = ["winter", "spring", "summer", "autumn"]


def next_season(current: int) -> str:
    return SEASONS[(current + 1) % 4]


def step_into(ctx, before: dict) -> dict:
    """Jump to the next season and wait until the mod has rolled for it. Returns the new state."""
    want = before["rolls"] + 1
    ctx.actions.set_season(next_season(before["last_season"]))
    ctx.run_until(lambda: state(ctx)["rolls"] >= want, 30, what="the season roll")
    return state(ctx)


def run(ctx) -> dict:
    ctx.run_until(lambda: state(ctx)["last_season"] >= 0, 30, what="the saved season")
    start = state(ctx)
    ctx.check("B3 the mod knows the season and rolled nothing", start["last_season"] == start["season"] and start["rolls"] == 0, start)

    ctx.time.run_game_days(3, speed=SPEED)
    same = state(ctx)
    ctx.check("B2 no roll while the season stays (3 game days)", same["rolls"] == 0 and same["last_season"] == start["last_season"], same)

    first = step_into(ctx, same)
    ctx.check("B1 one roll for the first season change", first["rolls"] == 1, first)
    second = step_into(ctx, first)
    ctx.check("B1 one more roll for the second change", second["rolls"] == 2, second)
    ctx.check("B1 the saved season follows the calendar", second["last_season"] == second["season"], second)
    ctx.time.run_game_days(1, speed=SPEED)
    later = state(ctx)
    ctx.check("B2 still two rolls a game day later", later["rolls"] == 2, later)

    # The game moves approval back within days, so Public Order stays near 71 and the dice are real.
    units_before = side_count(ctx.actions.units_census(), "bandit")
    third = step_into(ctx, later)
    ctx.check("B1 one roll for the third change", third["rolls"] == 3, third)
    last = third["ticks"][-1]
    want_chance = 0.5 if last["order"] < 25 else 0.25 if last["order"] < 50 else 0.1 if last["order"] < 75 else 0
    ctx.check("the last roll used the chance of its Public Order band", last["chance"] == want_chance, last)
    ctx.check("the ticks add up to the converted families", sum(tick["converted"] for tick in third["ticks"]) == third["converted_families"], third)
    if last["converted"]:
        ctx.run_until(lambda: side_count(ctx.actions.units_census(), "bandit") > units_before, 20, what="the bandit squad")
        gained = side_count(ctx.actions.units_census(), "bandit") - units_before
        ctx.check("B5 a conversion of 2 families brings one squad of 18 bandits", last["converted"] == 2 and gained == SQUAD_UNITS, [last["converted"], gained])

    ctx.time.run_game_days(10, speed=SPEED)
    final = state(ctx)
    ctx.check("B7 the game runs 10 days after the season ticks", final["day"] >= third["day"] + 10, [third["day"], final["day"]])
    ctx.metric("rolls", final["rolls"])
    ctx.metric("converted_families", final["converted_families"])
    return ctx.result()
