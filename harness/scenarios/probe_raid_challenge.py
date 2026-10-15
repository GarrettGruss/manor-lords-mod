"""Probe for spec 10, issue #99, task 3: does a real bandit raid create a challenge?

Research tool. It starts one real raid (spawnRaiders through rebel_raid_rally), lets it run, and records the challenge list
of the game engine before, during and after. It never fails on a game answer and never saves the game.
"""

import json

NAME = "probe-raid-challenge"
LIMIT_S = 400
HIDDEN = True
LONG_REASON = "The raid walks to the village: about 200 game seconds."
STEP_S = 50
STEPS = 4
SPEED = 3


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def challenge_count(ctx, step: str) -> int:
    state = ctx.actions.lords_state(log=0)
    note(ctx, step, challenges=state["challenges"], open_claims=state["open_claims"])
    return len(state["challenges"])


def run(ctx) -> dict:
    ctx.metric("challenges_before", challenge_count(ctx, "before"))
    note(ctx, "raid", result=ctx.actions.rebel_raid_rally(2))
    seen = 0
    for step in range(1, STEPS + 1):
        ctx.time.run_game_seconds(STEP_S, speed=SPEED)
        seen = max(seen, challenge_count(ctx, f"watch {step}"))
    ctx.metric("challenges_max_during_raid", seen)
    ctx.ensure_alive("raid challenge probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
