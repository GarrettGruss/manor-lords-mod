"""Probe for the spike finite-resource-limits: where are the mine deposit amount and the region unlimited flag stored?

Research tool, hidden. Step 1 (default) only reads. It never calls a save function and never reads structs with soft object fields.
HARNESS_PROBE=<step> selects other steps (see run()).
"""

import json
import os

from runlib.bridge_client import object_path

NAME = "probe-finite-limits"
LIMIT_S = 300
HIDDEN = True


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:3000]}")
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


def names(items, words):
    if isinstance(items, dict):
        items = [f"{p['name']}:{p['type']}" for p in items.get("properties", [])]


def prop_names(res, ref, **extra):
    data = res("props", ref=ref, include_super=True, read_soft=False, **extra)
    return [f"{p['name']}:{p['type']}" for p in data.get("properties", [])]


def run(ctx) -> dict:
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    engine = bridge.engine_path()
    step = os.environ.get("HARNESS_PROBE", "classes")
    if step == "classes":
        for name in ("ironResourceBP", "saltResourceBP", "clayResourceBP"):
            cls = attempt(ctx, f"engine.{name}", lambda n=name: bridge.read_property(engine, n))
            if cls:
                ref = object_path(cls) if isinstance(cls, dict) and " " in str(cls.get("__object", "")) else None
                note(ctx, f"{name} ref", ref=ref, raw=str(cls)[:300])
                if ref:
                    attempt(ctx, f"{name} cdo props", lambda r=ref: [p for p in prop_names(res, "cdo:" + r.replace("_C", "_C"))][:150])
        node = object_path(res("objects", class_name="ResourceNode", limit=1)["objects"][0])
        clumps = attempt(ctx, "clumps", lambda: bridge.read_property(node, "resourceClumps"))
        if clumps:
            clump = object_path(clumps[0])
            attempt(ctx, "clump props", lambda: prop_names(res, clump))
            attempt(ctx, "clump funcs", lambda: [f["name"] for f in res("funcs", ref=clump)][:60])
        for name in ("DepositDecal", "ResourceNodeProperties", "Ore"):
            attempt(ctx, f"types {name}", lambda n=name: str(res("objects", class_name=n, limit=3))[:300])

    if step == "buildings":
        words = ("mine", "deposit", "ore", "limit", "resource", "infin", "vein", "prospect", "quarry", "pit")
        match = lambda n: any(w in n.lower() for w in words)  # noqa: E731
        attempt(ctx, "engine funcs", lambda: [f["name"] for f in res("funcs", ref=engine) if match(f["name"]) and f["owner"] != "Actor"])
        attempt(ctx, "region all funcs", lambda: [f["name"] for f in res("funcs", ref=bridge.player_region_path()) if f["owner"] == "Region"])
        blds = [object_path(r) for r in res("objects", class_name="SMBuildingMaster", limit=400)["objects"]]
        first = blds[0]
        attempt(ctx, "building props", lambda: [n for n in prop_names(res, first) if match(n.split(":")[0])])
        attempt(ctx, "building funcs", lambda: [f["name"] for f in res("funcs", ref=first) if match(f["name"]) and f["owner"] != "Actor"])
        counts = {}
        for path in blds:
            try:
                key = str(bridge.read_property(path, "buildingType"))[:60]
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive("type")
                key = "err " + str(error)[:40]
            counts[key] = counts.get(key, 0) + 1
        note(ctx, "building types", counts=counts)
        attempt(ctx, "tracker funcs", lambda: [f["name"] for f in res("funcs", ref=object_path(bridge.read_property(first, "ProductionTrackerComponent"))) if f["owner"] not in ("Actor", "ActorComponent")])

    if step == "limit":
        region = bridge.player_region_path()
        for name in ("ironResourceBP", "saltResourceBP"):
            ref = object_path(bridge.read_property(engine, name))
            for field in ("amt", "capacity", "Type"):
                attempt(ctx, f"cdo {name} {field}", lambda r=ref, f=field: bridge.read_property("cdo:" + r, f))
        goods = (14, 145)  # EItemType IronOre, Salt
        for good in goods:
            attempt(ctx, f"before {good}", lambda g=good: [bridge.call_function(region, "isProductionLimited", [g]), bridge.call_function(region, "getProductionLimit", [g, -1])])
            attempt(ctx, f"set high {good}", lambda g=good: bridge.call_function(region, "setProductionLimit", [g, 1000000]))
            attempt(ctx, f"after set {good}", lambda g=good: [bridge.call_function(region, "isProductionLimited", [g]), bridge.call_function(region, "getProductionLimit", [g, -1])])
        ctx.time.run_game_seconds(40, speed=3)
        for good in goods:
            attempt(ctx, f"after 1 day {good}", lambda g=good: [bridge.call_function(region, "isProductionLimited", [g]), bridge.call_function(region, "getProductionLimit", [g, -1])])
            attempt(ctx, f"unlimit {good}", lambda g=good: bridge.call_function(region, "setProductionUnlimited", [g]))
            attempt(ctx, f"after unlimit {good}", lambda g=good: [bridge.call_function(region, "isProductionLimited", [g]), bridge.call_function(region, "getProductionLimit", [g, -1])])
    return ctx.result()
