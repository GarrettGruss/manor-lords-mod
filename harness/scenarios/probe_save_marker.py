"""Spike for spec 24, options A and B (save side). Hidden research tool.

It writes marker values into live string and number fields that may map to saved fields (region name, retinue name,
lord name, building town name, two pawn numbers). Then it saves with ctx.actions.save_game, changes the markers, and
saves again. Both slots are kept (keep=True) for probe-save-read. The live values are restored at the end.
The mod HarnessSaveProbe logs which save functions fire. The slot names go to saves.json in the run folder.
Writing a Tags array (names) through the bridge crashed the game (run 20261016-034223-9e92), so no Tags are written.
"""

import json

NAME = "probe-save-marker"
LIMIT_S = 180
HIDDEN = True

# (target, property, marker for slot a, marker for slot b)
FIELDS = (
    ("region", "regionName", "MLMOD_A1", "MLMOD_B2"),
    ("region", "retinueName", "MLMOD_RA", "MLMOD_RB"),
    ("pawn", "lordsName", "MLMOD_LA", "MLMOD_LB"),
    ("building", "TownName", "MLMOD_TA", "MLMOD_TB"),
    ("pawn", "lastQuestDay", 777, 888),
    ("pawn", "numTimesInDebt", 7, 8),
)
# Each slot writes only the fields of one group, so a field that breaks a load can be found (run 20261016-034717-fc52).
# Slot label -> (index of the marker value to use, field indexes in FIELDS).
SLOTS = {
    "marker-lord-a": (0, (2,)),
    "marker-lord-b": (1, (2,)),
}


def read_all(bridge, refs):
    return {f"{target}.{prop}": bridge.read_property(refs[target], prop) for target, prop, *_ in FIELDS}


def run(ctx) -> dict:
    bridge = ctx.bridge
    refs = {"region": bridge.player_region_path(), "pawn": bridge.player_path()}
    refs["building"] = bridge._result("objects", class_name="SMBuildingMaster", limit=1)["objects"][0].split(" ", 1)[1]
    originals = read_all(bridge, refs)
    out = {"refs": refs, "originals": originals, "slots": {}, "calendar": bridge.read_calendar()}
    ctx.log.info(f"MARKER originals {json.dumps(originals, default=str)}")
    try:
        for label, (index, field_indexes) in SLOTS.items():
            chosen = [FIELDS[i] for i in field_indexes]
            for target, prop, *markers in chosen:
                bridge.write_property(refs[target], prop, markers[index])
            info = {"readback": read_all(bridge, refs), "calendar": bridge.read_calendar()}
            record = ctx.actions.save_game(label, keep=True)
            info.update(slot=record["slot"], files=sorted(record["files"]), backup=record["backup"])
            out["slots"][label] = info
            for target, prop, *_ in chosen:
                bridge.write_property(refs[target], prop, originals[f"{target}.{prop}"])
            ctx.log.info(f"MARKER saved {label} -> {record['slot']}: {json.dumps(info, default=str)[:1500]}")
    finally:
        for target, prop, *_ in FIELDS:
            bridge.write_property(refs[target], prop, originals[f"{target}.{prop}"])
        (ctx.run_dir / "saves.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    result = ctx.result()
    result["slots"] = {label: info["slot"] for label, info in out["slots"].items()}
    return result
