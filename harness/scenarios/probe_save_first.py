"""First real guarded harness save (spec 24, issue #128). Research tool, hidden.

It loads the default fixture and calls ctx.actions.save_game once. keep=True here: the slot stays for a load test.
"""

import json

NAME = "probe-save-first"
LIMIT_S = 120
HIDDEN = True


def run(ctx) -> dict:
    record = ctx.actions.save_game("first", keep=True)
    (ctx.run_dir / "save_first.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    ctx.log.info(f"SAVE_FIRST slot={record['slot']} files={sorted(record['files'])} backup={record['backup']}")
    ctx.check("one new slot sav file", f"{record['slot']}.sav" in record["files"], 1, [1, 1])
    result = ctx.result()
    result["save"] = {"slot": record["slot"], "files": sorted(record["files"]), "backup": record["backup"]}
    return result
