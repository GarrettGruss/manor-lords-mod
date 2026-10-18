"""M05 iteration 03: armored militia against 1.69 times as many bandits, with the weapon bonus on or off.

Options (run.py --env): UB_WEAPON = on (default) or off; UB_BANDIT_SQUADS (1 to 4, default 3); UB_ARMOR_DEF (default 17.2, spearMilitia def 7.2 plus mail 10; 0: no armor write);
UB_RULE = on (default) or off (the whole feature off: the vanilla fight);
UB_ATT_FACTOR and UB_PIERCE_ADD (only with UB_WEAPON=on, default: the config values).
The rule is off while the groups spawn. Then the scenario writes the armor def on the militia and switches the rule on, so the
rule sees an armored militia (def 10 to 40) and unarmored bandits (def 0).
"""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "unit-balance-armored-fight"
DESCRIPTION = "32 armored militia against Brigands, weapon bonus on or off; metrics: win, loss rates."
COVERS = []
LIMIT_S = 240


def run(ctx) -> dict:
    weapon = ctx.variant_option("UB_WEAPON", "on")
    if weapon not in ("on", "off"):
        raise ValueError(f"UB_WEAPON must be on or off, got {weapon!r}")
    squads = int(ctx.variant_option("UB_BANDIT_SQUADS", "3"))
    armor_def = float(ctx.variant_option("UB_ARMOR_DEF", "17.2"))
    rule = ctx.variant_option("UB_RULE", "on")
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
    ctx.actions.clear_battle()
    try:
        ctx.actions.spawn_units("player", battle.SPEAR, count=1)
        ctx.actions.spawn_units("bandit", "Brigands", count=squads, dx=START_GAP)
        if armor_def > 0:
            ctx.actions.set_unit_stat("player", "def", armor_def)
        if weapon == "off":
            args = {"att_factor": 1.0, "pierce_add": 0.0}
        else:
            args = {k: float(ctx.variant_option(v, "")) for k, v in (("att_factor", "UB_ATT_FACTOR"), ("pierce_add", "UB_PIERCE_ADD")) if ctx.variant_option(v, "")}
        ctx.mod.command("InvasionMod.unit_balance_set", enabled=(rule == "on"), **args)
        state = ctx.mod.command("InvasionMod.unit_balance_apply")
        ctx.log.info(f"weapon {weapon}: {state}")
        ctx.metric("weapon_units", state["weapon"])
        ctx.metric("att_factor", state["att_factor"])
        ctx.metric("pierce_add", state["pierce_add"])
        fight = run_fight(ctx)
    finally:
        ctx.actions.clear_battle()
    st = fight.state
    ctx.expect.at_least("casualties of both sides", battle.casualties(st, "player") + battle.casualties(st, "bandit"), 3)
    ctx.expect.record("the fight ended", fight.finished, fight.reason, "not a timeout")
    player_rate, bandit_rate = battle.casualty_rate(st, "player"), battle.casualty_rate(st, "bandit")
    ctx.metric("won", 1 if bandit_rate >= 0.99 and player_rate < bandit_rate else 0)
    for key, value in {"player_casualties": battle.casualties(st, "player"), "bandit_casualties": battle.casualties(st, "bandit"),
                       "player_loss_rate": round(player_rate, 4), "bandit_loss_rate": round(bandit_rate, 4),
                       "fight_wall_s": round(fight.wall_s, 1)}.items():
        ctx.metric(key, value)
    return ctx.result()
