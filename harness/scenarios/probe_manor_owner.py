"""Spike (spec 32, part 2): list the manors (building type 98) of a save with their Data fields and owners. Read only. Research tool."""

import json

from runlib.bridge_client import object_path

NAME = "probe-manor-owner"
LIMIT_S = 240
HIDDEN = True
MANOR_TYPE = 98


def run(ctx) -> dict:
    found = ctx.bridge._result("objects", class_name="SMBuildingMaster", limit=500)["objects"]
    ctx.metric("masters", len(found))
    manors = 0
    for ref in found:
        path = object_path(ref)
        data = ctx.bridge.read_property(path, "Data")
        if isinstance(data, dict) and data.get("bType") == MANOR_TYPE:
            manors += 1
            ctx.log.info("MANOR " + path + " " + json.dumps(data, default=str)[:1500])
            for field in ("isManor", "owner", "pawnOwner", "region"):
                try:
                    ctx.log.info(f"MANOR {field} " + json.dumps(ctx.bridge.read_property(path, field), default=str)[:300])
                except Exception as error:  # noqa: BLE001
                    ctx.log.info(f"MANOR {field} error {str(error)[:100]}")
    ctx.metric("manors", manors)
    return ctx.result()
