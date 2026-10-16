"""Spike for spec 24: list the Tag-like live properties of a region, the player pawn and a building. No save, no writes."""

import json

NAME = "probe-save-fields"
LIMIT_S = 120
HIDDEN = True


def run(ctx) -> dict:
    bridge = ctx.bridge
    out = {}

    def note(key, value):
        out[key] = value
        ctx.log.info(f"FIELDS {key} = {json.dumps(value, default=str)[:1500]}")

    region = bridge.player_region_path()
    player = bridge.player_path()
    buildings = bridge._result("objects", class_name="SMBuildingMaster", limit=3)
    note("buildings", buildings)
    targets = {"region": region, "player": player}
    if buildings["objects"]:
        targets["building"] = buildings["objects"][0].split(" ", 1)[1]
    for name, ref in targets.items():
        note(f"{name}_ref", ref)
        for pattern in (None,):
            try:
                (ctx.run_dir / f"props_{name}.json").write_text(json.dumps(bridge._result("props", ref=ref, include_super=True, read_soft=False, pattern=pattern), default=str))
            except Exception as error:  # noqa: BLE001
                note(f"{name}_props_{pattern}_error", str(error)[:300])
    (ctx.run_dir / "fields.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    return ctx.result()
