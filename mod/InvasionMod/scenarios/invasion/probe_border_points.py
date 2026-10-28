"""Spike B of change update-spawn-from-map-border: do armies spawned just outside the map edge walk in?

Spawns one squad at each of 8 points 3000 units outside the playable square (the edge actor splines, Jagged_Cliffs: x -89459 to
84174, y -89040 to 84593), gives the lord a challenge at the manor, and records the squad positions. Research tool. It records
every answer in `probe.jsonl`. It never saves the game.
"""

import json

NAME = "probe-border-points"
LIMIT_S = 900
HIDDEN = True
LONG_REASON = "Observation of 8 armies walking in from the edge."
TEMPLATE = "spearMilitia"
MARGIN = 3000
X_MIN, X_MAX, Y_MIN, Y_MAX = -89459, 84174, -89040, 84593
STEP_S = 20
STEPS = 12
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


def points() -> dict:
    mid_x, mid_y = (X_MIN + X_MAX) // 2, (Y_MIN + Y_MAX) // 2
    return {
        "N": (mid_x, Y_MAX + MARGIN), "S": (mid_x, Y_MIN - MARGIN), "E": (X_MAX + MARGIN, mid_y), "W": (X_MIN - MARGIN, mid_y),
        "NE": (X_MAX + MARGIN, Y_MAX + MARGIN), "NW": (X_MIN - MARGIN, Y_MAX + MARGIN),
        "SE": (X_MAX + MARGIN, Y_MIN - MARGIN), "SW": (X_MIN - MARGIN, Y_MIN - MARGIN),
    }


def run(ctx) -> dict:
    actions = ctx.actions
    made = attempt(ctx, "spawn lord", lambda: actions.spawn_ai_lord("Probe Edge", can_build=False))
    if not made:
        ctx.expect.equals("a lord was spawned", False, True)
        return ctx.result()
    lord = made["lord"]
    attempt(ctx, "relations", lambda: actions.lord_relations(lord))
    attempt(ctx, "start ai", lambda: actions.lord_start_ai(lord, speed=1, can_build=False))
    attempt(ctx, "declare war", lambda: actions.lord_declare_war(lord))
    ids = {}
    for name, (x, y) in points().items():
        answer = attempt(ctx, f"spawn {name}", lambda x=x, y=y: actions.lord_spawn_army(lord, TEMPLATE, 1, x=x, y=y))
        if answer and answer.get("squads"):
            ids[answer["squads"][0]] = name
    attempt(ctx, "anchored challenge", lambda: actions.battlefield_anchor(lord=lord))
    for step in range(1, STEPS + 1):
        try:
            ctx.time.run_game_seconds(STEP_S, speed=SPEED)
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("advance")
            note(ctx, "advance failed", error=str(error)[:300])
        state = attempt(ctx, f"step {step}", lambda: actions.lords_state(log=0))
        mine = [row for row in (state or {}).get("lords", []) if row.get("name") == "Probe Edge"]
        squads = {ids.get(q["id"], q["id"]): (q["alive"], q.get("x"), q.get("y"), q.get("distance_to_player")) for q in mine[0]["squads"]} if mine else None
        note(ctx, f"step {step} summary", game_s=step * STEP_S, squads=squads)
    ctx.ensure_alive("border points probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
