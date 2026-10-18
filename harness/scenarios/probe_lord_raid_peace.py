"""Probe for M03 iteration 02: does an AI lord army at war march to the village, and does declare_peace make it leave?

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer. It never saves the game.
"""

import json
import math
import os

NAME = "probe-lord-raid-peace"
LIMIT_S = 1100
HIDDEN = True
LONG_REASON = "The probe lets an army march across the map and then leave: about 1500 game seconds."
TEMPLATE = "spearMilitia"
SQUADS = 3
START_DY = -50000
STEP_S = 60
STEPS_BEFORE_PEACE = int(os.environ.get("PEACE_AFTER_STEPS", "8"))
STEPS_AFTER_PEACE = 12
NEAR = 14000
SPEED = 3
RUN_CHALLENGE = False  # the first probe (challenge on) handed the player region to the lord


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1200]}")
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


def advance(ctx) -> None:
    """A spotted army drops the speed to 1x. The harness gives up after 3 tries. The probe goes on."""
    try:
        ctx.time.run_game_seconds(STEP_S, speed=SPEED)
    except Exception as error:  # noqa: BLE001
        ctx.ensure_alive('advance')
        note(ctx, 'advance failed', error=str(error)[:300])


def squad_distances(state: dict, lord: int) -> list:
    home = state.get("player_at") or {}
    rows = state["lords"][lord - 1]["squads"]
    out = []
    for squad in rows:
        pos = squad.get("pos") or squad.get("position") or squad.get("center") or {}
        if "x" in pos and home:
            out.append(round(math.hypot(pos["x"] - home["x"], pos["y"] - home["y"])))
    return out


def sample(ctx, lord: int, label: str):
    state = attempt(ctx, label, lambda: ctx.actions.lords_state(log=4))
    census = attempt(ctx, label + " census", ctx.actions.units_census)
    if state and state.get("lords"):
        note(ctx, label + " distances", distances=squad_distances(state, lord), with_player=state["lords"][lord - 1].get("with_player"))
    return state


def run(ctx) -> dict:
    actions = ctx.actions
    made = attempt(ctx, "spawn lord", lambda: actions.spawn_ai_lord("Probe Raider", can_build=False))
    if not made:
        ctx.expect.equals("a lord was spawned", False, True)
        return ctx.result()
    lord = made["lord"]
    attempt(ctx, "relations", lambda: actions.lord_relations(lord))
    attempt(ctx, "start ai", lambda: actions.lord_start_ai(lord, speed=1, can_build=False))
    attempt(ctx, "declare war", lambda: actions.lord_declare_war(lord))
    attempt(ctx, "regions before", actions.regions_state)
    attempt(ctx, "army", lambda: actions.lord_spawn_army(lord, TEMPLATE, SQUADS, 0, START_DY))
    if RUN_CHALLENGE:
        attempt(ctx, "challenge", lambda: actions.lord_challenge(lord))
    for step in range(1, STEPS_BEFORE_PEACE + 1):
        advance(ctx)
        sample(ctx, lord, f"war step {step}")
    attempt(ctx, "regions at peace time", actions.regions_state)
    attempt(ctx, "declare peace", lambda: actions.lord_declare_peace(lord))
    for step in range(1, STEPS_AFTER_PEACE + 1):
        advance(ctx)
        sample(ctx, lord, f"peace step {step}")
    attempt(ctx, "regions end", actions.regions_state)
    ctx.ensure_alive("lord raid peace probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
