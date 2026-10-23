"""M02 iteration 02 and update-raid-banners, C1 to C3: the great raid clock ends at the start of game year 10 and counts down.

The clock banners (years 7, 8 and 9) come from the fake game test (a real run does not reach year 7). It saves nothing.
"""

import re

NAME = "invasion-great-raid-clock"
LIMIT_S = 300
SPEED = 3
CLOCK_BANNER = re.compile(r"INVASION clock banner year=(\d+) years_left=(\d+) shown=(\w+)")
CLOCK_START = re.compile(r"INVASION clock start day=(\d+) end_day=(\d+) start_year=(\d+) year=(\d+)")
WAIT_DAYS = 3
SEASONS_TO_YEAR_10 = 36
SEASON_ESTIMATE_DAYS = 92


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def clock(ctx) -> dict:
    return ctx.mod.command("InvasionMod.invasion_clock_state")


def run(ctx) -> dict:
    ctx.run_until(lambda: clock(ctx)["great_raid_day"] > 0, 30, what="the great raid clock")
    first = clock(ctx)
    starts = [tuple(int(v) for v in m.groups()) for m in map(CLOCK_START.search, log_lines(ctx)) if m]
    ctx.check("C1 one clock start in the log", len(starts) == 1, starts)
    day, end_day, start_year, year = starts[0] if starts else (0, 0, 0, 0)
    ctx.check("C1 the start year is 10", start_year == 10, start_year)
    seasons_left = SEASONS_TO_YEAR_10 - 4 * (year - 1)
    ctx.check("C1 the end day is the estimate to the first day of year 10", end_day - day <= seasons_left * SEASON_ESTIMATE_DAYS, [day, end_day, year])

    ctx.time.run_game_days(WAIT_DAYS, speed=SPEED)
    second = clock(ctx)
    passed = second["day"] - first["day"]
    ctx.check("C3 the end day does not change", second["great_raid_day"] == first["great_raid_day"], [first["great_raid_day"], second["great_raid_day"]])
    ctx.check("C3 days left fell by the days that passed", first["days_left"] - second["days_left"] == passed, [first["days_left"], second["days_left"], passed])

    banners = [tuple(int(v) for v in m.groups()[:2]) + (m.group(3),) for m in map(CLOCK_BANNER.search, log_lines(ctx)) if m]
    ctx.check("C2 no clock banner in the first years (they come in years 7, 8 and 9)", banners == [] or second["year"] >= 7, banners)
    ctx.check("C2 a clock banner shows only in years 7, 8 or 9", all(year in (7, 8, 9) for year, _, _ in banners), banners)
    ctx.metric("clock_days_left", second["days_left"])
    return ctx.result()
