"""M05 iteration 04: one fight between two chosen groups, with the unit_balance rule and the experience of the player group as options.

Options (run.py --env): UB_PLAYER (template, default spearMilitia), UB_PLAYER_SQUADS (default 1), UB_ENEMY (default Brigands),
UB_ENEMY_SQUADS (default 2), UB_RULE = on (default) or off, UB_BLOCK_FACTOR (number, default: the config value),
UB_XP (experience written on the player squads, default 0), UB_VET = on (default) or off (the veterancy rule, when it exists).
The rule is off while the groups spawn and the experience is written. Then the settings are applied and one pass runs.
"""

from runlib import battle
from runlib.fights import START_GAP, run_fight

NAME = "unit-balance-matchup"
DESCRIPTION = "One fight between two chosen groups; metrics: win, loss rates; options for rule, block and experience."
COVERS = []
LIMIT_S = 240


def on_off(ctx, name: str, default: str) -> bool:
    value = ctx.variant_option(name, default)
    if value not in ("on", "off"):
        raise ValueError(f"{name} must be on or off, got {value!r}")
    return value == "on"


def settings(ctx, rule: bool) -> dict:
    args = {"enabled": rule}
    block = ctx.variant_option("UB_BLOCK_FACTOR", "")
    if block:
        args["block_factor"] = float(block)
    if on_off(ctx, "UB_VET", "on") is False:
        args["vet_enabled"] = False
    return args


def run(ctx) -> dict:
    player = ctx.variant_option("UB_PLAYER", battle.SPEAR)
    enemy = ctx.variant_option("UB_ENEMY", "Brigands")
    player_squads = int(ctx.variant_option("UB_PLAYER_SQUADS", "1"))
    enemy_squads = int(ctx.variant_option("UB_ENEMY_SQUADS", "2"))
    experience = float(ctx.variant_option("UB_XP", "0"))
    rule = on_off(ctx, "UB_RULE", "on")
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
    ctx.actions.clear_battle()
    try:
        made = ctx.actions.spawn_units("player", player, count=player_squads)
        ctx.actions.spawn_units("bandit", enemy, count=enemy_squads, dx=START_GAP)
        if experience > 0:
            for squad in made["answer"]["squads"]:
                ctx.actions.set_squad_experience(squad["id"], experience)
        ctx.mod.command("InvasionMod.unit_balance_set", **settings(ctx, rule))
        state = ctx.mod.command("InvasionMod.unit_balance_apply")
        ctx.log.info(f"settings: {state}")
        fight = run_fight(ctx)
    finally:
        ctx.actions.clear_battle()
    st = fight.state
    ctx.expect.at_least("casualties of both sides", battle.casualties(st, "player") + battle.casualties(st, "bandit"), 3)
    ctx.expect.record("the fight ended", fight.finished, fight.reason, "not a timeout")
    player_rate, enemy_rate = battle.casualty_rate(st, "player"), battle.casualty_rate(st, "bandit")
    ctx.metric("won", 1 if enemy_rate >= 0.99 and player_rate < enemy_rate else 0)
    for key, value in {"player_casualties": battle.casualties(st, "player"), "enemy_casualties": battle.casualties(st, "bandit"),
                       "player_loss_rate": round(player_rate, 4), "enemy_loss_rate": round(enemy_rate, 4),
                       "player_xp_end": round(battle.mean_experience(st, "player"), 2), "fight_wall_s": round(fight.wall_s, 1)}.items():
        ctx.metric(key, value)
    return ctx.result()
