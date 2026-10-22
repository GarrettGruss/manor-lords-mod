"""update-raid-clock-yearly: no raid in game year 1, one raid in each later game year, by a season roll.

A real calendar year takes about 1800 wall seconds at speed 3, so the scenario counts season changes with the test command
`invasion_yearly_advance_season` (it calls the same roll as a real season change, with a fixed roll value). The real game gives
the calendar, the season read, the real spawn and the raid tracker. It saves nothing.
"""

import re

NAME = "invasion-yearly-raid"
DESCRIPTION = "Year 1 has no raid. Year 2 and year 3 each have one raid, planned by a season roll (plunder, then subjugation)."
LIMIT_S = 1500
SPEED = 3
LONG_REASON = "Two real raids spawn and the first one must end (up to 40 game days) before the second. At speed 3 this takes about 700 s."
DAY_LIMIT = 40
QUIET_DAYS = 6
SPAWN = re.compile(r"INVASION spawn day=(\d+) .*kind=(\w+)")
NO_ROLL = 0.9  # over every chance except the last season
ROLL = 0.0     # under every chance


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def spawns(ctx) -> list[tuple[str, str]]:
    return [m.groups() for m in map(SPAWN.search, log_lines(ctx)) if m]


def yearly(ctx) -> dict:
    return ctx.mod.command("InvasionMod.invasion_yearly_state")


def advance(ctx, roll: float) -> dict:
    return ctx.mod.command("InvasionMod.invasion_yearly_advance_season", roll=roll)


def raids(ctx) -> list[dict]:
    return ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: yearly(ctx)["season_no"] == 0, 30, what="the first season read")
    first = yearly(ctx)
    ctx.check("Y0 the game calendar gives a season number", isinstance(first["season"], int), first["season"])
    ctx.check("Y0 the game starts in year 1, first season count", (first["year"], first["position"]) == (1, 1), first)

    for _ in range(QUIET_DAYS):
        run_day(ctx)
    quiet = yearly(ctx)
    ctx.check("Y1 no raid is planned in the first days", quiet["raid_day"] == 0 and quiet["raids_spawned"] == 0, quiet)

    # Year 1: three season changes, each with the roll that always passes. No raid may come.
    for _ in range(3):
        answer = advance(ctx, ROLL)
        ctx.check(f"Y1 season {answer['position']} of year {answer['year']} plans no raid", answer["planned"] is False and answer["raid_day"] == 0, answer)
    ctx.check("Y1 the log has no raid spawn in year 1", spawns(ctx) == [], spawns(ctx))

    # Year 2: the roll fails in season 1, passes in season 2, then the year is done.
    answer = advance(ctx, NO_ROLL)
    ctx.check("Y2 year 2 begins at the fourth season change", (answer["year"], answer["position"]) == (2, 1), answer)
    ctx.check("Y2 a roll over the chance (25 percent) plans no raid", answer["planned"] is False, answer)
    answer = advance(ctx, ROLL)
    ctx.check("Y2 a roll under the chance (33 percent) plans a raid", answer["planned"] is True and answer["raid_day"] > 0, answer)
    ctx.check("Y2 the plan is 1 to 90 game days ahead", 1 <= answer["raid_day"] - answer["day"] <= 90, [answer["raid_day"], answer["day"]])
    for _ in range(2):
        answer = advance(ctx, ROLL)
        ctx.check(f"Y2 season {answer['position']} plans no second raid in the year", answer["planned"] is False, answer)
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 1, 30, what="the year 2 raid record")
    ctx.check("Y2 one plunder raid spawned", [kind for _, kind in spawns(ctx)] == ["plunder"], spawns(ctx))

    # Year 3: no roll passes before the fourth season. The fourth season always raids (subjugation, the second raid).
    for _ in range(3):
        answer = advance(ctx, NO_ROLL)
        ctx.check(f"Y3 season {answer['position']} of year {answer['year']} plans no raid", answer["planned"] is False, answer)
    answer = advance(ctx, NO_ROLL)
    ctx.check("Y3 the fourth season plans a raid whatever the roll is", answer["planned"] is True and answer["sub_day"] > 0, answer)
    ctx.check("Y3 the year 3 raid is the subjugation raid", answer["sub_spawned"] is False and answer["sub_day"] > 0, answer)

    days = 0
    while raids(ctx)[0]["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
    if not ctx.mod.command("InvasionMod.invasion_subjugation_state")["spawned"]:  # else the planned day came while the first raid fought
        ctx.mod.command("InvasionMod.invasion_subjugation_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 2, 30, what="the year 3 raid record")
    ctx.check("Y3 the second raid is a subjugation raid", raids(ctx)[1]["kind"] == "subjugation", raids(ctx)[1].get("kind"))
    kinds = [kind for _, kind in spawns(ctx)]
    ctx.check("Y4 exactly 2 raids spawned in 3 game years (year 2 and year 3)", kinds == ["plunder", "subjugation"], kinds)
    ctx.metric("raids_spawned", yearly(ctx)["raids_spawned"])
    return ctx.result()
