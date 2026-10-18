"""M02 iteration 02, C1 to C3: the great raid clock is 3 to 5 game years, shows in the banner and counts down.

It saves nothing.
"""

import re

NAME = "invasion-great-raid-clock"
LIMIT_S = 300
SPEED = 3
CLOCK_BANNER = re.compile(r"INVASION clock banner day=(\d+) days_left=(\d+) shown=(\w+)")
CLOCK_START = re.compile(r"INVASION clock start day=(\d+) end_day=(\d+) length=(\d+)")
WAIT_DAYS = 3


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
    length = starts[0][2] if starts else 0
    ctx.check("C1 the clock is 3 to 5 game years (1095 to 1825 days)", 3 * 365 <= length <= 5 * 365, length)

    ctx.time.run_game_days(WAIT_DAYS, speed=SPEED)
    second = clock(ctx)
    passed = second["day"] - first["day"]
    ctx.check("C3 the end day does not change", second["great_raid_day"] == first["great_raid_day"], [first["great_raid_day"], second["great_raid_day"]])
    ctx.check("C3 days left fell by the days that passed", first["days_left"] - second["days_left"] == passed, [first["days_left"], second["days_left"], passed])

    banners = [tuple(int(v) for v in m.groups()[:2]) + (m.group(3),) for m in map(CLOCK_BANNER.search, log_lines(ctx)) if m]
    ctx.check("C2 a clock banner or a minor raid banner showed", len(banners) >= 1 or first["last_clock_banner_day"] > 0, banners)
    days = [day for day, _, _ in banners]
    ctx.check("C2 at most one clock banner for each day", len(days) == len(set(days)), days)
    ctx.check("C2 the banner days left match the clock", all(left == second["great_raid_day"] - day for day, left, _ in banners), banners)
    ctx.metric("clock_length_days", length)
    return ctx.result()
