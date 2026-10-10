"""Smoke test: pause state, unpause, calendar, pause again."""

NAME = "smoke"
LIMIT_S = 60

# A day of the year is 1 to 366. Day 61 of year 1 was seen in the test save.
CALENDAR_RANGES = {"day": (1, 366), "month": (1, 12), "year": (0, 10000)}


def run(ctx) -> dict:
    ctx.log.info("smoke: the game must be paused after boot")
    clock = ctx.read_clock()
    ctx.check("clock is stopped after boot", clock["paused"], clock["change"], [0, 0.001])

    unpaused = ctx.unpause()
    ctx.check("clock moves after unpause", unpaused["ok"], unpaused["change"], [0.001, 100])

    calendar = ctx.read_calendar()
    for key, (low, high) in CALENDAR_RANGES.items():
        ctx.check_range(f"calendar {key} is sane", calendar[key], low, high)

    paused = ctx.pause()
    ctx.check("clock is stopped after pause", paused["ok"], paused["change"], [0, 0.001])
    return ctx.result()
