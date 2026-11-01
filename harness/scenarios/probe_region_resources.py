"""Probe for the spike region-rich-resources: where does a region keep its rich deposits?

Research tool, hidden, read only. It never calls a save function and never reads soft object structs.
"""

import json
import os

NAME = "probe-region-resources"
LIMIT_S = 300
HIDDEN = True
WORDS = ("res", "deposit", "rich", "fertil", "farm", "iron", "clay", "stone", "salt", "berr", "game", "fish", "ore", "soil", "yield", "special")


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


def run(ctx) -> dict:
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    engine = bridge.engine_path()
    step = os.environ.get("HARNESS_PROBE", "names")
    regions = bridge.region_paths(engine)
    note(ctx, "regions", count=len(regions), paths=[r[-40:] for r in regions])
    first = regions[0]
    if step == "names":
        props = res("props", ref=first, include_super=True, read_soft=False)["properties"]
        note(ctx, "region props", props=[f"{p['name']}:{p['type']}" for p in props])
        attempt(ctx, "region funcs", lambda: [f["name"] for f in res("funcs", ref=first) if f["owner"] == "Region"])
        eprops = res("props", ref=engine, include_super=True, read_soft=False)["properties"]
        note(ctx, "engine matching", props=[f"{p['name']}:{p['type']}" for p in eprops if any(w in p["name"].lower() for w in WORDS)])
        attempt(ctx, "engine funcs", lambda: [f["name"] for f in res("funcs", ref=engine) if any(w in f["name"].lower() for w in WORDS) and f["owner"] != "Actor"])
    if step == "values":
        for path in regions:
            props = res("props", ref=path, include_super=False, read_soft=False)["properties"]
            note(ctx, "region values", path=path[-30:], props={p["name"]: str(p.get("value"))[:200] for p in props})
    if step == "table":
        table(ctx, regions)
    if step == "sweep":
        sweep(ctx, regions)
    if step == "hover":
        hover(ctx, regions)
    if step == "decal":
        decal(ctx, regions)
    if step == "food":
        food(ctx, regions)
    if step == "animals":
        animals(ctx, regions)
    if step == "foodhover":
        foodhover(ctx, regions)
    if step == "deep":
        deep(ctx, regions)
    return ctx.result()


def deep(ctx, regions) -> None:
    from runlib.bridge_client import object_path
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    for path in regions:
        for fn in ("getCropTypes", "GetEnviromentProportions", "hasWeakFertility", "getRegionName", "isMapBorderRegion"):
            attempt(ctx, f"{path[-12:]} {fn}", lambda p=path, f=fn: bridge.call_function(p, f, []))
    nodes = [object_path(r) for r in res("objects", class_name="ResourceNode", limit=100)["objects"]]
    for path in nodes[:3]:
        props = res("props", ref=path, include_super=False, read_soft=False)["properties"]
        note(ctx, "node props", path=path[-30:], props={p["name"]: str(p.get("value"))[:160] for p in props})
    for path in nodes:
        row = {}
        for name in ("masterPtr", "ResourceZoneDecal", "PaperMapDecal", "resourceClumps"):
            try:
                row[name] = str(bridge.read_property(path, name))[:160]
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive(name)
                row[name] = "err " + str(error)[:60]
        try:
            row["loc"] = str(bridge.call_function(path, "K2_GetActorLocation", []))
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("loc")
            row["loc"] = "err " + str(error)[:60]
        note(ctx, "node", path=path[-26:], **row)
    for name in ("resourceZoneMaterials", "paperMapResourceMaterials"):
        attempt(ctx, name, lambda n=name: str(bridge.read_property(bridge.engine_path(), n))[:1500])


def short(value) -> str:
    return str(value)[:140]


