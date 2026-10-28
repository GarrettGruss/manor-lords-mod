"""M02 iteration 01 and update-raid-banners, A1 to A5: one scheduled yearly raid, spawned on the planned day.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1), INVASION_SIZE (small, medium or large, default medium).
The size is forced so the unit count can be checked (A3). A small or medium yearly raid has no banner (A2).
A large yearly raid (the player raid) has one banner, 30 game days before the raid, or on the plan day when the plan is shorter (A2).
The scenario runs the real countdown (1 to 90 game days). It saves nothing.
"""

import re
import time

from runlib import osinput

NAME = "invasion-first-raid"
LIMIT_S = 900
SPEED = 3
LONG_REASON = "The countdown is real: up to 90 game days plus a margin. One game day takes about 5 wall seconds at speed 3 (about 450 s)."
CHUNK_DAYS = 5
MAX_DAYS_PAST_PLAN = 3
MULTIPLIERS = {"small": 1, "medium": 2, "large": 3}
BANNER_DAYS = 30
RAID_BANNER = re.compile(r"INVASION raid banner kind=(\w+) day=(\d+) days_left=(\d+) target=(.*?) raiders=(\d+) shown=(\w+)")
OLD_BANNER = re.compile(r"INVASION banner day=")
LEAD_DAYS = 5  # config invasion.border.march_lead_days: the army spawns this many days before the raid day (change update-spawn-from-map-border)
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
    if ctx.variant_option("INVASION_MENU_SHOT", "0") == "1":  # picture evidence of the raid menu with a planned yearly raid (needs --pak InvasionMod)
        ctx.mod.command("InvasionMod.raid_widget_open")
        time.sleep(1.0)
        osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
        time.sleep(1.0)
        ctx.screenshot("raid-menu-yearly-planned")
        ctx.mod.command("InvasionMod.raid_widget_close")

    wait = plan["raid_day"] - plan["plan_day"]
    ctx.check("A1 the planned day is 1 to 90 days after the plan (the season rule)", 1 <= wait <= 90, wait)
    ctx.check("A3 planned squads = multiplier x difficulty", plan["squads"] == expected_squads, plan["squads"])
    ctx.check("A3 the composition has one template for each squad", len(plan["composition"].split("-")) == expected_squads, plan["composition"])
    planned_units = plan["raiders"]  # the sum of the squad sizes of the composition (M05 iteration 02)

    while plan["raids_spawned"] == 0 and plan["day"] <= plan["raid_day"] + MAX_DAYS_PAST_PLAN:
        ctx.time.run_game_days(CHUNK_DAYS, speed=SPEED)
        plan = {**plan, **state(ctx)}
    ctx.check("the raid was spawned", plan["raids_spawned"] == 1, plan["raids_spawned"])

    lines = log_lines(ctx)
    banners = [m.groups() for m in map(RAID_BANNER.search, lines) if m]
    spawns = [tuple(int(v) for v in m.groups()) for m in map(SPAWN.search, lines) if m]
    ctx.check("A4 one spawn in the log", len(spawns) == 1, spawns)
    spawn_day, _, _, spawn_raiders = spawns[0] if spawns else (0, 0, 0, 0)
    ctx.check("A3 the raid spawned 5 days (march lead) before the planned day, plus or minus 1", abs(spawn_day - (plan["raid_day"] - LEAD_DAYS)) <= 1, [spawn_day, plan["raid_day"]])
    ctx.check("A2 no daily countdown banner", not any(OLD_BANNER.search(line) for line in lines), "an INVASION banner line was found")

    # The raid is a lord army (not the bandit side), so the census of bandits does not see it. The raid tracker counts its units at the start.
    raid_row = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"][0]
    spawned_units = raid_row["initial"] + raid_row.get("deaths_on_march", 0)  # the raid counts from the army that arrived
    ctx.check("A3 spawned unit count = planned units (a few raiders may die at once)", 0.9 * planned_units <= spawned_units <= planned_units,
              [spawned_units, planned_units])
    if size == "large":
        ctx.check("A2 a large raid has exactly one banner", len(banners) == 1, banners)
        if banners:
            kind, _, days_left, target, raiders, _ = banners[0]
            ctx.check("A2 the banner is for the plunder raid and names the player", kind == "plunder" and target == "you", [kind, target])
            ctx.check("A2 the banner shows 30 days before, or on the plan day for a shorter plan", abs(int(days_left) - min(BANNER_DAYS, wait)) <= 1,
                      [days_left, wait])
            ctx.check("A5 the banner estimate equals the spawned size", int(raiders) == spawned_units, [raiders, spawned_units])
    else:
        ctx.check("A2 a small or medium raid has no banner", banners == [], banners)
    ctx.check("A5 the log spawn size equals the unit count", spawn_raiders == spawned_units, spawn_raiders)
    ctx.metric("difficulty", difficulty)
    ctx.metric("spawned_units", spawned_units)
    return ctx.result()
