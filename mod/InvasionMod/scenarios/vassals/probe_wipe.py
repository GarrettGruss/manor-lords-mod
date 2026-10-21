"""Spike for the change add-vassal-sack-wipe (tasks 1.1, 1.2): what an AI village does when all its villagers are dead,
and whether raising its villager count to 5 makes the AI rebuild.

Research tool, not a test. It never fails on a game answer: every answer goes to `probe.jsonl` in the run folder.
The probe kills villagers of an AI village in the test only. It saves nothing. Never write the region owner.
Environment: WIPE_COLLAPSE (houses to collapse before the wipe, default 3), WIPE_DAYS (days to watch after the wipe, default 10),
RESTORE_DAYS (days to watch after the restore, default 15), RESTORE_SUPPLY (settleRegion supply, default 0).
"""

import json
import os

NAME = "probe-vassal-wipe"
LIMIT_S = 1500
HIDDEN = True
SPEED = 3
LONG_REASON = "Claim, settle and handover (about 100 s), 6 game days of growth, the wipe, then up to 25 game days of watching at speed 3."
INFLUENCE = 1000
GROWTH_DAYS = 6
COLLAPSE = int(os.environ.get("WIPE_COLLAPSE", "3"))
WIPE_DAYS = int(os.environ.get("WIPE_DAYS", "10"))
RESTORE_DAYS = int(os.environ.get("RESTORE_DAYS", "15"))
RESTORE_SUPPLY = int(os.environ.get("RESTORE_SUPPLY", "0"))
KILL_FIRST = int(os.environ.get("WIPE_FIRST", "1"))
STEP_DAYS = 2
LOG_LINES = 40


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
        note(ctx, step, ok=True, result=result)
        return result
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, ok=False, error=str(error)[:500])
        return None


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def make_vassal(ctx) -> str:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")
    return region


def region_row(ctx, region: str) -> dict:
    return next(row for row in ctx.actions.regions_state()["regions"] if row["region"] == region)


def probe(ctx, region: str) -> dict:
    return ctx.mod.command("InvasionMod.probe_region", region=region)


def lord_number(ctx, name: str):
    for row in ctx.actions.lords_state(log=0)["lords"]:
        if row["name"] == name:
            return row["lord"]
    return None


def watch(ctx, region: str, lord_name: str, label: str, days: int) -> None:
    seen: set[str] = set()
    for day in range(STEP_DAYS, days + 1, STEP_DAYS):
        ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        state = attempt(ctx, f"{label} day {day} probe", lambda: probe(ctx, region))
        attempt(ctx, f"{label} day {day} row", lambda: region_row(ctx, region))
        attempt(ctx, f"{label} day {day} vassals", lambda: vassals(ctx))
        logs = attempt(ctx, f"{label} day {day} lords", lambda: ctx.actions.lords_state(log=LOG_LINES)["logs"])
        for line in (logs or {}).get("debugLog_AI_construction", []):
            if line.startswith(lord_name) and line not in seen:
                seen.add(line)
                note(ctx, f"{label} day {day} construction line", line=line)
        if state:
            ctx.metric(f"{label}_day{day}_standing", state["standing"])
            ctx.metric(f"{label}_day{day}_families", state["families"])
    ctx.ensure_alive(label)


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    region = make_vassal(ctx)
    lord_name = vassals(ctx)["vassals"][0]["lord"]
    note(ctx, "vassal", region=region, lord=lord_name)
    ctx.time.run_game_days(GROWTH_DAYS, speed=SPEED)
    note(ctx, "grown", probe=probe(ctx, region), row=region_row(ctx, region), vassals=vassals(ctx))

    if COLLAPSE:
        attempt(ctx, "collapse houses", lambda: ctx.mod.command("InvasionMod.probe_collapse", region=region, count=COLLAPSE))
        ctx.time.run_game_days(1, speed=SPEED)
        note(ctx, "after collapse", probe=probe(ctx, region))

    attempt(ctx, "kill villagers", lambda: ctx.mod.command("InvasionMod.probe_kill_villagers", region=region, count=KILL_FIRST))
    if KILL_FIRST < 1000:
        ctx.time.run_game_days(1, speed=SPEED)
        note(ctx, "after first kill", probe=probe(ctx, region))
        attempt(ctx, "kill rest", lambda: ctx.mod.command("InvasionMod.probe_kill_villagers", region=region, count=1000))
    watch(ctx, region, lord_name, "wiped", WIPE_DAYS)

    number = lord_number(ctx, lord_name)
    note(ctx, "lord number", number=number)
    if number is not None:
        attempt(ctx, "restore settle_region", lambda: ctx.actions.settle_region(region, target=number, settlement_type=1, supply=RESTORE_SUPPLY))
        note(ctx, "after restore call", probe=probe(ctx, region))
        watch(ctx, region, lord_name, "restored", RESTORE_DAYS)
    ctx.time.run_game_days(1, speed=SPEED)
    return ctx.result()