def decal(ctx, regions) -> None:
    from runlib.bridge_client import object_path
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    for path in regions:
        row = {}
        for fn in ("getSettledRegionCenter", "K2_GetActorLocation"):
            try:
                row[fn] = short(bridge.call_function(path, fn, []))
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive(fn)
                row[fn] = "err " + str(error)[:60]
        try:
            row["town"] = short(bridge.read_property(path, "townCenter"))
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("town")
        note(ctx, "region pos", path=path[-12:], **row)
    nodes = [object_path(r) for r in res("objects", class_name="ResourceNode", limit=100)["objects"]]
    for path in nodes:
        row = {}
        clumps = bridge.read_property(path, "resourceClumps")
        row["clumps"] = [str(c.get("__object", c)).split(" ")[0] for c in clumps][:3] if isinstance(clumps, list) else short(clumps)
        row["n_clumps"] = len(clumps) if isinstance(clumps, list) else -1
        try:
            dec = object_path(bridge.read_property(path, "ResourceZoneDecal"))
            row["dec_loc"] = short(bridge.call_function(dec, "K2_GetComponentLocation", []))
            row["dec_mat"] = short(bridge.call_function(dec, "GetDecalMaterial", []))
            row["dec_size"] = short(bridge.read_property(dec, "DecalSize"))
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("decal")
            row["err"] = str(error)[:80]
        note(ctx, "node", path=path[-10:], **row)


def tooltip_text(ctx) -> str:
    bridge = ctx.bridge
    ui = object_path_of(bridge._result("objects", class_name="MainUICPP_C", limit=1)["objects"][0])  # noqa: SLF001
    widget = bridge.read_property(ui, "WhiteTooltipRT")
    return str(bridge.read_property(object_path_of(widget), "Text"))[:300]


def object_path_of(ref) -> str:
    from runlib.bridge_client import object_path
    return object_path(ref)


def hover(ctx, regions) -> None:
    import time
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    nodes = [object_path_of(r) for r in res("objects", class_name="ResourceNode", limit=100)["objects"]]
    attempt(ctx, "tooltip idle", lambda: tooltip_text(ctx))
    for path in nodes:
        clumps = bridge.read_property(path, "resourceClumps")
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        mat = str(bridge.call_function(dec, "GetDecalMaterial", []))
        if clumps and "Stone" not in str(clumps[0]):
            continue
        loc = bridge.call_function(dec, "K2_GetComponentLocation", [])
        size = bridge.read_property(dec, "DecalSize")["X"]
        name = mat.split("/")[-1][:40] if "invalid" not in mat else "clump"
        try:
            bridge.centre_camera_on(loc["X"], loc["Y"])
            time.sleep(1.5)
            ctx.hover_with_mouse(0.5, 0.5)
            time.sleep(1.5)
            text = tooltip_text(ctx)
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("hover")
            text = "err " + str(error)[:100]
        note(ctx, "hover", node=path[-10:], mat=name, size=size, loc=[round(loc["X"]), round(loc["Y"])], text=text)


def table(ctx, regions) -> None:
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    engine = bridge.engine_path()
    for path in regions:
        row = {"weak_fertility": bridge.call_function(path, "hasWeakFertility", []), "name": bridge.call_function(path, "getRegionName", [])}
        for fn in ("GetAffinitiesConnectedWithEnvironment", "getPredictedHarvestForGoodType"):
            try:
                row[fn] = short(bridge.call_function(path, fn, [] if fn.startswith("Get") else [1]))
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive(fn)
                row[fn] = "err " + str(error)[:60]
        note(ctx, "region", path=path[-12:], **row)
    nodes = [object_path_of(r) for r in res("objects", class_name="ResourceNode", limit=100)["objects"]]
    for path in nodes:
        clumps = bridge.read_property(path, "resourceClumps")
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        mat = str(bridge.call_function(dec, "GetDecalMaterial", []))
        size = bridge.read_property(dec, "DecalSize")["X"]
        loc = bridge.call_function(dec, "K2_GetComponentLocation", [])
        kind = str(clumps[0]).split(" ")[0].replace("{'__object':", "").strip() if clumps else mat.split("/")[-1].split(".")[0]
        try:
            owner = short(bridge.call_function(engine, "getRegionByPos", [{"X": loc["X"], "Y": loc["Y"], "Z": loc["Z"]}, True]))
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("regionbypos")
            owner = "err " + str(error)[:80]
        note(ctx, "node", id=path[-10:], kind=kind, size=size, n=len(clumps), loc=[round(loc["X"]), round(loc["Y"])], region=owner)


