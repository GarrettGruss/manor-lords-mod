"""Probe for M13 iteration 02: does the garrison limit hook change real retinue hiring?

Research tool. Use fixture manor-bailey (a built manor house). Run it twice and compare probe.jsonl:
    uv run python harness\run.py --scenario probe-retinue-cap --fixture manor-bailey --slot auto
    uv run python harness\run.py --scenario probe-retinue-cap --fixture manor-bailey --slot auto --env HARNESS_GARRISON_BONUS=24 --env HARNESS_GARRISON_MODULE_TYPE=98
It reads the limit and the hire answers, then calls hireExtraRetinue up to a cap and counts the bound retinue.
It never calls a save function.
"""

import json

from runlib.bridge_client import object_path

NAME = "probe-retinue-cap"
LIMIT_S = 300
HIDDEN = True
MANOR_TYPE = 98
MAX_HIRES = 40
SILVER = 100000


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:500])
        return None
    note(ctx, step, result=result)
    return result


def find_manor_path(ctx) -> str | None:
    found = ctx.bridge._result("objects", class_name="SMBuildingMaster", limit=80)["objects"]
    for ref in found:
        path = object_path(ref)
        data = ctx.bridge.read_property(path, "Data")
        if isinstance(data, dict) and data.get("bType") == MANOR_TYPE:
            return path
    return None


def bound_count(ctx, manor: str):
    result = attempt(ctx, "getBoundRetinue", lambda: ctx.bridge.call_function(manor, "getBoundRetinue", []))
    return len(result) if isinstance(result, list) else result


def run(ctx) -> dict:
    ctx.actions.set_silver(SILVER)
    manor = find_manor_path(ctx)
    ctx.check("P0 the manor house is found", manor is not None, manor)
    note(ctx, "start", limit=attempt(ctx, "limit", lambda: ctx.bridge.call_function(manor, "getModularGarrisonLimit", [])),
         can_hire=attempt(ctx, "canHireRetinue", lambda: ctx.bridge.call_function(manor, "canHireRetinue", [])),
         cost=attempt(ctx, "cost", lambda: ctx.bridge.call_function(manor, "GetRetinueHireTreasuryCost", [])),
         bound=bound_count(ctx, manor))
    last, stuck = bound_count(ctx, manor), 0
    for index in range(MAX_HIRES):
        attempt(ctx, f"hire {index}", lambda: ctx.bridge.call_function(manor, "hireExtraRetinue", []))
        ctx.time.run_game_seconds(1, speed=1)
        now = bound_count(ctx, manor)
        note(ctx, "after hire", index=index, bound=now,
             can_hire=attempt(ctx, "canHireRetinue", lambda: ctx.bridge.call_function(manor, "canHireRetinue", [])))
        stuck = stuck + 1 if now == last else 0
        last = now
        if stuck >= 3:
            break
    ctx.metric("bound_retinue_end", last)
    return ctx.result()
