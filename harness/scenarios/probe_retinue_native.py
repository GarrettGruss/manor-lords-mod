"""Probe for change add-contract-retinue-reward (spike 1): can a native retinue squad of 5 men be made and filled?

Research tool. Run on the fixture manor-bailey:
    uv run python harness\\run.py --scenario probe-retinue-native --fixture manor-bailey --slot 2
It records every answer in probe.jsonl and never fails on a game answer. It never calls a save function.
"""

import json

NAME = "probe-retinue-native"
LIMIT_S = 300
HIDDEN = True
SILVER = 100000


def note(ctx, step, **data):
    ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"step": step, **data}, default=str) + "\n")


def attempt(ctx, step, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:600])
        return None
    note(ctx, step, result=result)
    return result


def cmd(ctx, step, **fields):
    return attempt(ctx, step, lambda: ctx.actions._command("loan_probe", **fields))  # noqa: SLF001


def write_phase(ctx) -> dict:
    """Make a native squad with 5 men, save (guarded save_game, keep=True). The kept slot must be deleted afterwards."""
    ctx.actions.set_silver(SILVER)
    ctx.time.run_game_seconds(3, speed=1)
    cmd(ctx, "init", mode="rinit")
    for number in range(5):
        cmd(ctx, f"hire {number + 1}", mode="rhire")
    ctx.time.run_game_seconds(3, speed=1)
    cmd(ctx, "squads before save", mode="rsquads")
    record = ctx.actions.save_game("retinue squad probe", keep=True)
    note(ctx, "saved", slot=record["slot"])
    result = ctx.result()
    result["slot"] = record["slot"]
    return result


def read_phase(ctx) -> dict:
    ctx.time.run_game_seconds(5, speed=1)
    cmd(ctx, "squads after load", mode="rsquads")
    cmd(ctx, "bound after load", mode="rbound")
    cmd(ctx, "hire after load", mode="rhire")
    ctx.time.run_game_seconds(3, speed=1)
    cmd(ctx, "squads after load hire", mode="rsquads")
    ctx.screenshot("retinue-after-load")
    return ctx.result()


def run(ctx) -> dict:
    phase = ctx.variant_option("PROBE_PHASE", "main")
    if phase == "type":
        ctx.actions.set_silver(SILVER)
        ctx.actions.spawn_units("player", "spearMilitia", 1)
        ctx.actions.spawn_units("player", "retinue_tier1", 1)
        cmd(ctx, "init", mode="rinit")
        cmd(ctx, "hire", mode="rhire")
        ctx.time.run_game_seconds(3, speed=1)
        cmd(ctx, "squads", mode="rsquads")
        cmd(ctx, "squadType", mode="rsq")
        return ctx.result()
    if phase == "props":
        ctx.actions.set_silver(SILVER)
        paths = (cmd(ctx, "paths", mode="rpaths") or {}).get("paths", {})
        cmd(ctx, "init", mode="rinit")
        cmd(ctx, "hire", mode="rhire")
        for name, full in paths.items():
            path = full.split(" ", 1)[-1]
            for pattern in ("[Rr]etin", "[Ss]quad", "[Rr]etain"):
                attempt(ctx, f"props {name} {pattern}", lambda p=path, q=pattern: ctx.bridge._result("props", ref=p, include_super=True, read_soft=False, pattern=q)["properties"])  # noqa: SLF001
        return ctx.result()
    if phase == "units":
        ctx.actions.set_silver(SILVER)
        ctx.actions.spawn_units("player", "spearMilitia", 1)
        ctx.actions.spawn_units("player", "retinue_tier1", 1)
        cmd(ctx, "init", mode="rinit")
        cmd(ctx, "hire", mode="rhire")
        ctx.time.run_game_seconds(3, speed=1)
        units = cmd(ctx, "units", mode="runits")
        for row in (units or {}).get("units", []):
            if row["class"] != "VAMP_DefaultUnit_C":
                continue
            path = row["path"].split(" ", 1)[-1]
            for pattern in ("[Rr]etin", "[Rr]etain", "[Nn]oble", "[Cc]ompan", "[Ss]quadT"):
                attempt(ctx, f"props squad {row['squad']} {pattern}", lambda p=path, q=pattern: ctx.bridge._result("props", ref=p, include_super=True, read_soft=False, pattern=q)["properties"])  # noqa: SLF001
        return ctx.result()
    if phase == "write":
        return write_phase(ctx)
    if phase == "read":
        return read_phase(ctx)
    ctx.actions.set_silver(SILVER)
    ctx.time.run_game_seconds(3, speed=1)
    player = ctx.bridge.player_path()
    attempt(ctx, "player funcs", lambda: [f.get("name") for f in ctx.bridge._result("funcs", ref=player) if "etinue" in f.get("name", "") or "quad" in f.get("name", "")])  # noqa: SLF001
    cmd(ctx, "squads start", mode="rsquads")
    cmd(ctx, "bound start", mode="rbound")
    cmd(ctx, "hire one", mode="rhire")
    ctx.time.run_game_seconds(2, speed=1)
    cmd(ctx, "bound after hire", mode="rbound")
    cmd(ctx, "init empty squad", mode="rinit")
    ctx.time.run_game_seconds(3, speed=1)
    cmd(ctx, "squads after init", mode="rsquads")
    cmd(ctx, "hire after init", mode="rhire")
    ctx.time.run_game_seconds(3, speed=1)
    cmd(ctx, "squads after hire", mode="rsquads")
    cmd(ctx, "bound end", mode="rbound")
    ctx.screenshot("retinue-native")
    return ctx.result()
