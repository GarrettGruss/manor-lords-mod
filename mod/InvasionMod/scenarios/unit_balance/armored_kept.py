"""M05 iteration 01, A1 to A3: the rule changes unarmored units, keeps armored ones, and reaches a squad that spawns later.

No fight. Retinue (def 62) is armored. Brigands and spearMilitia are unarmored (def below 10).
"""

from runlib import battle

NAME = "unit-balance-armored-kept"
DESCRIPTION = "unit_balance changes unarmored units, keeps armored units, and reaches later squads without a command."
COVERS = []
LIMIT_S = 120
POLL_WAIT_S = 10  # 2 polls of 2 s, with margin


def squad_mean(ctx, side: str, template: str) -> dict:
    rows = [row for row in ctx.actions.unit_stats(side)["squads"] if row["template"] == template and row["alive"] > 0]
    return rows[0]["mean"] if rows else {}


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=True)
    ctx.actions.clear_battle()
    try:
        ctx.actions.spawn_units("player", battle.HEAVY, count=1)
        ctx.actions.spawn_units("bandit", "Brigands", count=1, dx=4000)
        heavy_before = squad_mean(ctx, "player", battle.HEAVY)
        state = ctx.mod.command("InvasionMod.unit_balance_apply")
        heavy, brigands = squad_mean(ctx, "player", battle.HEAVY), squad_mean(ctx, "bandit", "Brigands")
        ctx.log.info(f"state {state}; heavy {heavy}; brigands {brigands}")
        ctx.check("A1 Brigands have def 0 and block 0", brigands.get("def") == 0 and brigands.get("block") == 0, brigands)
        ctx.check("A1 the rule changed units and none failed", state["changed"] >= 1 and state["failed"] == 0, [state["changed"], state["failed"]])
        ctx.check("A2 retinue def and block are unchanged", heavy == heavy_before and heavy.get("def", 0) >= 50, [heavy_before, heavy])
        ctx.actions.spawn_units("player", battle.SPEAR, count=1, dy=4000)
        ctx.run_until(lambda: squad_mean(ctx, "player", battle.SPEAR).get("def") == 0, POLL_WAIT_S, what="the poll to change the new squad")
        ctx.check("A3 a later squad is changed by the poll", squad_mean(ctx, "player", battle.SPEAR).get("block") == 0, squad_mean(ctx, "player", battle.SPEAR))
        off = ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
        restored = squad_mean(ctx, "player", battle.SPEAR)
        ctx.check("A5 off restores the original values", off["restored"] > 0 and restored.get("def", 0) > 5, [off["restored"], restored])
    finally:
        ctx.mod.command("InvasionMod.unit_balance_set", enabled=True)
        ctx.actions.clear_battle()
    return ctx.result()
