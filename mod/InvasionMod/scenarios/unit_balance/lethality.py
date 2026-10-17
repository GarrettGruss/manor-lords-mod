"""M05 iteration 01, A4 and A5: one fight with the unit_balance rule on or off.

Option UB_RULE (run.py --env): "on" (default) or "off". Option UB_BANDIT_SQUADS (1 to 3, default 2).
The groups are 32 spearMilitia and Brigands. Both sides are unarmored, so the rule changes both.
"""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "unit-balance-lethality"
DESCRIPTION = "One fight with the unit_balance rule on or off; metrics: casualties of both sides, loss rates, mean def."
COVERS = []
LIMIT_S = 240


def mean_def(ctx, side: str) -> float:
    squads = [row for row in ctx.actions.unit_stats(side)["squads"] if row["alive"] > 0]
    return round(sum(row["mean"]["def"] * row["alive"] for row in squads) / max(1, sum(row["alive"] for row in squads)), 3)


def run(ctx) -> dict:
    rule = ctx.variant_option("UB_RULE", "on")
    if rule not in ("on", "off"):
        raise ValueError(f"UB_RULE must be on or off, got {rule!r}")
    squads = int(ctx.variant_option("UB_BANDIT_SQUADS", "2"))
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=(rule == "on"))
    ctx.actions.clear_battle()
    try:
        ctx.actions.spawn_units("player", battle.SPEAR, count=1)
        ctx.actions.spawn_units("bandit", "Brigands", count=squads, dx=START_GAP)
        state = ctx.mod.command("InvasionMod.unit_balance_apply")
        ctx.log.info(f"rule {rule}: {state}")
        ctx.metric("player_def_mean", mean_def(ctx, "player"))
        ctx.metric("bandit_def_mean", mean_def(ctx, "bandit"))
        fight = run_fight(ctx)
    finally:
        ctx.actions.clear_battle()
    st = fight.state
    ctx.expect.at_least("casualties of both sides", battle.casualties(st, "player") + battle.casualties(st, "bandit"), 3)
    ctx.expect.record("the fight ended", fight.finished, fight.reason, "not a timeout")
    for key, value in {"player_casualties": battle.casualties(st, "player"), "bandit_casualties": battle.casualties(st, "bandit"),
                       "casualties_total": battle.casualties(st, "player") + battle.casualties(st, "bandit"),
                       "player_loss_rate": round(battle.casualty_rate(st, "player"), 4),
                       "bandit_loss_rate": round(battle.casualty_rate(st, "bandit"), 4),
                       "fight_wall_s": round(fight.wall_s, 1)}.items():
        ctx.metric(key, value)
    return ctx.result()
