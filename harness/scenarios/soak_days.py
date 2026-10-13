"""Run the settlement at 8x speed for about 10 minutes of wall time, close pop-ups, and check that the game stays alive (spec 10, Q1)."""

import os
import time

from runlib import soak
from runlib.actions import CHEAT_MANAGER
from runlib.game import find_game_processes
from runlib.timectl import CLOCK_SECONDS_PER_DAY, SPEED_FACTOR

NAME = "soak-days"
DESCRIPTION = "Soak: 8x speed for 600 wall seconds (about 120 game days). Pop-ups are closed and the village is fed. No crash, no stall, a steady clock rate, and a memory range."
COVERS = ["Q1"]
SPEED = 3  # 8 game seconds for each wall second, 5 wall seconds a day
SOAK_WALL_S = float(os.environ.get("HARNESS_SOAK_WALL_S", "600"))  # a longer soak is chosen by this variable
MAX_SOAK_WALL_S = 3900.0
if not 60 <= SOAK_WALL_S <= MAX_SOAK_WALL_S:
    raise ValueError(f"HARNESS_SOAK_WALL_S={SOAK_WALL_S:g} must be between 60 and {MAX_SOAK_WALL_S:g} seconds")
# Room for the speed change (about 10 s), the final pause (about 5 s), and slow bridge calls.
LIMIT_S = SOAK_WALL_S + 300
LONG_REASON = (f"A soak needs real time: {SOAK_WALL_S:g} wall seconds at 8x are about {SOAK_WALL_S * SPEED_FACTOR[SPEED] / CLOCK_SECONDS_PER_DAY:.0f} game days. "
               "730 days (2 game years) would take about 1 hour (HARNESS_SOAK_WALL_S=3650), but the unmanaged start village is defeated in its first winter, "
               "at about day 350 (soak-results.md). Longer than about 1700 s needs a managed settlement.")

POLL_S = 2.0
STALL_S = 20.0  # no clock progress for this long while the game should run: close pop-ups, then fail
# Measured at 8x on the base fixture: 7.8 game seconds a wall second. The range allows for a slow machine.
RUNNING_RATE_RANGE = (6.0, 9.0)
# Share of the nominal days that must pass. Pop-ups and slow polls lower it.
DAYS_SHARE_RANGE = (0.6, 1.1)
# The start village starves and is defeated at about day 137 (spike S8). Fish is added to the stock of the player region.
FEED_EVERY_DAYS = 10
FEED_ITEM_ID = 30  # Fish (verified with GiveItemByID)
FEED_AMOUNT = 100
# The unmanaged start village is defeated by winter at about day 350 (its Approval falls to 0). This option writes the Approval every
# poll so that a 730 day soak can finish. It tests the game process and the clock, not the economy.
KEEP_APPROVAL = os.environ.get("HARNESS_SOAK_KEEP_APPROVAL") == "1"
KEEP_APPROVAL_VALUE = 100
MAX_MEMORY_MB = 8192
MAX_MEMORY_GROWTH_MB = 2048


def run(ctx) -> dict:
    expect, bridge = ctx.expect, ctx.bridge
    engine = bridge.engine_path()
    calendar = bridge.calendar_path(engine)
    games = find_game_processes
    sampler = soak.Sampler(time.monotonic, lambda: bridge.read_clock_value(engine),
                           lambda: bridge.read_property(calendar, "daysTotal"), lambda: soak.process_memory_mb(games()))
    first = sampler()
    game_instance = "first:BP_MLGameInstance_C"

    def feed() -> None:
        bridge.call_function(CHEAT_MANAGER, "GiveItemByID", [FEED_ITEM_ID, FEED_AMOUNT])

    feeder = soak.Feeder(FEED_EVERY_DAYS, feed, first.days_total)

    def on_poll() -> None:
        ctx.popups()
        sample = sampler()
        soak.check_game_over(bridge.read_property(game_instance, "currentGameVictoryStatus"), sample.days_total)
        if KEEP_APPROVAL:
            ctx.actions.set_region_value("Approval", KEEP_APPROVAL_VALUE)
        if feeder(sample.days_total):
            ctx.log.info(f"fed {FEED_AMOUNT} of item {FEED_ITEM_ID} at daysTotal {sample.days_total}")
    ctx.time.set_speed(SPEED)
    started = time.monotonic()
    # The predicate is the wall budget. The popup guard runs at every poll, so a pop-up holds the game for about one poll.
    ctx.run_until(lambda: time.monotonic() - started >= SOAK_WALL_S, SOAK_WALL_S + 120, what=f"{SOAK_WALL_S:g} wall seconds of soak",
                  poll_s=POLL_S, stall_s=STALL_S, on_stall=ctx.popups, on_poll=on_poll)
    ctx.time.pause()
    last = sampler()

    ctx.ensure_alive("soak end")  # a crash is a crash verdict, not a failed assert
    expect.equals("game process alive at the end", bool(games()), True)
    days = last.days_total - first.days_total
    nominal_days = SOAK_WALL_S * SPEED_FACTOR[SPEED] / CLOCK_SECONDS_PER_DAY
    expect.in_range("game days run", days, nominal_days * DAYS_SHARE_RANGE[0], nominal_days * DAYS_SHARE_RANGE[1])
    rate = soak.running_rate(sampler.samples)
    expect.in_range("game clock rate while running (game s per wall s)", rate if rate is not None else -1, *RUNNING_RATE_RANGE)
    record_numbers(ctx, sampler.samples, first, last, days, feeder)
    check_memory(expect, first, last)
    return ctx.result()


def check_memory(expect, first, last) -> None:
    if first.rss_mb is None or last.rss_mb is None:
        expect.equals("process memory could be read", False, True)
        return
    expect.at_most("process memory at the end in MB", last.rss_mb, MAX_MEMORY_MB)
    expect.at_most("process memory growth in MB", last.rss_mb - first.rss_mb, MAX_MEMORY_GROWTH_MB)


def record_numbers(ctx, samples, first, last, days, feeder) -> None:
    numbers = {
        "days_run": days,
        "game_s": round(last.clock - first.clock, 1),
        "wall_s": last.wall_s,
        "overall_rate": soak.overall_rate(samples),
        "running_rate": soak.running_rate(samples),
        "popups_closed": len(ctx.popups.closed),
        "feedings": feeder.times,
        "stalled_polls": soak.stalled_gaps(samples),
        "longest_stall_s": soak.longest_stall_s(samples),
        "rss_start_mb": first.rss_mb,
        "rss_end_mb": last.rss_mb,
    }
    ctx.notes.append(f"soak {numbers}; pop-ups {ctx.popups.closed}")
    for name, value in numbers.items():
        if isinstance(value, (int, float)):
            ctx.metric(name, value)