def sweep(ctx, regions) -> None:
    import time
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    nodes = [object_path_of(r) for r in res("objects", class_name="ResourceNode", limit=100)["objects"]]
    for path in nodes:
        clumps = bridge.read_property(path, "resourceClumps")
        if clumps:
            continue
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        mat = str(bridge.call_function(dec, "GetDecalMaterial", []))
        size = bridge.read_property(dec, "DecalSize")["X"]
        if size != 5000 or "deer" in mat:
            continue
        loc = bridge.call_function(dec, "K2_GetComponentLocation", [])
        name = mat.split("/")[-1][:30]
        try:
            bridge.centre_camera_on(loc["X"], loc["Y"])
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("cam")
            note(ctx, "sweep", node=path[-10:], err=str(error)[:80])
            continue
        time.sleep(1.0)
        seen = []
        for fy in (0.4, 0.5, 0.6):
            for fx in (0.4, 0.5, 0.6):
                ctx.hover_with_mouse(fx, fy)
                time.sleep(0.6)
                text = tooltip_text(ctx)
                if text and text not in seen:
                    seen.append(text)
        note(ctx, "sweep", node=path[-10:], mat=name, loc=[round(loc["X"]), round(loc["Y"])], texts=seen)


def clump_class(clump) -> str:
    import re
    match = re.search(r"'(\w+) /", str(clump))
    return match.group(1) if match else "?"


def food_nodes(ctx):
    from runlib.bridge_client import object_path
    bridge = ctx.bridge
    return [object_path(r) for r in bridge._result("objects", class_name="ResourceNode", limit=100)["objects"]]  # noqa: SLF001


def region_name_at(ctx, loc) -> str:
    bridge = ctx.bridge
    try:
        region = bridge.call_function(bridge.engine_path(), "getRegionByPos", [{"X": loc["X"], "Y": loc["Y"], "Z": loc["Z"]}, True])
        return str(bridge.call_function(object_path_of(region), "getRegionName", []))
    except Exception as error:  # noqa: BLE001
        ctx.ensure_alive("region")
        return "err " + str(error)[:60]


def food(ctx, regions) -> None:
    """One row per node with clump totals, decal data and region. Also the Resource and node properties once."""
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    nodes = food_nodes(ctx)
    for name in ("Resource_Fish_C", "Resource_Berries_C"):
        objs = res("objects", class_name=name, limit=1)["objects"]
        if objs:
            props = res("props", ref=object_path_of(objs[0]), include_super=True, read_soft=False)["properties"]
            note(ctx, "resource props " + name, props={p["name"]: str(p.get("value"))[:100] for p in props})
    for path in nodes:
        clumps = bridge.read_property(path, "resourceClumps")
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        mat = str(bridge.call_function(dec, "GetDecalMaterial", []))
        size = bridge.read_property(dec, "DecalSize")
        loc = bridge.call_function(dec, "K2_GetComponentLocation", [])
        kinds = {}
        for clump in clumps or []:
            cpath = object_path_of(clump)
            cls = clump_class(clump)
            amt = capacity = -1
            try:
                amt = bridge.read_property(cpath, "amt")
                capacity = bridge.read_property(cpath, "capacity")
            except Exception:  # noqa: BLE001
                ctx.ensure_alive("clump")
            row = kinds.setdefault(cls, {"n": 0, "amt": 0, "cap": 0})
            row["n"] += 1
            row["amt"] += amt
            row["cap"] += capacity
        note(ctx, "food node", id=path[-10:], mat=mat.split("/")[-1][:30], size=size, loc=[round(loc["X"]), round(loc["Y"])], region=region_name_at(ctx, loc), kinds=kinds)
    props = res("props", ref=nodes[0], include_super=False, read_soft=False)["properties"]
    note(ctx, "node props", props={p["name"]: str(p.get("value"))[:80] for p in props})


