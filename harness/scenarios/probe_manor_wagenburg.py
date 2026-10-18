"""Probe for spec 32: does a built manor wall keep its collision and gate when its wall piece mesh is a wagon?

Research tool, not a test. Use fixture manor-closed (a built manor with a closed palisade ring and a gatehouse).
Steps:
  1. Read the wall piece actors (mesh PalisadeWallNarrow) and the gatehouse. Compute the ring centre, the polygon and the gate.
  2. Screenshots of the ring from three aim points.
  3. Bait: a player squad at the ring centre. Bandits: a squad outside, on the side opposite the gate.
  4. Track the bandit positions at speed 3. Write every sample to `track.jsonl`. Record when the first bandit is inside the ring and
     how far that bandit is from the gate then. A control run (no pak) and a pak run are compared with the same fixture.
Keep mode (HARNESS_KEEP=1, mouse-free): before the track, add a keep (type 57) with `manor_blueprint_add`, commit, feed the builders,
  wait until built (HARNESS_DAYS, default 30), then take close screenshots of the keep. Uses the helpers of probe-manor-flow.
Options (run.py --env): HARNESS_PATH (0 = skip the path test, the clock did not restart after a long build), HARNESS_KEEP, HARNESS_SPOT, HARNESS_MESH, HARNESS_DAYS, HARNESS_TRACK_S (game seconds to track, default 70), HARNESS_OUT_M (start distance outside the ring in metres, default 35).
No eval. No save function. The probe spawns only units and clears them at the end.
"""

import json
import math

from runlib import battle
from scenarios import probe_manor_flow as flow
from runlib.waiting import WaitTimeout

NAME = "probe-manor-wagenburg"
LIMIT_S = 1500
HIDDEN = True
LONG_REASON = "The probe tracks a bandit squad for 70 game seconds and takes screenshots."
WALL_MESH = "PalisadeWallNarrow"
GATE_MESH = "Gatehouse_Lv1"
KEEP_MESH = "MainTower_Lv1_New"
POLL_S = 0.5
TRACK_SPEED = 1
UNIT_CM = 100.0
SHOT_SAMPLES = (20, 40, 60)


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


def actors_of(ctx, mesh: str, owner: str | None = None) -> list[dict]:
    answer = ctx.commands.send("mesh_actors", mesh=mesh)
    rows = answer["actors"]
    note(ctx, f"mesh_actors {mesh}", total=answer["total"], shown=len(rows), owners=sorted({r["owner"] for r in rows}))
    return [r for r in rows if owner is None or r["owner"] == owner]


def inside(polygon: list[tuple[float, float]], x: float, y: float) -> bool:
    count, previous = False, polygon[-1]
    for current in polygon:
        (x1, y1), (x2, y2) = previous, current
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            count = not count
        previous = current
    return count


def ring_polygon(pieces: list[dict], centre: tuple[float, float]) -> list[tuple[float, float]]:
    ordered = sorted(pieces, key=lambda p: math.atan2(p["y"] - centre[1], p["x"] - centre[0]))
    return [(p["x"], p["y"]) for p in ordered]


def look(ctx, label: str, x: float, y: float) -> None:
    for suffix, (dx, dy) in {"c": (0, 0), "n": (0, 900), "s": (0, -900)}.items():
        attempt(ctx, f"camera {label}_{suffix}", lambda: ctx.bridge.centre_camera_on(x + dx, y + dy))
        ctx.screenshot(f"{label}_{suffix}")


