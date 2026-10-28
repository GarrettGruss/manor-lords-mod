"""Spike C of change update-spawn-from-map-border: can an allied AI lord bring a relief army in from the map edge?

A player squad cannot be moved from Lua (wiki engine-limits). So the relief army is tried as the army of a second AI lord that is
at war with the raid lord, with a challenge against it at the manor. Questions: do the ally squads walk in? Do they fight the raid
army? Research tool. It records every answer in `probe.jsonl`. It never saves the game.
"""

import json

NAME = "probe-border-ally"
LIMIT_S = 1000
HIDDEN = True
LONG_REASON = "Two armies walk in from opposite edges and meet."
TEMPLATE = "spearMilitia"
SQUADS = 3
HOSTILE_AT = (-2643, -92040)
ALLY_AT = (-2643, 87593)
STEP_S = 20
STEPS = 14
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
    hostile = (attempt(ctx, "spawn hostile lord", lambda: actions.spawn_ai_lord("Probe Hostile", can_build=False)) or {}).get("lord")
    ally = (attempt(ctx, "spawn ally lord", lambda: actions.spawn_ai_lord("Probe Ally", can_build=False)) or {}).get("lord")
    if not hostile or not ally:
        ctx.expect.equals("two lords were spawned", False, True)
        return ctx.result()
    for lord in (hostile, ally):
        attempt(ctx, f"relations {lord}", lambda lord=lord: actions.lord_relations(lord))
        attempt(ctx, f"start ai {lord}", lambda lord=lord: actions.lord_start_ai(lord, speed=1, can_build=False))
    attempt(ctx, "hostile war on player", lambda: actions.lord_declare_war(hostile))
    # Runs 20261028-021440-80f4 and -021742-8a3b: a war of the ally on the raid lord crashed the game (access violation) after 120 to 180 game s.
    for _ in range(SQUADS):
        attempt(ctx, "hostile squad", lambda: actions.lord_spawn_army(hostile, TEMPLATE, 1, x=HOSTILE_AT[0], y=HOSTILE_AT[1]))
        attempt(ctx, "ally squad", lambda: actions.lord_spawn_army(ally, TEMPLATE, 1, x=ALLY_AT[0], y=ALLY_AT[1]))
    attempt(ctx, "hostile challenge", lambda: actions.battlefield_anchor(lord=hostile))
    ctx.time.run_game_seconds(3, speed=SPEED)
    for step in range(1, STEPS + 1):
        try:
            ctx.time.run_game_seconds(STEP_S, speed=SPEED)
        except Exception as error:  # noqa: BLE001
            ctx.ensure_alive("advance")
            note(ctx, "advance failed", error=str(error)[:300])
        state = attempt(ctx, f"step {step}", lambda: actions.lords_state(log=0))
        rows = {}
        for lord in (state or {}).get("lords", []):
            if lord.get("name") in ("Probe Hostile", "Probe Ally"):
                rows[lord["name"]] = [(q["id"], q["alive"], q.get("x"), q.get("y"), q.get("distance_to_player")) for q in lord["squads"]]
        note(ctx, f"step {step} summary", game_s=step * STEP_S, rows=rows,
             challenges=[(c.get("by"), c.get("challenged"), c.get("status"), c.get("center")) for c in (state or {}).get("challenges", [])])
    ctx.ensure_alive("border ally probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
