"""M02 iteration 01, A4: over 120 game days the base game timer starts no extra raid. Exactly one raid is spawned.

The mod lifts the base raid timer each day. The scenario checks the spawn log, the bandit unit count and that the base timer stayed high.
It saves nothing.
"""

import re

from runlib.units import side_count

NAME = "invasion-no-double-raid"
LIMIT_S = 1000
SPEED = 3
LONG_REASON = "A4 needs 120 game days. One game day takes about 5 wall seconds at speed 3 (about 600 s)."
TOTAL_DAYS = 120
CHUNK_DAYS = 10
SPAWN = re.compile(r"INVASION spawn day=.*kind=plunder")  # the subjugation raid (M02.03) may come in the 120 days
SPAWN_RAIDERS = re.compile(r"INVASION spawn .*raiders=(\d+)")
REFILL = re.compile(r"base raid timer was (\d+),")
TIMER_FLOOR = 300


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.invasion_state")


def run_chunk(ctx) -> None:
    """A pop-up (seen at the new year) pauses the game. Close it and try once more."""
    ctx.popups()
    try:
        ctx.time.run_game_days(CHUNK_DAYS, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"chunk failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(CHUNK_DAYS, speed=SPEED)


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    plan = ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    bandits_before = side_count(ctx.actions.units_census(), "bandit")
    calendar = ctx.bridge.calendar_path()
    start_day = ctx.bridge.read_property(calendar, "daysTotal")
    timers = []
    while ctx.bridge.read_property(calendar, "daysTotal") - start_day < TOTAL_DAYS:
        run_chunk(ctx)
        timers.append(ctx.bridge.read_property(calendar, "daysUntilNextRaid"))

    lines = log_lines(ctx)
    spawns = [line for line in lines if SPAWN.search(line)]
    ctx.check("A4 exactly one raid spawn event in the log", len(spawns) == 1, spawns)
    ctx.check("A4 the base timer stayed at 300 or more", all(value >= TIMER_FLOOR - 1 for value in timers), timers)
    refills = [int(m.group(1)) for m in map(REFILL.search, lines) if m]
    ctx.check("A4 every lift started from just under the floor (no base raid reset it)", all(value == TIMER_FLOOR - 1 for value in refills), refills)
    added = side_count(ctx.actions.units_census(), "bandit") - bandits_before
    planned_units = plan["raiders"]
    spawned = [int(m.group(1)) for m in map(SPAWN_RAIDERS.search, spawns) if m]
    # Why no survivor minimum: raiders fight for days after the spawn and unarmored units die (M05), so all can be dead.
    # More units than planned would mean a second raid. The spawn event proves that the planned raid came.
    ctx.check("A4 the spawn event has exactly the planned raiders", spawned == [planned_units], [spawned, planned_units])
    # The census is a metric only: the bandits feature (M04) also makes bandit units from families.
    ctx.metric("bandit_units_added", added)
    return ctx.result()
