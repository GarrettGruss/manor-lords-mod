"""Probe for the change spike-raid-skill-near-enemy (issue #495).

Research tool, not in the regular suite:
    uv run python harness\run.py --scenario probe-raid-near --fixture playtest-noai --slot auto
Environment switches:
  HARNESS_PROBE_TARGET  camp (bandit camp, brigands killed) or village (a new AI lord at war founds a village)
  HARNESS_PROBE_FLAG    false or true: last argument of SquadComponent:SetSkillActive(handle, 19, true, flag); none: control, no skill call
  HARNESS_PROBE_MODE    near (squad spawns at the camera next to the target), click (plus one real right click), walk (squad from the village)
  HARNESS_PROBE_BUILD_DAYS, HARNESS_PROBE_SUPPLY, HARNESS_PROBE_OFFSET, HARNESS_PROBE_STEPS  village build time, supply, spawn offset, watch steps
A player squad stands next to a hostile building, skill 19 is on, the probe watches, switches it off and watches again.
It never calls a save function and never reads Squad structs. It reads building masters with structured bridge ops only.
"""

import json
import os

NAME = "probe-raid-near"
LIMIT_S = 1500
EXCLUSIVE = True  # real mouse input in walk mode
HIDDEN = True
LONG_REASON = "The probe watches a squad for several game minutes."
SPEED = 3
SKILL = 19
TEMPLATE = "spearMilitia"
NEAR_OFFSET = int(os.environ.get("HARNESS_PROBE_OFFSET", "1500"))
WATCH_ON_STEPS = int(os.environ.get("HARNESS_PROBE_STEPS", "18"))
WATCH_OFF_STEPS = 4
STEP_GAME_S = 10
SQUAD_COMPONENT = "first:SquadComponent"


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        entry = {"step": step, **data}
        self.ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1800]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(self, step: str, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            self.note(step, error=str(error)[:600])
            return None
        self.note(step, result=result)
        return result


def distance(a: dict | None, b: dict | None):
    if not a or not b:
        return None
    return round(((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5)


def site_point(site: dict) -> dict | None:
    at = site.get("at") or site.get("location")
    if not isinstance(at, dict):
        return None
    return {"x": at.get("x", at.get("X")), "y": at.get("y", at.get("Y"))}


def prepare_camp(probe: Probe) -> dict | None:
    actions = probe.ctx.actions
    probe.attempt("spawn camp", actions.spawn_bandit_camp)
    probe.ctx.time.run_game_seconds(3, speed=SPEED)
    sites = (probe.attempt("camp sites", actions.encampment_sites) or {}).get("sites", [])
    camp = site_point(sites[0]) if sites else None
    if camp:
        probe.attempt("kill brigands", lambda: actions.kill_units("bandit", 18))
    return camp


def prepare_village(probe: Probe) -> dict | None:
    """A new AI lord at war with the player founds a village in the free region nearest to the player village."""
    ctx, actions = probe.ctx, probe.ctx.actions
    regions = (probe.attempt("regions", actions.encampment_regions) or {}).get("regions", [])
    player_at = ctx.bridge.call_function(ctx.bridge.player_path(), "K2_GetActorLocation")
    free = [r for r in regions if r.get("owner") == "<invalid>" and not r.get("settled") and r.get("at")]
    free.sort(key=lambda r: (r["at"]["x"] - player_at["X"]) ** 2 + (r["at"]["y"] - player_at["Y"]) ** 2)
    if not free:
        return None
    region = free[0]
    build_days = int(os.environ.get("HARNESS_PROBE_BUILD_DAYS", "0"))
    lord = (probe.attempt("spawn lord", lambda: actions.spawn_ai_lord("Raid Target Lord", can_build=build_days > 0)) or {}).get("lord")
    if lord is None:
        return None
    probe.attempt("relations", lambda: actions.lord_relations(lord))
    probe.attempt("found village", lambda: actions.lord_found_village(lord, region["region"], supply=int(os.environ.get("HARNESS_PROBE_SUPPLY", "0"))))
    probe.attempt("declare war", lambda: actions.lord_declare_war(lord, 0))
    if build_days > 0:
        probe.attempt("start ai", lambda: actions.lord_start_ai(lord, 1, can_build=True))
        probe.attempt("build days", lambda: ctx.time.run_game_days(build_days, speed=SPEED))
    ctx.time.run_game_seconds(10, speed=SPEED)
    rows = enemy_buildings(probe, "village buildings") or []
    built = [row for row in rows if row.get("built") and row.get("x") is not None and (row["x"], row["y"]) != (0, 0)]
    if built:
        return {"x": built[0]["x"], "y": built[0]["y"]}
    probe.attempt("regions after", lambda: [r for r in actions.regions_state().get("regions", []) if r.get("region") == region["region"] or r.get("name") == region["name"]])
    return region.get("town_center_at") or region["at"]


def enemy_buildings(probe: Probe, label: str):
    """Building masters of other pawns: name, owner, region, position. Structured ops only (no eval, no Data struct)."""
    from ue4ss_bridge import server
    bridge = probe.ctx.bridge
    try:
        found = server.one("objects", class_name="SMBuildingMaster", limit=600)["result"]["objects"]
        paths = [entry.split(" ", 1)[1] for entry in found if "Default__" not in entry]
        calls = []
        for path in paths:
            calls.append({"op": "get", "ref": path, "name": "ownerPawn"})
            calls.append({"op": "get", "ref": path, "name": "Region"})
            calls.append({"op": "call", "ref": path, "function": "K2_GetActorLocation", "args": []})
            calls.append({"op": "call", "ref": path, "function": "IsConstructed", "args": []})
        answers = server.batch(calls)
    except Exception as error:  # noqa: BLE001
        probe.ctx.ensure_alive(label)
        probe.note(label, error=str(error)[:400])
        return None
    player = bridge.player_path()
    rows = []
    for index, path in enumerate(paths):
        owner, region, where, built = (answers[4 * index + k].get("result") for k in range(4))
        owner_text = owner.get("__object", "") if isinstance(owner, dict) else str(owner)
        if owner_text.endswith("<invalid>") or (player.split(".")[-1] and player.split(".")[-1] in owner_text):
            continue
        rows.append({"b": path.split(".")[-1], "owner": owner_text.split(".")[-1], "region": (region or {}).get("__object", "").split(".")[-1] if isinstance(region, dict) else None,
                     "x": round(where["X"]) if isinstance(where, dict) else None, "y": round(where["Y"]) if isinstance(where, dict) else None, "built": built})
    probe.note(label, total_masters=len(paths), other_owner=len(rows), rows=rows[:40])
    return rows


def skill_reads(probe: Probe, squad: int) -> dict:
    bridge = probe.ctx.bridge
    handle = {"Value": squad}
    return {
        "active": probe.attempt("IsSkillActiveForSquad", lambda: bridge.call_function(SQUAD_COMPONENT, "IsSkillActiveForSquad", [handle, SKILL])),
        "any_raiding": probe.attempt("isAnySquadRaiding", lambda: bridge.call_function(bridge.player_path(), "isAnySquadRaiding", [{}])),
    }


def watch(probe: Probe, label: str, squad: int, camp: dict | None, steps: int) -> None:
    ctx, actions = probe.ctx, probe.ctx.actions
    for step in range(1, steps + 1):
        ctx.time.run_game_seconds(STEP_GAME_S, speed=SPEED)
        state = actions.steer_state(squad)
        sites = actions.encampment_sites().get("sites", [])
        probe.note(f"{label} {step}", game_s=step * STEP_GAME_S, center=state.get("center"), units=state.get("units"),
                   target_mean=state.get("target_mean"), distance_to_camp=distance(state.get("center"), camp),
                   camp_sites=[{"parts": s.get("parts"), "owner": s.get("owner"), "region": s.get("region")} for s in sites],
                   **skill_reads(probe, squad))
        if step in (1, steps // 2, steps):
            if state.get("center"):
                probe.attempt("camera on squad", lambda: ctx.bridge.centre_camera_on(state["center"]["x"], state["center"]["y"], tries=4))
            ctx.screenshot(f"{label}-{step}")


def run(ctx) -> dict:
    probe = Probe(ctx)
    actions = ctx.actions
    flag_text = os.environ.get("HARNESS_PROBE_FLAG", "false").lower()
    control = flag_text == "none"
    flag = flag_text == "true"
    mode = os.environ.get("HARNESS_PROBE_MODE", "near")
    target_kind = os.environ.get("HARNESS_PROBE_TARGET", "camp")
    camp = prepare_camp(probe) if target_kind == "camp" else prepare_village(probe)
    if not camp:
        return ctx.fail("target", "no hostile building target")
    if mode in ("near", "click"):
        probe.attempt("camera", lambda: ctx.bridge.centre_camera_on(camp["x"] - NEAR_OFFSET, camp["y"], tries=6))
    spawned = probe.attempt("spawn squad", lambda: actions.spawn_units("player", TEMPLATE))
    squad = spawned["answer"]["squads"][0]["id"] if spawned else None
    if squad is None:
        return ctx.fail("squad", "no squad")
    ctx.time.run_game_seconds(3, speed=SPEED)
    state = probe.attempt("state start", lambda: actions.steer_state(squad))
    probe.note("start", camp=camp, distance=distance((state or {}).get("center"), camp))
    handle = {"Value": squad}
    bridge = ctx.bridge
    probe.attempt("available", lambda: bridge.call_function(SQUAD_COMPONENT, "isSkillAvailableForSquad", [handle, SKILL, {}]))
    if mode in ("walk", "click"):
        probe.attempt("select", lambda: actions.steer_select(squad))
        center = state["center"]
        step_x = camp["x"] - center["x"]
        step_y = camp["y"] - center["y"]
        length = max(1.0, (step_x ** 2 + step_y ** 2) ** 0.5)
        reach = 600 if mode == "click" else length - NEAR_OFFSET
        target = {"x": center["x"] + reach * step_x / length, "y": center["y"] + reach * step_y / length}
        ctx.unpause()
        ctx.time.set_speed(SPEED)
        probe.attempt("cursor", lambda: actions.steer_cursor(target["x"], target["y"], center.get("z") or 0))
        probe.attempt("right click", ctx.order_with_mouse)
        ctx.pause()
        watch(probe, "walk", squad, camp, 6 if mode == "click" else 40)
    ctx.screenshot("before-skill")
    enemy_buildings(probe, "enemy buildings before")
    if not control:
        probe.attempt("skill on", lambda: bridge.call_function(SQUAD_COMPONENT, "SetSkillActive", [handle, SKILL, True, flag]))
    watch(probe, "on", squad, camp, WATCH_ON_STEPS)
    if not control:
        probe.attempt("skill off", lambda: bridge.call_function(SQUAD_COMPONENT, "SetSkillActive", [handle, SKILL, False, flag]))
    enemy_buildings(probe, "enemy buildings after on")
    watch(probe, "off", squad, camp, WATCH_OFF_STEPS)
    return ctx.result()
