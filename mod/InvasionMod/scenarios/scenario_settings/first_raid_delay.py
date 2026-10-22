"""add-scenario-settings-menu: the setting "First Hussite raid" sets the first year of the season roll.

Runs on a fixture. The season changes are counted with the test command `invasion_yearly_advance_season` (a real calendar year takes
about 1800 wall seconds at speed 3), with a fixed roll value that passes every season of a raid year. It saves nothing.
"""

NAME = "scenario-settings-first-raid-delay"
DESCRIPTION = "After 2 years no raid is planned in years 1 and 2; the roll of year 3 plans one."
LIMIT_S = 200
PREFIX = "InvasionMod."
ROLL = 0.0  # under every chance


def advance(ctx) -> dict:
    return ctx.mod.command(PREFIX + "invasion_yearly_advance_season", roll=ROLL)


def yearly(ctx) -> dict:
    return ctx.mod.command(PREFIX + "invasion_yearly_state")


def run(ctx) -> dict:
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "scenario_settings_state")["decided"], 60, what="the settings decision")
    ctx.run_until(lambda: yearly(ctx)["season_no"] == 0, 30, what="the first season read")
    state = ctx.mod.command(PREFIX + "scenario_settings_set", first_raid_years=2)
    ctx.check("F0 the setting reads 2 years", state["first_raid_years"] == 2, state["first_raid_years"])
    start = yearly(ctx)
    ctx.check("F0 no raid is planned yet", start["raid_day"] == 0 and start["raids_spawned"] == 0, start)
    quiet = [advance(ctx) for _ in range(7)]
    ctx.check("F1 no raid is planned in years 1 and 2", not any(a["planned"] for a in quiet) and quiet[-1]["year"] == 2, quiet[-1])
    first = advance(ctx)
    ctx.check("F2 the roll of year 3 plans the raid", (first["year"], first["planned"]) == (3, True) and first["raid_day"] > 0, first)
    ctx.check("F2 the plan is 1 to 90 game days ahead", 1 <= first["raid_day"] - first["day"] <= 90, [first["raid_day"], first["day"]])
    return ctx.result()
