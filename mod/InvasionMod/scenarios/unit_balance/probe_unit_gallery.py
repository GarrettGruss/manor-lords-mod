"""Probe for the wiki page unit-templates: stats and gear of every spawnable unit type, and a picture of each brigand variant.

Research tool, not a test. It saves nothing. Every answer goes to `probe.jsonl`. A type that fails to spawn is recorded, not failed.
The squads belong to the player side, so they stand still and do not fight. The rule unit_balance is off, so the stats are vanilla.
"""

import json
import time

from runlib.osinput import Win32Input  # only bring_to_front: other windows may cover the game, and the picture copies screen pixels

NAME = "probe-unit-gallery"
LIMIT_S = 420
HIDDEN = True
LONG_REASON = "The probe spawns 18 squads, reads their stats and gear, and takes five pictures."
TYPES = ["spearMilitia", "militiaPole", "militiaFoot", "bowMilitia", "crossbowMilitia", "militia", "retinue_tier1", "retinue_tier3",
         "mercenary_spearmen", "mercenary_infantry", "mercenary_archers", "mercenary_heavy_archers", "mercenary_crossbowmen",
         "brigands", "brigandArchers", "brigandPolearms", "basket", "sherwoodBow"]
BRIGANDS = ["brigands", "brigandArchers", "brigandPolearms", "basket", "sherwoodBow"]
GRID_STEP = 3000
GRID_COLUMNS = 6
GEAR_UNITS = 4
SETTLE_S = 6
ZOOM = 900.0  # world units from the pawn; meshy_house uses 600 for a close view
BALANCE_COMMAND = "InvasionMod.unit_balance_set"


def run(ctx) -> dict:
    actions = ctx.actions
    path = ctx.run_dir / "probe.jsonl"

    def note(step, **data):
        entry = {"step": step, **data}
        ctx.log.info(f"GALLERY {json.dumps(entry, default=str)[:1500]}")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, default=str) + "\n")

    def attempt(step, work):
        try:
            result = work()
        except Exception as error:  # noqa: BLE001 - the probe records every answer
            ctx.ensure_alive(step)
            note(step, error=str(error)[:400])
            return None
        return result

    attempt("close popups", actions.close_popups)
    attempt("balance off", lambda: ctx.mod.command(BALANCE_COMMAND, enabled=False))
    squads = {}
    for index, template in enumerate(TYPES):
        dx = (index % GRID_COLUMNS - GRID_COLUMNS / 2) * GRID_STEP
        dy = (index // GRID_COLUMNS - 1) * GRID_STEP
        record = attempt(f"spawn {template}", lambda: actions.spawn_units("player", template, 1, dx, dy))
        if not record:
            note("spawned", type=template, ok=False)
            continue
        answer = record["answer"]
        squads[template] = {"id": answer["squads"][0]["id"], "units": answer["squads"][0]["units"], "x": answer["center"]["x"], "y": answer["center"]["y"]}
        note("spawned", type=template, **squads[template])

    stats = attempt("unit_stats", actions.unit_stats) or {"squads": []}
    by_id = {row["squad"]: row for row in stats["squads"]}
    for template, squad in squads.items():
        mean = by_id.get(squad["id"], {}).get("mean", {})
        gear = attempt(f"gear {template}", lambda: actions.lead_unit_gear(squad["id"])) or {}
        note("squad", type=template, units=squad["units"], alive=by_id.get(squad["id"], {}).get("alive"),
             att=mean.get("att"), defense=mean.get("def"), armor_pierce=mean.get("armorPierce"),
             gear=[row["gear"] for row in gear.get("rows", [])[:GEAR_UNITS]])

    bridge = actions._bridge
    player = bridge.player_path()
    note("zoom before", zoom=attempt("zoom read", lambda: bridge.read_property(player, "zoomLevel")))
    attempt("zoom write", lambda: bridge.write_property(player, "zoomLevel", ZOOM))
    attempt("zoom settle", lambda: ctx.time.run_game_seconds(SETTLE_S, speed=1))
    note("zoom after", zoom=attempt("zoom read", lambda: bridge.read_property(player, "zoomLevel")))
    for template in BRIGANDS:
        squad = squads.get(template)
        if not squad:
            continue
        ground = attempt(f"camera {template}", lambda: bridge.centre_camera_on(squad["x"], squad["y"]))
        attempt("settle", lambda: ctx.time.run_game_seconds(SETTLE_S, speed=1))
        time.sleep(2)  # the camera follows the pawn with a lag
        ground = attempt(f"camera again {template}", lambda: bridge.centre_camera_on(squad["x"], squad["y"]))
        note("camera", type=template, ground=ground, squad=squad)
        attempt("front", lambda: Win32Input().bring_to_front(ctx.game_window()["hwnd"]))
        time.sleep(1)
        ctx.screenshot(template)

    attempt("clear", lambda: actions.clear_battle())
    ctx.ensure_alive("unit gallery probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
