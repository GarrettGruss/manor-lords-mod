"""Run 2 game days at speed 3 from the paused start. Check the date, the pause and the wall time."""

from runlib.timectl import absolute_day

NAME = "time-advance"
DESCRIPTION = "Run 2 game days at speed 3. The date must move by 2 days and the clock must stop at the end."
LIMIT_S = 90
DAYS = 2
SPEED = 3
# At speed 3 one game day takes 5 wall seconds, so 2 days take about 10 s. The range allows for slow bridge calls.
WALL_RANGE_S = (6, 40)


def run(ctx) -> dict:
    expect = ctx.expect
    before = ctx.read_calendar()
    record = ctx.time.run_game_days(DAYS, speed=SPEED)
    after = ctx.read_calendar()

    expect.changed("absolute day moved by 2", absolute_day(before), absolute_day(after), DAYS, DAYS)
    expect.changed("daysTotal moved by 2", record["days_start"], record["days_end"], DAYS, DAYS)
    expect.equals("paused at the end", record["paused_at_end"], True)
    expect.in_range("wall seconds", record["wall_s"], *WALL_RANGE_S)
    stopped = ctx.read_clock(3.0)
    expect.equals("clock stands still for 3 s", stopped["paused"], True)
    return ctx.result()
