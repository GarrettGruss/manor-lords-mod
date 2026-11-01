"""Probe for the spike rich-game-detection: can Lua read the game area (current/max) or its rich flag?

Research tool, hidden, read only. It never calls a save function and never reads soft object structs.
Steps (env HARNESS_PROBE): funcs, comps, compare, hook.
"""

import json
import os
import time

NAME = "probe-rich-game"
LIMIT_S = 300
HIDDEN = True
TIP_WORDS = ("tip", "hover", "info", "text", "desc", "select", "target", "focus", "animal", "game", "hunt", "herd", "rich", "count", "capacity", "spawn")


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:3000]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:500])
        return None
    note(ctx, step, result=result)
    return result


def opath(ref) -> str:
    from runlib.bridge_client import object_path
    return object_path(ref)


def deer_nodes(ctx):
    """Return (path, decal path, location) for each deer node."""
    bridge = ctx.bridge
    out = []
    for ref in bridge._result("objects", class_name="ResourceNode", limit=100)["objects"]:  # noqa: SLF001
        path = opath(ref)
        dec = opath(bridge.read_property(path, "ResourceZoneDecal"))
        if "deer" not in str(bridge.call_function(dec, "GetDecalMaterial", [])):
            continue
        out.append((path, dec, bridge.call_function(dec, "K2_GetComponentLocation", [])))
    return out


def region_name(ctx, loc) -> str:
    bridge = ctx.bridge
    region = bridge.call_function(bridge.engine_path(), "getRegionByPos", [{"X": loc["X"], "Y": loc["Y"], "Z": loc["Z"]}, True])
    return str(bridge.call_function(opath(region), "getRegionName", []))


def run(ctx) -> dict:
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    step = os.environ.get("HARNESS_PROBE", "funcs")
    nodes = deer_nodes(ctx)
    names = {path: region_name(ctx, loc) for path, _dec, loc in nodes}
    note(ctx, "deer nodes", nodes=[(p[-26:], names[p], round(l["X"]), round(l["Y"])) for p, _d, l in nodes])
    first = nodes[0][0]
    if step == "funcs":
        funcs = attempt(ctx, "node funcs", lambda: [f"{f['owner']}:{f['name']}" for f in res("funcs", ref=first)])
        attempt(ctx, "node class", lambda: str(bridge.call_function(first, "GetClass", []))[:200])
        ui = opath(res("objects", class_name="MainUICPP_C", limit=1)["objects"][0])
        attempt(ctx, "ui funcs", lambda: [f"{f['owner']}:{f['name']}" for f in res("funcs", ref=ui) if any(w in f["name"].lower() for w in TIP_WORDS)])
        attempt(ctx, "ui props", lambda: [f"{p['name']}:{p['type']}" for p in res("props", ref=ui, include_super=False, read_soft=False)["properties"] if any(w in p["name"].lower() for w in TIP_WORDS)])
        player = bridge.player_path()
        attempt(ctx, "player funcs", lambda: [f"{f['owner']}:{f['name']}" for f in res("funcs", ref=player) if any(w in f["name"].lower() for w in TIP_WORDS)])
        attempt(ctx, "player props", lambda: [f"{p['name']}:{p['type']}" for p in res("props", ref=player, include_super=True, read_soft=False)["properties"] if any(w in p["name"].lower() for w in TIP_WORDS)])
        engine = bridge.engine_path()
        attempt(ctx, "engine funcs", lambda: [f"{f['owner']}:{f['name']}" for f in res("funcs", ref=engine) if any(w in f["name"].lower() for w in TIP_WORDS) and f["owner"] != "Actor"])
        attempt(ctx, "engine props", lambda: [f"{p['name']}:{p['type']}" for p in res("props", ref=engine, include_super=True, read_soft=False)["properties"] if any(w in p["name"].lower() for w in TIP_WORDS)])
        note(ctx, "done", n=len(funcs or []))
    if step == "comps":
        prefix = first.split(".")[-1] if "." in first else first
        for cls in ("ActorComponent",):
            attempt(ctx, f"{names[first]} {cls}", lambda c=cls: [str(o)[:160] for o in res("objects", class_name=c, limit=5000)["objects"] if prefix in str(o)])
    if step == "compare":
        for path, dec, _loc in nodes:
            props = res("props", ref=path, include_super=True, read_soft=False)["properties"]
            note(ctx, "node all props " + names[path], props={p["name"]: str(p.get("value"))[:100] for p in props})
            dprops = res("props", ref=dec, include_super=True, read_soft=False)["properties"]
            note(ctx, "decal all props " + names[path], props={p["name"]: str(p.get("value"))[:100] for p in dprops})
    if step == "lairs":
        lairs(ctx)
    if step == "deer":
        deer(ctx, nodes, names)
    if step == "widgets":
        widgets(ctx)
    if step == "hook":
        hover_rich(ctx, nodes, names)
    return ctx.result()


