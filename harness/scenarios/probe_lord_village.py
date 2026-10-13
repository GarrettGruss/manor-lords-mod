"""Probe for spec 10 spike S13 (dynamic lords): a spawned neutral lord founds a village in a free region and builds (rerun, 3 runs per variant).

Research tool. It records every answer in `probe.jsonl`. The variant is chosen with the environment:
LORD_VILLAGE_SUPPLY (0 to 2) and LORD_VILLAGE_TYPE (settlement type 1 to 5). It never saves the game.
"""

import json
import os

NAME = "probe-lord-village"
LIMIT_S = 600
HIDDEN = True
LONG_REASON = "The probe watches the lord village for 30 game days (about 150 s at 8x)."
SUPPLY = int(os.environ.get("LORD_VILLAGE_SUPPLY", "2"))
SETTLEMENT_TYPE = int(os.environ.get("LORD_VILLAGE_TYPE", "1"))
WATCH_DAYS = int(os.environ.get("LORD_VILLAGE_DAYS", "30"))
STEP_DAYS = 10
SPEED = 3
LOG_LINES = 40


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    note(ctx, "regions", free=free, rows=rows)
    if not free:
        raise RuntimeError("no free region on this map: the probe cannot run")
    return free[0]


def region_row(ctx, region: str) -> dict:
    return next(row for row in ctx.actions.regions_state()["regions"] if row["region"] == region)


LORD_NAME = "Probe Lord"
seen_lines: set[str] = set()  # the log keeps only the newest lines of all lords, so lines are collected at every step


def build_lines(ctx, lord: int) -> int:
    """Count the successful AI_build lines of the probe lord seen so far. `lord` is unused: the log names lords by name."""
    state = ctx.actions.lords_state(log=LOG_LINES)
    for line in state["logs"].get("debugLog_AI_construction", []):
        if line.startswith(LORD_NAME) and "AI_build" in line and "lacks" not in line and "failed" not in line:
            seen_lines.add(line)
    return len(seen_lines)


def setup_lord(ctx) -> int:
    actions = ctx.actions
    lord = actions.spawn_ai_lord("Probe Lord", can_build=True)["lord"]
    note(ctx, "relations", result=actions.lord_relations(lord))
    note(ctx, "start ai", result=actions.lord_start_ai(lord, speed=1, can_build=True))
    return lord


def run(ctx) -> dict:
    actions, expect = ctx.actions, ctx.expect
    region = free_region(ctx)
    lord = setup_lord(ctx)
    found = actions.lord_found_village(lord, region, settlement_type=SETTLEMENT_TYPE, supply=SUPPLY)
    note(ctx, "found village", supply=SUPPLY, type=SETTLEMENT_TYPE, result=found)
    start = region_row(ctx, region)
    ctx.metric("buildings_start", start.get("buildings") or 0)
    for step in range(STEP_DAYS, WATCH_DAYS + 1, STEP_DAYS):
        ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        row = region_row(ctx, region)
        note(ctx, f"day {step}", region=row, build_lines=build_lines(ctx, lord))
        ctx.metric(f"buildings_day{step}", row.get("buildings") or 0)
    ctx.ensure_alive("lord village")
    last = region_row(ctx, region)
    ctx.metric("buildings_end", last.get("buildings") or 0)
    ctx.metric("families_end", last.get("families") or 0)
    ctx.metric("build_lines", build_lines(ctx, lord))
    note(ctx, "final lords", result=actions.lords_state(log=LOG_LINES))
    expect.at_least("the lord village has buildings after the watch", last.get("buildings") or 0, 1)
    return ctx.result()
