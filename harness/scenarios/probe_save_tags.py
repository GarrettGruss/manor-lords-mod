"""Spike for spec 24: can a Tags array (names) of the player pawn or the player region carry a marker over save and load?

Writing a Tags array through the bridge `set` crashed the game (run 20261016-034223-9e92) and eval is off. So the mod
HarnessSaveProbe has the command tag_add (a Lua FName write). It stops before a save if the write fails.
Slots are kept for probe-save-read. The first slot has the pawn marker. The second slot has the pawn and the region marker.
"""

import json

NAME = "probe-save-tags"
LIMIT_S = 180
HIDDEN = True
MARKER = "mlmod_tag_A1"
MOD = "HarnessSaveProbe"


def run(ctx) -> dict:
    out = {"slots": {}}
    for target in ("pawn", "region"):
        answer = ctx.mod_commands.send(MOD, f"{MOD}.tag_add", {"target": target, "marker": MARKER})
        ctx.log.info(f"TAGS write {target}: {json.dumps(answer, default=str)[:600]}")
        out[f"write_{target}"] = answer
        record = ctx.actions.save_game(f"tags-{target}", keep=True)
        out["slots"][target] = record["slot"]
        ctx.log.info(f"TAGS saved {target} -> {record['slot']}")
    (ctx.run_dir / "tags.json").write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    result = ctx.result()
    result["slots"] = out["slots"]
    return result
