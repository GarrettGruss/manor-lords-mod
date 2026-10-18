"""M13 iteration 03: retinue men above the native limit of 12, made as extra player squads.

Run it on the fixture manor-bailey (a built manor house, no mouse needed):
    uv run python harness\run.py --scenario manor-stronghold-retinue-squads --fixture manor-bailey --slot auto
Steps: no squad is allowed without the tech tree bonus, Militia Rights allows one squad of 36 men, the squad is hired and paid,
the men are player-owned, then Brigands attack the squad and the squad fights and survives. It saves nothing.
"""

NAME = "manor-stronghold-retinue-squads"
DESCRIPTION = "An extra retinue squad of 36 men above the native limit of 12: hired with silver, player-owned, fights and survives."
LIMIT_S = 300
SPEED = 2
SILVER = 100000
SQUAD_MEN = 36
FIGHT_S = 90
MIN_SURVIVORS = 20


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.retinue_squad_state")


def unlock_militia_rights(ctx) -> None:
    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="prosperity")
    ctx.actions.set_settlement_level(3)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.tech_tree_state")["slots"] >= 3, 20, what="3 node slots")
    for node in ("fair_courts", "amnesty", "militia_rights"):
        ctx.mod.command("InvasionMod.tech_tree_unlock", node=node)
    ctx.run_until(lambda: state(ctx)["bonus"] > 0, 20, what="the retinue bonus")


def player_units(ctx) -> int:
    return ctx.actions.units_census()["by_side"].get("player", 0)


def run(ctx) -> dict:
    ctx.actions.set_silver(SILVER)
    start = state(ctx)
    ctx.check("S1 no squad is allowed without the bonus", start["squads_allowed"] == 0, start)
    ctx.check("S1 a hire without the bonus is refused", ctx.mod.refusal("InvasionMod.retinue_squad_hire") is not None)

    unlock_militia_rights(ctx)
    allowed = state(ctx)
    ctx.check("S2 the bonus allows one squad", allowed["squads_allowed"] == 1, allowed)
    men_before = player_units(ctx)
    hired = ctx.mod.command("InvasionMod.retinue_squad_hire")
    ctx.time.run_game_seconds(2, speed=SPEED)
    after = state(ctx)
    ctx.check("S3 the squad exists with 36 living men", after["squads"] == 1 and after["squad_men_alive"] == SQUAD_MEN, after)
    ctx.check("S3 the total retinue men are above the native limit of 12", after["bound"] + after["squad_men_alive"] > 12, after)
    ctx.check("S4 the men are player-owned", player_units(ctx) - men_before >= SQUAD_MEN, player_units(ctx))
    ctx.check("S5 a second squad is refused", ctx.mod.refusal("InvasionMod.retinue_squad_hire") is not None)

    ctx.actions.set_silver(SILVER)  # keeps the later checks independent of the payment
    pawn = ctx.bridge.call_function(ctx.bridge.player_path(), "K2_GetActorLocation", [])
    ctx.actions.spawn_units("bandit", "Brigands", 1, dx=hired["x"] - pawn["X"], dy=hired["y"] - pawn["Y"] + 2500)
    ctx.time.run_game_seconds(FIGHT_S, speed=SPEED)
    final = state(ctx)
    battle = ctx.actions.battle_state()
    ctx.metric("squad_men_alive_end", final["squad_men_alive"])
    ctx.metric("bandit_alive_end", battle["by_side"].get("bandit", {}).get("alive", -1))
    bandit_initial = battle["by_side"].get("bandit", {}).get("initial", 0)
    bandit_alive = battle["by_side"].get("bandit", {}).get("alive", bandit_initial)
    ctx.check("S6 the squad fought: some bandits died", bandit_alive < bandit_initial, battle["by_side"])
    ctx.check(f"S7 the squad survived with at least {MIN_SURVIVORS} men", final["squad_men_alive"] >= MIN_SURVIVORS, final)
    return ctx.result()
