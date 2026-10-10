"""Probe for spec 07: can a building be placed with a reflected function? Research tool, not a test.

Choose a group with HARNESS_PROBE_B (read, mode, click). Each group is one run, because a call may crash the game.
It writes `probe.jsonl` in the run folder. It never calls a function that saves.
"""

import json
import os

NAME = "probe-building"
LIMIT_S = 120
HIDDEN = True


class Probe:
    def __init__(self, ctx):
        self.ctx = ctx
        self.bridge = ctx.bridge
        self.path = ctx.run_dir / "probe.jsonl"

    def note(self, step: str, **data) -> None:
        self.ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:900]}")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"step": step, **data}, default=str) + "\n")

    def attempt(self, step: str, work):
        self.ctx.log.info(f"PROBE start {step}")
        try:
            outcome = {"ok": True, "result": work()}
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            self.ctx.ensure_alive(step)
            outcome = {"ok": False, "error": str(error)[:400]}
        self.note(step, **outcome)
        return outcome

    def get(self, ref, name):
        try:
            return self.bridge.read_property(ref, name)
        except Exception as error:  # noqa: BLE001
            return f"<error: {str(error)[:80]}>"


def counts(probe, region):
    bridge = probe.bridge
    return {
        "GetBuildings": len(bridge.call_function(region, "GetBuildings") or []),
        "all": bridge.call_function(region, "getBuildingCount", [-1, False]),
        "engine_buildingArr": len(probe.get(bridge.engine_path(), "buildingArr") or []),
    }


def mode_state(probe, player):
    names = ["cursorMode", "BuildingCategory", "placePlotType", "currentUIMode", "selectedBlueprint"]
    state = {name: probe.get(player, name) for name in names}
    state["inConstruction"] = probe.attempt("isInAnyConstructionMode", lambda: probe.bridge.call_function(player, "isInAnyConstructionMode"))
    return state


def group_read(probe, region, player):
    bridge = probe.bridge
    probe.note("counts", values=counts(probe, region))
    types = {}
    for bType in range(0, 80):
        n = bridge.call_function(region, "getBuildingCount", [bType, False])
        if n:
            types[bType] = n
    probe.note("building types in the region", types=types)
    probe.note("mode", values=mode_state(probe, player))
    buildings = bridge.call_function(region, "GetBuildings") or []
    probe.attempt("props of the first building", lambda: str(bridge._result("props", ref=str(buildings[0]), pattern="type|Type|ID|Id"))[:800])


def group_mode(probe, region, player):
    bridge = probe.bridge
    probe.note("counts before", values=counts(probe, region))
    probe.attempt("attemptEnterConstructionMenu", lambda: bridge.call_function(player, "attemptEnterConstructionMenu"))
    probe.note("mode after menu", values=mode_state(probe, player))
    wanted = int(os.environ.get("HARNESS_PROBE_BTYPE", "1"))
    probe.attempt(f"activateBuildingMode({wanted})", lambda: bridge.call_function(player, "activateBuildingMode", [wanted]))
    probe.note("mode after activate", values=mode_state(probe, player))
    probe.attempt("resetBuildingMode", lambda: bridge.call_function(player, "resetBuildingMode"))
    probe.note("mode after reset", values=mode_state(probe, player))


def group_click(probe, region, player):
    bridge = probe.bridge
    wanted = int(os.environ.get("HARNESS_PROBE_BTYPE", "1"))
    probe.note("counts before", values=counts(probe, region))
    probe.attempt(f"activateBuildingMode({wanted})", lambda: bridge.call_function(player, "activateBuildingMode", [wanted]))
    probe.note("mode after activate", values=mode_state(probe, player))
    probe.attempt("LMB_BP_pressed", lambda: bridge.call_function(player, "LMB_BP_pressed"))
    probe.attempt("LMB_BP_released", lambda: bridge.call_function(player, "LMB_BP_released"))
    probe.note("counts right after click", values=counts(probe, region))
    probe.attempt("run 5 s", lambda: probe.ctx.time.run_game_seconds(5, speed=1))
    probe.note("counts after 5 s", values=counts(probe, region))
    probe.attempt("resetBuildingMode", lambda: bridge.call_function(player, "resetBuildingMode"))


def group_scan(probe, region, player):
    """Activate several building types, look for a preview, click, and count the buildings of the region."""
    bridge = probe.bridge
    for bType in (2, 5, 10, 16, 20, 30, 40, 50):
        before = counts(probe, region)["GetBuildings"]
        probe.attempt(f"activateBuildingMode({bType})", lambda b=bType: bridge.call_function(player, "activateBuildingMode", [b]))
        plane = probe.get(player, "buildingPreviewPlane")
        mouse = probe.attempt("getMouse3d", lambda: bridge.call_function(player, "getMouse3d"))
        probe.note(f"type {bType} preview", plane=plane, mouse=mouse.get("result"), building_mode=mode_state(probe, player)["inConstruction"])
        probe.attempt("LMB pressed", lambda: bridge.call_function(player, "LMB_BP_pressed"))
        probe.attempt("LMB released", lambda: bridge.call_function(player, "LMB_BP_released"))
        probe.attempt("run 2 s", lambda: probe.ctx.time.run_game_seconds(2, speed=1))
        probe.note(f"type {bType} result", before=before, after=counts(probe, region)["GetBuildings"])
        probe.attempt("resetBuildingMode", lambda: bridge.call_function(player, "resetBuildingMode"))


GROUPS = {"read": group_read, "mode": group_mode, "click": group_click, "scan": group_scan}


def run(ctx) -> dict:
    group = os.environ.get("HARNESS_PROBE_B", "read")
    probe = Probe(ctx)
    probe.note("group", name=group)
    bridge = ctx.bridge
    GROUPS[group](probe, bridge.player_region_path(), bridge.player_path())
    ctx.check("probe finished", True, group)
    return ctx.result()
