"""Spike for spec 24, load side. Hidden research tool. Start it on a kept marker slot (run.py --save <path>.sav).

It reads the same fields that probe-save-marker wrote and records them in loaded.json. It writes nothing and saves nothing.
"""

import json

from scenarios.probe_save_marker import FIELDS

NAME = "probe-save-read"
LIMIT_S = 120
HIDDEN = True


def run(ctx) -> dict:
    bridge = ctx.bridge
    refs = {"region": bridge.player_region_path(), "pawn": bridge.player_path()}
    refs["building"] = bridge._result("objects", class_name="SMBuildingMaster", limit=1)["objects"][0].split(" ", 1)[1]
    values = {f"{target}.{prop}": bridge.read_property(refs[target], prop) for target, prop, *_ in FIELDS}
    for target in ("region", "pawn"):
        props = bridge._result("props", ref=refs[target], include_super=True, read_soft=False, pattern="Tag")["properties"]
        values[f"{target}.Tags"] = next((p["value"] for p in props if p["name"] == "Tags"), None)
    out = {"values": values, "calendar": bridge.read_calendar(), "refs": refs}
    (ctx.run_dir / "loaded.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    ctx.log.info(f"LOADED {json.dumps(out, default=str)}")
    result = ctx.result()
    result["loaded"] = values
    return result
