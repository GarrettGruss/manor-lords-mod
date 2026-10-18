"""Probe for spec 30: can a Wagenburg mesh stand in for the bandit camp, or be spawned in neutral and AI territory? Research tool, not a test.

Run with the pak that holds BM_Wagenburg (option HARNESS_BM=<asset> uses another Blueprint of the pak) (row 100 points at it, row 4000 is a clone of the tent):
  run.py --scenario probe-wagenburg --fixture base --pak wagen --slot auto
Host a: the game spawns a bandit camp (spawn_bandit_camp). The probe reads the camp master, its parts and the bandit units.
Host c: the probe spawns the Blueprint class as a plain actor in a neutral region and in an AI-owned region.
No eval. No save function. The probe destroys only actors it spawned itself.
"""

import json

NAME = "probe-wagenburg"
LIMIT_S = 420
HIDDEN = True
LONG_REASON = "The probe spawns a camp, moves the camera to three places and takes screenshots."
DEFAULT_ASSET = "BM_Wagenburg"
CAMP_TYPE = 100
EXTRA_TYPE = 4000
PART_ROWS = 40


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


# Windows of other game runs can cover part of the game window (the screenshot copies screen pixels).
# Several aim points put the target in a different part of the picture each time.
AIM_OFFSETS = {"c": (0, 0), "n": (0, 1200), "s": (0, -1200)}


def look_at(ctx, step: str, x: float, y: float):
    ground = None
    for suffix, (dx, dy) in AIM_OFFSETS.items():
        found = attempt(ctx, f"camera {step}_{suffix}", lambda: ctx.bridge.centre_camera_on(x + dx, y + dy))
        ctx.screenshot(f"{step}_{suffix}")
        ground = ground or found
    return ground


def host_a(ctx) -> None:
    actions = ctx.actions
    attempt(ctx, "sites before", lambda: actions.encampment_sites(CAMP_TYPE))
    attempt(ctx, "spawn camp", actions.spawn_bandit_camp)
    ctx.time.run_game_days(1, speed=3)
    after = attempt(ctx, "sites after", lambda: actions.encampment_sites(CAMP_TYPE))
    attempt(ctx, "camp parts", lambda: actions.master_parts(type_id=CAMP_TYPE, limit=PART_ROWS))
    attempt(ctx, "bandit state", actions.bandit_state)
    attempt(ctx, "census day 1", actions.units_census)
    ctx.time.run_game_days(2, speed=3)
    attempt(ctx, "bandit state day 3", actions.bandit_state)
    attempt(ctx, "census day 3", actions.units_census)
    attempt(ctx, "sites day 3", lambda: actions.encampment_sites(CAMP_TYPE))
    sites = (after or {}).get("sites") or []
    spot = sites and (sites[0].get("first_part_at") or sites[0].get("at"))
    if spot:
        look_at(ctx, "camp_near", spot["x"], spot["y"])


def host_c(ctx) -> None:
    actions = ctx.actions
    # HARNESS_BM names another Blueprint asset of the pak under test (spec 33 re-cook checks of other Meshy paks).
    pak_asset = ctx.variant_option("HARNESS_BM", DEFAULT_ASSET)
    class_path = f"/Game/HarnessMod/{pak_asset}.{pak_asset}_C"
    attempt(ctx, "load class", lambda: actions.load_pak_blueprint(pak_asset))
    regions = (attempt(ctx, "regions", actions.encampment_regions) or {}).get("regions") or []
    player = (attempt(ctx, "housing", actions.housing_state) or {}).get("region", {}).get("name")
    neutral = [r for r in regions if r["owner"] == "<invalid>" and r.get("at")]
    ai = [r for r in regions if r["owner"] not in ("<invalid>", "<unnamed>") and r["name"] != player and r.get("at")]
    targets = {"neutral": [neutral[0]] if neutral else [], "neutral2": neutral[1:2], "ai": ai[:1], "ai_centre": ai[:1], "ai2": ai[1:2]}
    for label, rows in targets.items():
        if not rows:
            note(ctx, f"spawn {label}", skipped="no such region")
            continue
        at = (rows[0].get("town_center_at") if label == "ai_centre" else None) or rows[0]["at"]
        ground = look_at(ctx, f"{label}_before", at["x"], at["y"]) or {}
        z = ground.get("Z", at["z"])
        note(ctx, f"ground {label}", ground=ground, region_z=at["z"], z=z)
        attempt(ctx, f"spawn {label}", lambda: actions.encampment_spawn(class_path, at["x"], at["y"], z))
        look_at(ctx, f"{label}_after", at["x"], at["y"])
    attempt(ctx, "spawned", actions.encampment_list)
    attempt(ctx, "stat extra row", lambda: actions.building_stat(EXTRA_TYPE))


def run(ctx) -> dict:
    attempt(ctx, "stat camp row", lambda: ctx.actions.building_stat(CAMP_TYPE))
    host_c(ctx)
    host_a(ctx)
    attempt(ctx, "remove spawned", ctx.actions.encampment_remove)
    return ctx.result()
