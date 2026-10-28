"""Spike A of change update-spawn-from-map-border: spawnArmy with arrival days 0 to 3.

Questions: does the army appear at once or after N days? Where (the given position or the map border)? Are squad ids returned
before arrival? Research tool. It records every answer in `probe.jsonl`. It never saves the game.
"""

import json

NAME = "probe-border-arrival"
LIMIT_S = 900
HIDDEN = True
LONG_REASON = "Four game days of observation after the spawn."
TEMPLATE = "spearMilitia"
START_DY = -50000
DAYS = (0, 1, 2, 3)
STEP_S = 10
STEPS = 18
SPEED = 3


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, work):
    try:
        result = work()
    except Exception as error:  # noqa: BLE001 - the probe records every answer
        ctx.ensure_alive(step)
        note(ctx, step, error=str(error)[:500])
        return None
    note(ctx, step, result=result)
    return result


def run(ctx) -> dict:
    actions = ctx.actions
    made = attempt(ctx, "spawn lord", lambda: actions.spawn_ai_lord("Probe Border", can_build=False))
    if not made:
        ctx.expect.equals("a lord was spawned", False, True)
        return ctx.result()
    lord = made["lord"]
    attempt(ctx, "relations", lambda: actions.lord_relations(lord))
    attempt(ctx, "start ai", lambda: actions.lord_start_ai(lord, speed=1, can_build=False))
    attempt(ctx, "declare war", lambda: actions.lord_declare_war(lord))
    attempt(ctx, "player region", lambda: [r for r in actions.regions_state().get("regions", []) if "MyPawn" in (r.get("owner") or "")])
    for days in DAYS:
        attempt(ctx, f"spawn days={days}", lambda d=days: actions.lord_spawn_army(lord, TEMPLATE, 1, 0, START_DY, d))
    for step in range(1, STEPS + 1):
        try:
            ctx.time.run_game_seconds(STEP_S, speed=SPEED)
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("advance")
            note(ctx, "advance failed", error=str(error)[:300])
        state = attempt(ctx, f"step {step}", lambda: actions.lords_state(log=0))
        mine = [row for row in (state or {}).get("lords", []) if row.get("name") == "Probe Border"]
        squads = [(q["id"], q["alive"], q.get("x"), q.get("y"), q.get("distance_to_player")) for q in mine[0]["squads"]] if mine else None
        note(ctx, f"step {step} summary", game_s=step * STEP_S, squads=squads)
    ctx.ensure_alive("border arrival probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
