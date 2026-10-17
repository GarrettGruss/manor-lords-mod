"""M03 iteration 01, A1 to A5 (and the numbers for A6): a raid under the native plunder AI on the base fixture.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1), INVASION_SIZE (small, medium or large, default small).
The raid is started at once with invasion_force_next. The scenario adds no steering. It saves nothing.
"""

import re
import time

from runlib.units import side_count

NAME = "raid-behavior-native-plunder"
LIMIT_S = 900
SPEED = 3
LONG_REASON = "A raid walks about 16 game days before it burns. The scenario runs up to 30 game days at speed 3 (about 150 to 300 s) plus the start."
MAX_DAYS = 30  # A1 says 20 days; raids of 2 squads arrived late in some runs (see the iteration file)
MULTIPLIERS = {"small": 1, "medium": 2, "large": 3}
LEAVE = re.compile(r"RAID_BEHAVIOR native leave line seen")


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    size = ctx.variant_option("INVASION_SIZE", "small")
    squads = MULTIPLIERS[size] * difficulty
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size=size)
    bandits_before = side_count(ctx.actions.units_census(), "bandit")
    population_before = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    raid = tracker(ctx)
    ctx.check("the tracker found all raiders", raid["initial"] == 18 * squads, raid["initial"])

    mismatches, samples, days = [], 0, 0
    while raid["state"] == "active" and days < MAX_DAYS:
        run_day(ctx)
        days += 1
        raid = tracker(ctx)
        census_living = side_count(ctx.actions.units_census(), "bandit") - bandits_before
        samples += 1
        if census_living != raid["living"]:
            # The tracker looks once a second. A unit can die in between, so look again after the tracker had time.
            time.sleep(2.0)
            raid = tracker(ctx)
            census_living = side_count(ctx.actions.units_census(), "bandit") - bandits_before
        if census_living != raid["living"]:
            mismatches.append([days, raid["living"], census_living])
        ctx.log.info(f"day {days}: {raid}")

    ctx.check("A1 the raid ended within the day limit (30; 20 for one squad)", raid["state"] != "active", [raid["state"], days])
    ctx.check("A1 the native leave line is in the log", any(LEAVE.search(line) for line in (ctx.run_dir / "mod.log").read_text(encoding="utf-8", errors="replace").splitlines()), raid["leaving"])
    ctx.check("A2 total looted goods are more than 0", raid["looted_total"] > 0, raid["looted_total"])
    ctx.check("A3 burned buildings are 0 to 10", 0 <= raid["burned"] <= 10, raid["burned"])
    population = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.check("A4 the village still has people", population is not None and population > 0, [population_before, population])
    ctx.check("A5 tracker living equals the game unit count at every sample", not mismatches, mismatches)
    ctx.metric("squads", squads)
    ctx.metric("looted_total", raid["looted_total"])
    ctx.metric("burned", raid["burned"])
    ctx.metric("deaths", raid["deaths"])
    ctx.metric("days", days)
    ctx.check("A1 a one-squad raid ended within 20 game days", squads > 1 or days <= 20, days)
    return ctx.result()
