"""Probe for spec 07: place a building with the HarnessActions experiment (hook on getMouse3d, then a click).

Research tool, not a test. Choose the building type with HARNESS_PROBE_BTYPE (default 30, HitchingPost) and the
offset from the first building with HARNESS_PROBE_DX and HARNESS_PROBE_DY. It writes `probe.jsonl` in the run folder.
It never calls a function that saves.
"""

import json
import os
import time

from runlib.commands import CommandChannel

NAME = "probe-building2"
LIMIT_S = 150
HIDDEN = True


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.channel = CommandChannel(ctx.run_dir / "commands", check_alive=ctx.ensure_alive)
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        self.ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:900]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"step": step, **data}, default=str) + "\n")

    def send(self, step: str, command: str, **fields) -> dict:
        self.ctx.log.info(f"PROBE start {step}")
        try:
            answer = self.channel.send(command, **fields)
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            answer = {"ok": False, "error": str(error)[:300]}
        self.note(step, answer=answer)
        return answer

    def run_seconds(self, seconds: int) -> None:
        if os.environ.get("HARNESS_PROBE_RUNNING", "0") == "1":
            time.sleep(seconds)  # the game stays unpaused for the whole sequence
        else:
            self.ctx.time.run_game_seconds(seconds, speed=1)


def nearest_region(answer: dict) -> dict:
    pawn = answer["pawn"]
    distance = lambda region: (region["first"]["x"] - pawn["x"]) ** 2 + (region["first"]["y"] - pawn["y"]) ** 2  # noqa: E731
    return min((r for r in answer["regions"] if r.get("first")), key=distance)


def target_from(region: dict) -> tuple[float, float, float]:
    first = region["first"]
    dx = float(os.environ.get("HARNESS_PROBE_DX", "1500"))
    dy = float(os.environ.get("HARNESS_PROBE_DY", "0"))
    return first["x"] + dx, first["y"] + dy, first["z"]


def region_count(probe, name: str) -> int:
    answer = probe.send("where", "place_where")
    return next(r["count"] for r in answer["regions"] if r["name"] == name)


def region_items(probe, name: str) -> list:
    answer = probe.send("where after", "place_where")
    return next(r["items"] for r in answer["regions"] if r["name"] == name)


PAWN_FIELDS = ["placeBuilding", "placeBuilding_isSnapped", "cursorMode", "hasClicked", "buildConfirmHovered",
               "requestBuild", "isUsingUI", "bFullscreenUIActive", "currentUIMode", "buildingPreviewPlane", "previewBuildingDecals", "hitBuilding", "placebuilding_missingTech", "resourcesInCollisionOfPlacebuilding"]


def pawn_state(ctx) -> dict:
    state = {}
    for name in PAWN_FIELDS:
        try:
            state[name] = str(ctx.bridge.read_property(ctx.bridge.player_path(), name))[:120]
        except Exception as error:  # noqa: BLE001
            state[name] = f"<error {str(error)[:60]}>"
    for name in ("getMouse", "getMouse3d", "isBuildingHovered", "getLMBPressedB", "isInAnyConstructionMode"):
        try:
            state[name] = str(ctx.bridge.call_function(ctx.bridge.player_path(), name))[:120]
        except Exception as error:  # noqa: BLE001
            state[name] = f"<error {str(error)[:60]}>"
    state["LastMousePos"] = str(ctx.bridge.read_property(ctx.bridge.player_path(), "LastMousePos"))
    return state


def run(ctx) -> dict:
    probe = Probe(ctx)
    btype = int(os.environ.get("HARNESS_PROBE_BTYPE", "30"))
    where = probe.send("where", "place_where")
    region = nearest_region(where)
    before = region["count"]
    x, y, z = target_from(region)
    probe.note("target", region=region["name"], count=before, x=x, y=y, z=z)
    if os.environ.get("HARNESS_PROBE_SPAWN", "0") == "1":
        probe.send("spawn with an empty struct", "place_spawn_raw")
        probe.run_seconds(3)
        after = region_count(probe, region["name"])
        probe.note("result spawn", before=before, after=after)
        probe.note("items before", items=region["items"])
        probe.note("items after", items=region_items(probe, region["name"]))
        ctx.check("probe finished", True, f"before {before}, after {after}")
        return ctx.result()
    running = os.environ.get("HARNESS_PROBE_RUNNING", "0") == "1"
    if running:
        ctx.unpause()
    probe.send(f"arm type {btype}", "place_arm", type=btype, x=x, y=y, z=z)
    probe.run_seconds(2)
    ctx.screenshot("armed")
    probe.note("pawn state armed", state=pawn_state(ctx))
    if os.environ.get("HARNESS_PROBE_FORCE", "0") == "1":
        probe.send("force button and mesh", "place_force", type=btype)
        probe.run_seconds(1)
        probe.note("pawn state forced", state=pawn_state(ctx))
    probe.send("press", "place_press")
    probe.run_seconds(1)
    probe.send("release", "place_release")
    if running:
        probe.note("clock after release", clock=str(ctx.read_clock()))
    probe.run_seconds(3)
    ctx.screenshot("released")
    probe.note("pawn state released", state=pawn_state(ctx))
    if os.environ.get("HARNESS_PROBE_REQUEST", "0") == "1":
        probe.note("set requestBuild", result=str(ctx.bridge._result("set", ref=ctx.bridge.player_path(), name="requestBuild", value=True))[:200])
        probe.run_seconds(3)
    if running:
        ctx.pause()
    after = region_count(probe, region["name"])
    probe.note("result", before=before, after=after)
    probe.send("disarm", "place_disarm")
    ctx.check("probe finished", True, f"before {before}, after {after}")
    return ctx.result()
