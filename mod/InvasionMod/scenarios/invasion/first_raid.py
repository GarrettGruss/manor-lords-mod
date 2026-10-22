"""M02 iteration 01, A1 to A5: one scheduled raid with a daily banner, spawned on the planned day.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1), INVASION_SIZE (small, medium or large, default medium).
The size is forced so the unit count can be checked (A3). The scenario runs the real countdown (1 to 90 game days).
It saves nothing.
"""

import re

NAME = "invasion-first-raid"
LIMIT_S = 900
SPEED = 3
LONG_REASON = "The countdown is real: 30 to 90 game days plus a margin. One game day takes about 5 wall seconds at speed 3 (about 450 s)."
CHUNK_DAYS = 5
MAX_DAYS_PAST_PLAN = 3
MULTIPLIERS = {"small": 1, "medium": 2, "large": 3}
BANNER = re.compile(r"INVASION banner day=(\d+) days_left=(\d+) raiders=(\d+) shown=(\w+)")
SPAWN = re.compile(r"INVASION spawn day=(\d+) planned_day=(\d+) squads=(\d+) raiders=(\d+)")


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.invasion_state")


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    size = ctx.variant_option("INVASION_SIZE", "medium")
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    plan = ctx.mod.command("InvasionMod.invasion_set_size", size=size)
    expected_squads = MULTIPLIERS[size] * difficulty
    ctx.log.info(f"INVASION plan {plan}")

    plan_day = plan["day"]
    wait = plan["raid_day"] - plan["plan_day"]
    warning = plan["raid_day"] - plan["warning_day"]
    ctx.check("A1 the planned day is 1 to 90 days after the plan (the season rule)", 1 <= wait <= 90, wait)
    ctx.check("A1 the warning time is 14 to 56 days and at most the wait", 1 <= warning <= min(56, wait) and (warning >= 14 or warning == wait), warning)
    ctx.check("A3 planned squads = multiplier x difficulty", plan["squads"] == expected_squads, plan["squads"])
    ctx.check("A3 the composition has one template for each squad", len(plan["composition"].split("-")) == expected_squads, plan["composition"])
    planned_units = plan["raiders"]  # the sum of the squad sizes of the composition (M05 iteration 02)

    while plan["raids_spawned"] == 0 and plan["day"] <= plan["raid_day"] + MAX_DAYS_PAST_PLAN:
        ctx.time.run_game_days(CHUNK_DAYS, speed=SPEED)
        plan = {**plan, **state(ctx)}
    ctx.check("the raid was spawned", plan["raids_spawned"] == 1, plan["raids_spawned"])

    lines = log_lines(ctx)
    banners = [tuple(int(v) for v in m.groups()[:3]) for m in map(BANNER.search, lines) if m]
    spawns = [tuple(int(v) for v in m.groups()) for m in map(SPAWN.search, lines) if m]
    ctx.check("A4 one spawn in the log", len(spawns) == 1, spawns)
    spawn_day, _, _, spawn_raiders = spawns[0] if spawns else (0, 0, 0, 0)
    ctx.check("A3 the raid spawned on the planned day, plus or minus 1", abs(spawn_day - plan["raid_day"]) <= 1, [spawn_day, plan["raid_day"]])

    shown = {day: (left, raiders) for day, left, raiders in banners}
    for day in range(plan["warning_day"], plan["raid_day"]):
        entry = shown.get(day)
        ctx.check(f"A2 banner on day {day} with the right days left", entry is not None and entry[0] == plan["raid_day"] - day, entry)
    ctx.check("A2 no banner before the warning", all(day >= plan["warning_day"] for day in shown), sorted(shown)[:1])
    ctx.check("A2 no day has two banners", len(banners) == len(shown), len(banners))

    # The raid is a lord army (not the bandit side), so the census of bandits does not see it. The raid tracker counts its units at the start.
    spawned_units = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"][0]["initial"]
    ctx.check("A3 spawned unit count = planned units (a few raiders may die at once)", 0.9 * planned_units <= spawned_units <= planned_units,
              [spawned_units, planned_units])
    # The forced size comes after the first check. A banner of the plan day can show the random size from before.
    estimates = {raiders for day, _, raiders in banners if day > plan_day}
    ctx.check("A5 every banner estimate equals the spawned size", estimates == {spawned_units}, [sorted(estimates), spawned_units])
    ctx.check("A5 the log spawn size equals the unit count", spawn_raiders == spawned_units, spawn_raiders)
    ctx.metric("difficulty", difficulty)
    ctx.metric("spawned_units", spawned_units)
    return ctx.result()