def animals(ctx, regions) -> None:
    """Look for the object that holds the wild animal count and its maximum."""
    bridge = ctx.bridge
    res = bridge._result  # noqa: SLF001
    for name in ("Deer", "Animal", "WildAnimal", "AnimalSpawner", "HuntingGround", "Wildlife", "DeerCPP", "BP_Deer_C", "HuntingZone", "AnimalHerd", "Herd"):
        attempt(ctx, "class " + name, lambda n=name: len(res("objects", class_name=n, limit=100)["objects"]))
    for path in food_nodes(ctx):
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        if "deer" not in str(bridge.call_function(dec, "GetDecalMaterial", [])):
            continue
        props = res("props", ref=path, include_super=True, read_soft=False)["properties"]
        note(ctx, "deer node", props={p["name"]: str(p.get("value"))[:120] for p in props if not p["name"].startswith("b") and not p["name"].startswith("On")})
        for fn in ("getMaster", "GetOverlappingActors"):
            attempt(ctx, "deer " + fn, lambda f=fn, p=path: str(bridge.call_function(p, f, []))[:300])
        break
    for path in food_nodes(ctx):
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        if "deer" not in str(bridge.call_function(dec, "GetDecalMaterial", [])):
            continue
        row = {"loc": str(bridge.call_function(dec, "K2_GetComponentLocation", []))[:80]}
        for fn in ("K2_GetComponentScale",):
            attempt(ctx, "x", lambda: 0)
            try:
                row[fn] = str(bridge.call_function(dec, fn, []))[:120]
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive(fn)
                row[fn] = "err"
        for name in ("RelativeScale3D", "DecalSize", "FadeScreenSize", "SortOrder", "FadeStartDelay"):
            try:
                row[name] = str(bridge.read_property(dec, name))[:100]
            except Exception:  # noqa: BLE001
                ctx.ensure_alive(name)
        try:
            row["actor_scale"] = str(bridge.call_function(path, "GetActorScale3D", []))[:100]
        except Exception:  # noqa: BLE001
            ctx.ensure_alive("scale")
        note(ctx, "deer decal", **row)
    for fn in ("GetWildAnimals", "getWildAnimalCount", "GetAnimals"):
        attempt(ctx, "engine " + fn, lambda f=fn: str(bridge.call_function(bridge.engine_path(), f, []))[:200])


def foodhover(ctx, regions) -> None:
    import time
    bridge = ctx.bridge
    attempt(ctx, "tooltip idle", lambda: tooltip_text(ctx))
    for path in food_nodes(ctx):
        clumps = bridge.read_property(path, "resourceClumps")
        dec = object_path_of(bridge.read_property(path, "ResourceZoneDecal"))
        mat = str(bridge.call_function(dec, "GetDecalMaterial", []))
        deer = "deer" in mat
        kinds = {clump_class(c) for c in clumps or []}
        if not (deer or any(k in " ".join(kinds) for k in ("Berries", "Fish", "Eel", "Mushrooms"))):
            continue
        points = [bridge.call_function(dec, "K2_GetComponentLocation", [])]
        only = os.environ.get("HARNESS_LOCS")
        if only:
            wanted = [tuple(int(v) for v in item.split(",")) for item in only.split(";")]
            if not any(abs(points[0]["X"] - x) < 60 and abs(points[0]["Y"] - y) < 60 for x, y in wanted):
                continue
        for clump in (clumps or [])[:3]:
            try:
                points.append(bridge.call_function(object_path_of(clump), "K2_GetActorLocation", []))
            except Exception:  # noqa: BLE001
                ctx.ensure_alive("clumploc")
        texts = []
        for loc in points:
            try:
                bridge.centre_camera_on(loc["X"], loc["Y"])
                time.sleep(1.2)
                seen = []
                for fx, fy in ((0.5, 0.5), (0.45, 0.5), (0.55, 0.5), (0.5, 0.45), (0.5, 0.55)):
                    ctx.hover_with_mouse(fx, fy)
                    time.sleep(0.5)
                    text = tooltip_text(ctx)
                    if text and text not in seen:
                        seen.append(text)
                texts.append({"loc": [round(loc["X"]), round(loc["Y"])], "texts": seen})
            except Exception as error:  # noqa: BLE001
                ctx.ensure_alive("hover")
                texts.append("err " + str(error)[:80])
        note(ctx, "foodhover", node=path[-10:], kinds=sorted(kinds), deer=deer, size=bridge.read_property(dec, "DecalSize"), hovers=texts)