class Track:
    def __init__(self, ctx, squad: int, polygon, gate, limit: int):
        self.ctx, self.squad, self.polygon, self.gate, self.limit = ctx, squad, polygon, gate, limit
        self.samples: list[dict] = []
        self.first_inside: dict | None = None
        self.path = ctx.run_dir / "track.jsonl"

    def __call__(self) -> bool:
        units = self.ctx.commands.send("squad_positions", squad=self.squad)["units"]
        flags = [inside(self.polygon, u["x"], u["y"]) for u in units]
        row = {"n": len(self.samples), "units": units, "inside": sum(flags)}
        self.samples.append(row)
        if row["n"] in SHOT_SAMPLES:
            self.ctx.screenshot(f"track_{row['n']}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row) + "\n")
        if self.first_inside is None and any(flags) and self.gate:
            near = min(math.hypot(u["x"] - self.gate["x"], u["y"] - self.gate["y"]) for u, f in zip(units, flags) if f)
            self.first_inside = {"sample": row["n"], "inside": row["inside"], "gate_distance_cm": round(near)}
        return len(self.samples) >= self.limit


WAGON_MESH = "/Game/HarnessMod/WagonM/SM_Wagon"
TENT_MESH = "/Game/HarnessMod/TentM/SM_KeepTent"


def lua_reskin(ctx, wall: bool, keep: bool) -> None:
    """Part 2: set the meshes of ONE manor from Lua (HarnessWagenburg). HARNESS_LUA_MANOR overrides the manor id (a wrong id must change nothing)."""
    state = attempt(ctx, "wagen_state before", lambda: ctx.commands.send("wagen_state"))
    manors = (state or {}).get("manors") or []
    manor = int(ctx.variant_option("HARNESS_LUA_MANOR", "0")) or (manors[0]["manor"] if manors else 0)
    fields = {"manor": manor}
    if wall:
        fields["wall_mesh"] = WAGON_MESH
    if keep:
        fields["keep_mesh"] = TENT_MESH
    answer = attempt(ctx, "wagen_apply", lambda: ctx.commands.send("wagen_apply", **fields))
    ctx.metric("lua_changed_wall", (answer or {}).get("changed", {}).get("wall", -1))
    ctx.metric("lua_changed_keep", (answer or {}).get("changed", {}).get("keep", -1))
    attempt(ctx, "wagen_state after", lambda: ctx.commands.send("wagen_state"))


def build_keep(ctx) -> None:
    manor = flow.find_manor_path(ctx)
    if not manor:
        raise RuntimeError("no manor found")
    note(ctx, "manor", path=manor)
    placed = flow.mousefree_place(ctx, manor)
    note(ctx, "keep placed", ok=placed)
    flow.feed_builders(ctx)
    flow.mousefree_commit(ctx)
    built = flow.watch_build(ctx, manor, int(ctx.variant_option("HARNESS_DAYS", "30")))
    ctx.metric("keep_built", int(bool(built)))
    attempt(ctx, "keep mesh users", lambda: ctx.commands.send("mesh_actors", mesh=KEEP_MESH))
    if ctx.variant_option("HARNESS_LUA", "") in ("keep", "both"):
        lua_reskin(ctx, True, True)
        attempt(ctx, "keep mesh users after", lambda: ctx.commands.send("mesh_actors", mesh="SM_KeepTent"))
    x, y, _ = (float(v) for v in ctx.variant_option("HARNESS_SPOT", "13000,-51163,2500").split(","))
    ctx.time.pause()
    for zoom in (3000, 1200):
        attempt(ctx, f"zoom {zoom}", lambda z=zoom: ctx.bridge.write_property(ctx.bridge.player_path(), "zoomLevel", z))
        look(ctx, f"keep_z{zoom}", x, y)
    attempt(ctx, "zoom reset", lambda: ctx.bridge.write_property(ctx.bridge.player_path(), "zoomLevel", 9000))


def run(ctx) -> dict:
    track_s = float(ctx.variant_option("HARNESS_TRACK_S", "70"))
    out_cm = float(ctx.variant_option("HARNESS_OUT_M", "35")) * UNIT_CM
    attempt(ctx, "path state", lambda: ctx.commands.send("path_state"))
    pieces = actors_of(ctx, WALL_MESH, "SMBuilding")
    gates = actors_of(ctx, GATE_MESH, "SMBuilding")
    actors_of(ctx, KEEP_MESH)
    ctx.metric("wall_pieces", len(pieces))
    if len(pieces) < 8:
        raise RuntimeError(f"too few built wall pieces for a ring: {len(pieces)}")
    centre = (sum(p["x"] for p in pieces) / len(pieces), sum(p["y"] for p in pieces) / len(pieces))
    polygon = ring_polygon(pieces, centre)
    radius = max(math.hypot(p["x"] - centre[0], p["y"] - centre[1]) for p in pieces)
    gate = gates[0] if gates else None
    note(ctx, "ring", centre=centre, radius_cm=round(radius), gate=gate, wall_samples=pieces[:3])
    ctx.metric("ring_radius_cm", round(radius))
    (ctx.run_dir / "ring.json").write_text(json.dumps({"centre": centre, "radius_cm": radius, "pieces": pieces, "gate": gate}), encoding="utf-8")
    lua = ctx.variant_option("HARNESS_LUA", "")
    if lua in ("wall", "both"):
        lua_reskin(ctx, True, False)
    look(ctx, "ring", centre[0], centre[1])
    attempt(ctx, "camera ring centre", lambda: ctx.bridge.centre_camera_on(centre[0], centre[1]))
    if ctx.variant_option("HARNESS_KEEP", "") == "1":
        build_keep(ctx)
        if ctx.variant_option("HARNESS_PATH", "1") != "1":
            return ctx.result()
        attempt(ctx, "camera ring centre 2", lambda: ctx.bridge.centre_camera_on(centre[0], centre[1]))
    ctx.actions.clear_battle()
    try:
        bait = ctx.actions.spawn_units("player", battle.SPEAR)
        pawn = bait["answer"]["center"]
        gate_bearing = math.atan2(gate["y"] - centre[1], gate["x"] - centre[0]) if gate else 0.0
        away = gate_bearing + math.pi
        target = (centre[0] + math.cos(away) * (radius + out_cm), centre[1] + math.sin(away) * (radius + out_cm))
        dx, dy = target[0] - pawn["x"], target[1] - pawn["y"]
        raiders = ctx.actions.spawn_units("bandit", "Brigands", dx=dx, dy=dy)
        squad = raiders["answer"]["squads"][0]["id"]
        start = ctx.commands.send("squad_positions", squad=squad)["units"]
        note(ctx, "start", bait_at=pawn, target=target, bandit_units=len(start), first=start[:2], gate_bearing_deg=round(math.degrees(gate_bearing)))
        ctx.screenshot("start")
        track = Track(ctx, squad, polygon, gate, int(track_s / (POLL_S * TRACK_SPEED)) + 1)
        ctx.popups()
        ctx.time.set_speed(TRACK_SPEED)
        try:
            ctx.run_until(track, track_s + 60, what="the bandit track", poll_s=POLL_S, stall_s=10, on_stall=ctx.popups)
        except WaitTimeout:
            ctx.log.info("track timed out")
        finally:
            ctx.time.pause()
        ctx.screenshot("end")
        last = track.samples[-1] if track.samples else {"units": [], "inside": 0}
        ctx.metric("samples", len(track.samples))
        ctx.metric("bandits_at_start", len(start))
        ctx.metric("bandits_inside_at_end", last["inside"])
        ctx.metric("bandits_alive_at_end", len(last["units"]))
        ctx.metric("max_inside", max((s["inside"] for s in track.samples), default=0))
        note(ctx, "result", first_inside=track.first_inside, last=last["units"][:3])
        if track.first_inside:
            ctx.metric("first_inside_sample", track.first_inside["sample"])
            ctx.metric("first_inside_gate_distance_cm", track.first_inside["gate_distance_cm"])
    finally:
        ctx.actions.clear_battle()
    return ctx.result()
