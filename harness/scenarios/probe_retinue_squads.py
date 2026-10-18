"""Probe for M13 iteration 03: can a script make retinue squads above the native limit of 12 men?

Research tool. Run on the fixture manor-bailey:
    uv run python harness\run.py --scenario probe-retinue-squads --fixture manor-bailey --slot auto
It lists retinue functions, calls InitializeEmptyRetinueSquad, spawns a retinue squad with spawnArmy and records the unit census.
It never calls a save function.
"""

import json

NAME = "probe-retinue-squads"
LIMIT_S = 300
HIDDEN = True
SILVER = 100000


def note(ctx, step: str, **data) -> None:
    ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:1800]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"step": step, **data}, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:600])
        return None
    note(ctx, step, result=result)
    return result


def retinue_functions(ctx, ref: str):
    found = ctx.bridge._result("funcs", ref=ref)  # noqa: SLF001
    return [item for item in found if "etinue" in json.dumps(item) or "quad" in item.get("name", "")]


def run(ctx) -> dict:
    ctx.actions.set_silver(SILVER)
    player = ctx.bridge.player_path()
    engine = ctx.bridge.engine_path()
    region = ctx.bridge.player_region_path()
    attempt(ctx, "player retinue funcs", lambda: retinue_functions(ctx, player))
    attempt(ctx, "engine retinue funcs", lambda: retinue_functions(ctx, engine))
    attempt(ctx, "census before", lambda: ctx.actions.units_census()["by_squad_type"])
    attempt(ctx, "InitializeEmptyRetinueSquad", lambda: ctx.bridge.call_function(player, "InitializeEmptyRetinueSquad", [region]))
    ctx.time.run_game_seconds(2, speed=1)
    attempt(ctx, "census after init", lambda: ctx.actions.units_census(sample=3))
    spawned = attempt(ctx, "spawn retinue_tier1", lambda: ctx.actions.spawn_units("player", "retinue_tier1", 1))
    ctx.time.run_game_seconds(2, speed=1)
    attempt(ctx, "census after spawn", lambda: ctx.actions.units_census())
    attempt(ctx, "battle state", lambda: ctx.actions.battle_state())
    return ctx.result()
