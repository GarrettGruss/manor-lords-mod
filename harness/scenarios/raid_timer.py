"""Set the raid timer to 2, run game days, and check that a raid of 18 units spawns on time (spec 10, spike S1)."""

from runlib.units import SQUAD_UNITS, side_count

NAME = "raid-timer"
DESCRIPTION = "Write daysUntilNextRaid=2. The timer falls by 1 a day. A squad of 18 bandit units spawns on the day it reaches 0."
# T1 is only partly proven (no announcement in the base game), so it is not listed here: see criteria.json spike_note.
COVERS = []
LIMIT_S = 150
TIMER_DAYS = 2
MAX_DAYS = 5
SPEED = 3
# The game sets a new timer after a raid. Two values were seen: 208 and 353.
NEW_TIMER_RANGE = (30, 800)


def run(ctx) -> dict:
    expect, bridge = ctx.expect, ctx.bridge
    calendar = bridge.calendar_path()
    before = side_count(ctx.actions.units_census(), "bandit")
    ctx.actions.set_raid_timer(TIMER_DAYS, days_since=5)

    start_day = bridge.read_property(calendar, "daysTotal")
    bandits, days = before, 0
    while bandits == before and days < MAX_DAYS:
        ctx.time.run_game_days(1, speed=SPEED)
        days = bridge.read_property(calendar, "daysTotal") - start_day
        bandits = side_count(ctx.actions.units_census(), "bandit")

    expect.in_range("days until the raid appeared", days, TIMER_DAYS, TIMER_DAYS + 1)
    expect.equals("bandit units added", bandits - before, SQUAD_UNITS)
    expect.in_range("new timer", bridge.read_property(calendar, "daysUntilNextRaid"), *NEW_TIMER_RANGE)
    expect.equals("days since last raid", bridge.read_property(calendar, "daysSinceLastRaid"), 0)
    return ctx.result()
