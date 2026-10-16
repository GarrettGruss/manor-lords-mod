"""Probe for spec 26: does a region claim play the victory cinematic, and does the goal setting change it?

Research tool. It records every answer in `probe.jsonl`. It never saves the game.
Environment: GS_GOAL (0 to 3, optional: write the goal before the claim), GS_CONSUME (1: layClaim with consumeInfluence),
GS_REGION (region object name, default: the first region without an owner).
"""

import json
import os
import time

NAME = "probe-claim-victory"
LIMIT_S = 300
HIDDEN = True
LONG_REASON = "The probe waits for the cinematic after the claim."
HOOKS = {
    "victory": "/Script/ManorLords.PawnCPP:createAndPlayVictoryCinematic",
    "layClaim": "/Script/ManorLords.PawnCPP:layClaim",
    "finalizeClaim": "/Script/ManorLords.PawnCPP:finalizeClaim",
    "defeat": "/Script/ManorLords.PawnCPP:triggerDefeat",
}
INFLUENCE = 1000
WAIT_AFTER_CLAIM_S = 12


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1500]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def attempt(ctx, step: str, fn):
    try:
        result = fn()
    except Exception as error:  # a probe records the failure and goes on
        note(ctx, step, error=repr(error))
        return None
    note(ctx, step, result=result)
    return result


def pick_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    note(ctx, "regions", rows=rows)
    wanted = os.environ.get("GS_REGION")
    if wanted:
        return wanted
    free = [row["region"] for row in rows if not row.get("owner")]
    if not free:
        raise RuntimeError("no region without an owner in this start: the probe cannot claim")
    return free[0]


def count_events(ctx) -> dict:
    events = ctx.bridge._result("events", since=0, limit=200)  # noqa: SLF001
    counts: dict = {}
    for event in events.get("events", []):
        counts[event.get("label")] = counts.get(event.get("label"), 0) + 1
    note(ctx, "events", counts=counts, events=events.get("events", [])[:30])
    return counts


def run(ctx) -> dict:
    actions, bridge = ctx.actions, ctx.bridge
    note(ctx, "env", goal=os.environ.get("GS_GOAL"), consume=os.environ.get("GS_CONSUME"))
    note(ctx, "setup before", result=actions.game_setup_state())
    goal = os.environ.get("GS_GOAL")
    if goal is not None:
        note(ctx, "set goal", result=actions.game_setup_set_goal(int(goal)))
    for label, path in HOOKS.items():
        attempt(ctx, f"hook {label}", lambda p=path, l=label: bridge._result("hook", function=p, label=l, max_args=4))  # noqa: SLF001
    player = bridge.player_path()
    note(ctx, "influence write", result=bridge.write_property(player, "influence", INFLUENCE))
    region = pick_region(ctx)
    ctx.screenshot("before-claim")
    consume = os.environ.get("GS_CONSUME") == "1"
    note(ctx, "claim", region=region, consume=consume,
         result=actions.claim_region(region, target=0, finalize=True, consume_influence=consume))
    for second in (2, 6, WAIT_AFTER_CLAIM_S):
        time.sleep(second if second == 2 else 4 if second == 6 else 6)
        ctx.screenshot(f"after-claim-{second}s")
    counts = count_events(ctx)
    note(ctx, "setup after", result=actions.game_setup_state())
    note(ctx, "influence after", result=bridge.read_property(player, "influence"))
    ctx.metric("victory_calls", counts.get("victory", 0))
    ctx.metric("defeat_calls", counts.get("defeat", 0))
    ctx.metric("lay_claim_calls", counts.get("layClaim", 0))
    ctx.metric("finalize_claim_calls", counts.get("finalizeClaim", 0))
    ctx.ensure_alive("claim probe")
    return ctx.result()
