"""Probe for M03 iteration 02: does declare_peace with the bandit lord remove a role raid (spawnArmy squads)?

Research tool. It records every answer in `probe.jsonl` and never fails on a game answer. It never saves the game.
"""

import json

from runlib.units import side_count

NAME = "probe-role-raid-peace"
LIMIT_S = 600
HIDDEN = True
LONG_REASON = "The probe waits some game minutes for the raid to move."
SPEED = 3
STEP_S = 60
STEPS_BEFORE = 4
STEPS_AFTER = 6


def note(ctx, step: str, **data) -> None:
    entry = {"step": step, **data}
    ctx.log.info(f"PROBE {json.dumps(entry, default=str)[:1200]}")
    with (ctx.run_dir / "probe.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, default=str) + "\n")


def advance(ctx) -> None:
    try:
        ctx.time.run_game_seconds(STEP_S, speed=SPEED)
    except Exception as error:  # noqa: BLE001 - a spotted army drops the speed
        ctx.ensure_alive("advance")
        note(ctx, "advance failed", error=str(error)[:300])


def bandit_lord(ctx) -> int:
    for row in ctx.actions.lords_state(log=0)["lords"]:
        if row.get("bandit"):
            return row["lord"]
    raise AssertionError("no bandit lord in lords_state")


def look(ctx, label: str) -> None:
    lord = bandit_lord(ctx)
    row = ctx.actions.lords_state(log=0)["lords"][lord - 1]
    note(ctx, label, bandit_units=side_count(ctx.actions.units_census(), "bandit"),
         squads=[(q["id"], q["alive"], q.get("distance_to_player")) for q in row["squads"]], tags=row["with_player"]["tags"])


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    note(ctx, "state", state=ctx.mod.command("InvasionMod.invasion_state"))
    ctx.mod.command("InvasionMod.invasion_force_next")
    for step in range(1, STEPS_BEFORE + 1):
        advance(ctx)
        look(ctx, f"before {step}")
    lord = bandit_lord(ctx)
    note(ctx, "declare peace", result=ctx.actions.lord_declare_peace(lord))
    for step in range(1, STEPS_AFTER + 1):
        advance(ctx)
        look(ctx, f"after {step}")
    ctx.ensure_alive("role raid peace probe")
    ctx.expect.equals("the game stayed alive", True, True)
    return ctx.result()
