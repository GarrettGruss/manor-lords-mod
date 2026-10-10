"""Measure the game clock rate at 1x with about 300 units, after a large raid (spec 10, spike S10)."""

from runlib.units import side_count

NAME = "raid-load"
DESCRIPTION = "Spawn 8 raider squads (144 units). The clock rate at 1x stays near 1, and the bridge and the census still answer."
COVERS = ["Q2"]
LIMIT_S = 150
SQUADS = 8
WINDOW_WALL_S = 6.0
# Measured with 220 to 661 units: 1.02 to 1.03 at 1x. The range allows for a slow machine.
RATE_RANGE = (0.8, 1.3)
MIN_UNITS = 300


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.spawn_raid(squads=SQUADS)
    census = ctx.actions.units_census()
    expect.at_least("units in the game", census["units"], MIN_UNITS)
    expect.at_least("bandit units", side_count(census, "bandit"), SQUADS * 18)

    ctx.time.set_speed(1)
    window = ctx.bridge.measure_clock(WINDOW_WALL_S)
    rate = window["change"] / WINDOW_WALL_S
    ctx.time.pause()
    expect.in_range("clock rate at 1x (game s per wall s)", round(rate, 2), *RATE_RANGE)
    expect.at_most("census cost in ms", ctx.actions.units_census()["ms"], 100)
    return ctx.result()
