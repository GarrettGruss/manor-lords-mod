"""Stand-in mod: a raid is announced N days ahead and arrives on time, and the announced type matches the units (a toy model)."""

from raidstandin.client import DOMINANT_UNIT, RaidMod, distinct_units, dominant_unit

NAME = "raid-timeline"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Set the raid timer with a command, step the toy clock to the announcement and to the arrival, compare the announced type "
               "with the units, then wait real game days to prove that the toy clock follows the game clock. "
               "Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["T1", "T3"]

TIER = 3
ANNOUNCE_DAYS = 3
TIMER_DAYS = 10
CLOCK_ANNOUNCE_DAYS = 2
CLOCK_TIMER_DAYS = 4
CLOCK_LEGS = 2  # two legs of CLOCK_ANNOUNCE_DAYS game days: after the first leg the raid is announced, after the second it has arrived
SPEED = 3
ARRIVAL_TOLERANCE_DAYS = 1


def check_announcement(ctx, mod, faction):
    expect = ctx.expect
    mod.start(tier=TIER, announce_days=ANNOUNCE_DAYS, seed=5)
    mod("set_day", day=100)
    planned = mod("set_timer", days=TIMER_DAYS, faction=faction)
    arrival = planned["planned_day"]
    mod("advance_days", days=TIMER_DAYS - ANNOUNCE_DAYS - 1)
    expect.equals(f"T1 {faction}: nothing is announced before the lead time", mod("next_raid")["state"], "scheduled")
    mod("advance_days", days=1)
    announced = mod("next_raid")
    expect.equals(f"T1 {faction}: the raid is announced", announced["state"], "announced")
    expect.equals(f"T1 {faction}: it is announced N days before arrival", arrival - announced["announced_day"], ANNOUNCE_DAYS)
    expect.equals(f"T1 {faction}: the metric raid_announced is true", mod.metric("raid_announced"), True)
    mod("advance_days", days=ANNOUNCE_DAYS)
    return announced, mod("current_raid")


def check_arrival(ctx, announced, active, faction):
    expect = ctx.expect
    expect.equals(f"T1 {faction}: the raid is active after the lead time", active["state"], "active")
    expect.in_range(f"T1 {faction}: it arrives on the announced day", active["arrival_day"] - announced["planned_day"],
                    -ARRIVAL_TOLERANCE_DAYS, ARRIVAL_TOLERANCE_DAYS)


def check_type_matches_units(ctx, announced, active, faction):
    expect = ctx.expect
    composition = active["composition"]
    dominant = dominant_unit(composition)
    expect.equals(f"T3 {faction}: the announced kind is the expected one", announced["kind"], DOMINANT_UNIT[faction])
    expect.equals(f"T3 {faction}: the most common unit type is the announced kind", dominant, announced["kind"])
    expect.equals(f"T3 {faction}: the units add up to the announced size", sum(composition.values()), announced["size"])
    expect.equals(f"T3 {faction}: the unit types match the tier variety", distinct_units(composition), TIER)


def check_clock_link(ctx, mod):
    """Wait real game days. The toy clock must move with the game clock, and the director must run on it."""
    expect = ctx.expect
    mod.start(tier=TIER, announce_days=CLOCK_ANNOUNCE_DAYS, seed=6)
    arrived_before = mod.metric("raids_arrived")
    day_before = mod("clock")["day"]
    mod("set_timer", days=CLOCK_TIMER_DAYS, faction="norse")
    first = ctx.time.run_game_days(CLOCK_ANNOUNCE_DAYS, speed=SPEED)
    expect.equals("T1 clock: the raid is announced after the first game days", mod.metric("raid_announced") or mod.metric("raid_active"), True)
    second = ctx.time.run_game_days(CLOCK_ANNOUNCE_DAYS, speed=SPEED)
    passed = (first["days_end"] - first["days_start"]) + (second["days_end"] - second["days_start"])
    expect.at_least("T1 clock: game days passed", passed, CLOCK_TIMER_DAYS)
    expect.equals("T1 clock: the toy clock moved by the game days", mod("clock")["day"] - day_before, passed)
    expect.equals("T1 clock: the raid arrived", mod.metric("raids_arrived") - arrived_before, 1)


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    for faction in ("cuman", "norse"):
        announced, active = check_announcement(ctx, mod, faction)
        check_arrival(ctx, announced, active, faction)
        check_type_matches_units(ctx, announced, active, faction)
    check_clock_link(ctx, mod)
    return ctx.result()
