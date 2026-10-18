"""Probe for M10: how does the game represent ore deposits (iron, salt, clay)?

Research tool. Reads RTSMultiEngineCPP.deposits (array of struct Ore: Pos, oreComponent, iNo, Type, amt, Region) and the region
production limit functions. It writes nothing to the game, except the optional step "limit" (HARNESS_PROBE=limit) that sets and clears
a production limit of one good. It never calls a save function.
"""

import json
import os

from runlib.bridge_client import object_path

NAME = "probe-deposits"
LIMIT_S = 300
HIDDEN = True
IRON = 21  # TBD: checked by the probe through the item names in the output
MAX_ROWS = 60


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


def run(ctx) -> dict:
    engine = ctx.bridge.engine_path()
    deposits = attempt(ctx, "deposits", lambda: ctx.bridge.read_property(engine, "deposits"))
    if isinstance(deposits, list):
        note(ctx, "count", count=len(deposits))
        by_type: dict = {}
        for row in deposits:
            if isinstance(row, dict):
                by_type.setdefault(row.get("Type"), []).append(row.get("amt"))
        note(ctx, "by_type", amounts={str(k): v[:20] for k, v in by_type.items()}, counts={str(k): len(v) for k, v in by_type.items()})
        for row in deposits[:MAX_ROWS]:
            note(ctx, "row", row=row)
    for name in ("ResourceNode", "BP_ResourceNode_C", "BP_Deposit_C", "DepositDecal", "BP_DepositDecal_C", "ResourceSettings", "MineableNode"):
        attempt(ctx, f"count {name}", lambda n=name: len(ctx.bridge._result("objects", class_name=n, limit=500)["objects"]))
    nodes = [object_path(ref) for ref in ctx.bridge._result("objects", class_name="ResourceNode", limit=500)["objects"]]
    note(ctx, "nodes", count=len(nodes))
    kinds: dict = {}
    for path in nodes:
        clumps = ctx.bridge.read_property(path, "resourceClumps")
        kind = clumps[0]["__object"].split(" ", 1)[0] if clumps else "empty"
        kinds[kind] = kinds.get(kind, 0) + 1
    note(ctx, "node kinds", kinds=kinds)
    buildings = [object_path(ref) for ref in ctx.bridge._result("objects", class_name="SMBuildingMaster", limit=300)["objects"]]
    note(ctx, "buildings", count=len(buildings))
    totals: dict = {}
    for path in buildings[:80]:
        tracker = attempt(ctx, f"tracker {path[-10:]}", lambda p=path: ctx.bridge.read_property(p, "ProductionTrackerComponent"))
        if not isinstance(tracker, dict):
            continue
        tpath = object_path(tracker)
        for days in (1, 36500):
            produced = attempt(ctx, f"produced {days} {path[-10:]}", lambda t=tpath, d=days: ctx.bridge.call_function(t, "getGoodsProducedOver", [d]))
            if days == 36500 and isinstance(produced, dict):
                for good, amount in produced.items():
                    totals[good] = totals.get(good, 0) + amount
    note(ctx, "produced totals", totals=totals)
    found = attempt(ctx, "DepositDecal objects", lambda: ctx.bridge._result("objects", class_name="DepositDecal", limit=200)["objects"])
    for ref in (found or [])[:MAX_ROWS]:
        path = ref["__object"].split(" ", 1)[-1] if isinstance(ref, dict) and "__object" in ref else str(ref)
        fields = {name: attempt(ctx, f"{path[-24:]} {name}", lambda p=path, n=name: ctx.bridge.read_property(p, n))
                  for name in ("depositedGood", "Limit", "depositType", "bRichDeposit")}
        note(ctx, "deposit", path=path[-60:], **fields)
    region = ctx.bridge.player_region_path()
    for good in (IRON, 22, 23, 24, 25, 26, 27, 28):
        attempt(ctx, f"isProductionLimited {good}", lambda g=good: ctx.bridge.call_function(region, "isProductionLimited", [g]))
    if os.environ.get("HARNESS_PROBE") == "limit":
        attempt(ctx, "set limit", lambda: ctx.bridge.call_function(region, "setProductionLimit", [IRON, 0]))
        attempt(ctx, "limited", lambda: ctx.bridge.call_function(region, "isProductionLimited", [IRON]))
        attempt(ctx, "get limit", lambda: ctx.bridge.call_function(region, "getProductionLimit", [IRON, -1]))
        attempt(ctx, "unlimit", lambda: ctx.bridge.call_function(region, "setProductionUnlimited", [IRON]))
    return ctx.result()
