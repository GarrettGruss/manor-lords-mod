"""Spec 10, issue #99: can the harness steer the battle place of a challenge with a battlefield anchor?

One run is one arm of an A/B. The variant option BATTLEFIELD_ANCHOR picks the arm: "1" moves all battlefield_BP_C actors to the
anchor (the manor of the defending region) in the same step as initChallenge; "0" is the control (plain lord_challenge).
It records the distance from the anchor reference to the challenge center, to the chosen battlefield actor and to the
lord army. The option BATTLEFIELD_EXTRA_LORDS adds more lords that challenge the same region (more samples per launch).
The options are read with ctx.variant_option: a Python scenario cannot read the game environment. The suite `battlefield-anchor-ab` judges the difference. It never saves the game.
"""

import json
import math

NAME = "battlefield-anchor"
LIMIT_S = 600
HIDDEN = True
LONG_REASON = "The run starts a war and a challenge, then watches the lord army for about 150 game seconds."
ENEMY_TEMPLATE = "spearMilitia"
DEFENDER_TEMPLATE = "retinue_tier3"
ENEMY_OFFSET = 6000
WATCH_STEP_S = 50
WATCH_STEPS = 3
SPEED = 3


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def distance(point: dict | None, reference: dict) -> float | None:
    if not point:
        return None
    return round(math.hypot(point["x"] - reference["x"], point["y"] - reference["y"]))


def lord_army_center(state: dict, lord: int) -> dict | None:
    squads = [squad for squad in state["lords"][lord - 1]["squads"] if squad.get("alive") and squad.get("x") is not None]
    if not squads:
        return None
    return {"x": sum(s["x"] for s in squads) / len(squads), "y": sum(s["y"] for s in squads) / len(squads)}


def prepare_war(ctx) -> int:
    actions = ctx.actions
    lord = actions.spawn_ai_lord("Anchor Baron", can_build=False)["lord"]
    actions.lord_relations(lord)
    actions.lord_start_ai(lord, speed=1, can_build=False)
    actions.lord_declare_war(lord)
    actions.lord_spawn_army(lord, ENEMY_TEMPLATE, 1, ENEMY_OFFSET, 0)
    actions.spawn_units("player", DEFENDER_TEMPLATE, 3, ENEMY_OFFSET - 500, 0)
    return lord


def start_challenge(ctx, lord: int, use_anchor: bool, delay_ms: int) -> dict:
    if use_anchor:
        return ctx.actions.battlefield_anchor(lord=lord, target=0, delay_ms=delay_ms)
    return ctx.actions.lord_challenge(lord)


def first_challenge(state: dict) -> dict | None:
    return state["challenges"][-1] if state["challenges"] else None


def record_challenge(ctx, state: dict, reference: dict) -> None:
    challenge = first_challenge(state)
    note(ctx, "challenge", challenge=challenge)
    if not challenge:
        return
    ctx.metric("center_dist", distance(challenge.get("center"), reference) or -1)


def extra_challenges(ctx, count: int, reference: dict, use_anchor: bool, delay_ms: int) -> None:
    """More lords challenge the same region. Each challenge picks a battlefield again."""
    for index in range(2, count + 2):
        lord = ctx.actions.spawn_ai_lord(f"Anchor Baron {index}", can_build=False)["lord"]
        ctx.actions.lord_relations(lord)
        answer = start_challenge(ctx, lord, use_anchor, delay_ms)
        ctx.time.run_game_seconds(3, speed=SPEED)
        state = ctx.actions.lords_state(log=0)
        note(ctx, f"extra challenge {index}", answer=answer, challenges=state["challenges"])
        challenge = state["challenges"][-1] if state["challenges"] else None
        if challenge and len(state["challenges"]) >= index:
            ctx.metric(f"center_dist_{index}", distance(challenge.get("center"), reference) or -1)


def run(ctx) -> dict:
    actions, expect = ctx.actions, ctx.expect
    use_anchor = ctx.variant_option("BATTLEFIELD_ANCHOR", "1") == "1"
    delay_ms = int(ctx.variant_option("BATTLEFIELD_DELAY_MS", "500"))
    extra_lords = int(ctx.variant_option("BATTLEFIELD_EXTRA_LORDS", "0"))
    ctx.metric("anchor_arm", 1 if use_anchor else 0)
    lord = prepare_war(ctx)
    before = actions.battlefield_state(target=0)
    note(ctx, "before", state=before)
    expect.equals("an anchor reference exists", before.get("would_anchor") is not None, True)
    reference = before["would_anchor"]
    answer = start_challenge(ctx, lord, use_anchor, delay_ms)
    note(ctx, "challenge started", anchor=use_anchor, answer=answer)
    ctx.time.run_game_seconds(5, speed=SPEED)
    state = actions.lords_state(log=0)
    expect.equals("a challenge exists", first_challenge(state) is not None, True)
    record_challenge(ctx, state, reference)
    after = actions.battlefield_state(target=0)
    note(ctx, "after", state=after)
    ctx.metric("fields_restored", 1 if after.get("anchor_active") is False else 0)
    extra_challenges(ctx, extra_lords, reference, use_anchor, delay_ms)
    for step in range(1, WATCH_STEPS + 1):
        ctx.time.run_game_seconds(WATCH_STEP_S, speed=SPEED)
        state = actions.lords_state(log=0)
        center = lord_army_center(state, lord)
        note(ctx, f"watch {step}", army=center, dist=distance(center, reference))
        if center:
            ctx.metric(f"army_dist_{step}", distance(center, reference))
    ctx.ensure_alive("battlefield anchor")
    return ctx.result()
