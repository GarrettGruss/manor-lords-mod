"""Spike for add-raid-carry-caps task 1.1: write ItemsLooted above the cap in a native raid and watch the raiders.

Options (run.py --env): LOOT_VALUE (default 50). It saves nothing.
"""

from runlib.units import loot_max, loot_total, side_count

NAME = "probe-raid-loot-cap"
LIMIT_S = 600
LONG_REASON = "A native raid walks, loots and leaves over about 16 game days; the probe samples up to 12 game days at speed 3."
SAMPLE_DAYS = 40
STEP_S = 2 # game seconds between samples (one game day is 40 game seconds)


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run(ctx) -> dict:
    value = int(ctx.variant_option("LOOT_VALUE", "50"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_set_roles", enabled=ctx.variant_option("ROLES", "0") == "1")
    before = side_count(ctx.actions.units_census(), "bandit")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    bandits = side_count(ctx.actions.units_census(), "bandit")
    ctx.actions.set_unit_loot(side="bandit", count=bandits, amount=value)
    rows = []
    for day in range(SAMPLE_DAYS):
        census = ctx.actions.units_census()
        raid = tracker(ctx)
        keys = ("state", "living", "loot", "looted_total", "leaving", "burned", "capped", "carry_cap")
        row = {"day": day, "loot_total": loot_total(census), "loot_max": loot_max(census), "tracker": {k: raid.get(k) for k in keys}}
        rows.append(row)
        ctx.log.info(f"SPIKE {row}")
        if raid.get("state") != "active":
            break
        ctx.popups()
        ctx.time.run_game_seconds(STEP_S, speed=3)
    ctx.metric("value_written", value)
    ctx.metric("bandits", bandits - before)
    ctx.metric("max_loot_seen", max(r["loot_max"] for r in rows))
    ctx.check("probe ran", True, len(rows))
    return ctx.result()