def hover_rich(ctx, nodes, names) -> None:
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    labels = [s for s in os.environ.get("HARNESS_HOOKS", "").split(";") if s]
    for fn in labels:
        attempt(ctx, "hook " + fn, lambda f=fn: res("hook", function=f, label=f.split(":")[-1], max_args=6))
    for path, dec, loc in nodes:
        ctx.pause()
        if names[path] not in os.environ.get("HARNESS_REGIONS", "Riesenbuckel,Hochweg"):
            continue
        bridge.centre_camera_on(loc["X"], loc["Y"])
        time.sleep(1.5)
        seen = []
        for fx, fy in ((0.5, 0.5), (0.45, 0.5), (0.55, 0.5), (0.5, 0.45), (0.5, 0.55)):
            ctx.hover_with_mouse(fx, fy)
            time.sleep(0.6)
            try:
                ui = opath(res("objects", class_name="MainUICPP_C", limit=1)["objects"][0])
                text = str(bridge.read_property(opath(bridge.read_property(ui, "WhiteTooltipRT")), "Text"))[:200]
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive("tip")
                text = "err " + str(error)[:60]
            direct = {}
            for target, fn in ((bridge.player_path(), "getSmallTooltip"), (ui, "whiteTooltip")):
                try:
                    direct[fn] = str(bridge.call_function(target, fn, []))[:200]
                except Exception as error:  # noqa: BLE001
                    ctx.ensure_alive(fn)
                    direct[fn] = "err " + str(error)[:80]
            try:
                direct["target"] = str(res("target", distance=300000))[:300]
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive("target")
            note(ctx, "hover point " + names[path], fx=fx, fy=fy, text=text, direct=direct)
            if text and text not in seen:
                seen.append(text)
        ctx.screenshot("hover-" + names[path].replace(" ", "_"))
        note(ctx, "hover " + names[path], texts=seen)
    attempt(ctx, "events", lambda: res("events", since=0, limit=300))


def widgets(ctx) -> None:
    """Unique widget classes alive (the paw icon over a deer area may be a widget that holds the numbers)."""
    res = ctx.bridge._result  # noqa: SLF001
    objs = res("objects", class_name="UserWidget", limit=5000)["objects"]
    classes = {}
    for obj in objs:
        cls = str(obj).split(" ")[0].replace("{'__object':", "").strip("' ")
        classes[cls] = classes.get(cls, 0) + 1
    note(ctx, "widget classes", classes=classes)


def deer(ctx, nodes, names) -> None:
    """Call getDeerLairLocations and compare with the deer node positions."""
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    engine = bridge.engine_path()
    attempt(ctx, "funcs sig", lambda: [str(f) for f in res("funcs", ref=engine) if "DeerLair" in f["name"]])
    attempt(ctx, "getDeerLairLocations", lambda: str(bridge.call_function(engine, "getDeerLairLocations", []))[:2500])
    for path, _dec, loc in nodes:
        attempt(ctx, "lairs " + names[path], lambda l=loc: str(bridge.call_function(engine, "getDeerLairLocations", [{"X": l["X"], "Y": l["Y"], "Z": l["Z"]}]))[:1500])


def lairs(ctx) -> None:
    """Try class names around AffectAnimalLairs, and read the pawn function list for animal words."""
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    for name in ("AnimalLair", "AnimalLairCPP", "Lair", "AnimalLairActor", "BP_AnimalLair_C", "AnimalSpawnPoint", "HuntingGroundCPP", "AnimalCPP", "SMAnimal", "AnimalUnit", "SMAnimalUnit", "SMLivestock"):
        attempt(ctx, "class " + name, lambda n=name: len(res("objects", class_name=n, limit=100)["objects"]))
    for target, label in ((bridge.player_path(), "player"), (bridge.engine_path(), "engine")):
        attempt(ctx, label + " animal funcs", lambda t=target: [f"{f['owner']}:{f['name']}" for f in res("funcs", ref=t) if any(w in f["name"].lower() for w in ("animal", "lair", "wild", "deer", "hunt"))])
        attempt(ctx, label + " animal props", lambda t=target: [f"{p['name']}:{p['type']}" for p in res("props", ref=t, include_super=True, read_soft=False)["properties"] if any(w in p["name"].lower() for w in ("animal", "lair", "wild", "deer", "hunt"))])
