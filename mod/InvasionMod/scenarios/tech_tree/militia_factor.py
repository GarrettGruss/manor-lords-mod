"""M12 iteration 03: Militia Rights raises the attack of the player militia by 10 percent.

The militia are the villagers of the player pawn (role Husband or Son) in the saved game. The scenario reads one of them through the
state command of the tech tree: its base att and its live att. It saves nothing.
"""

NAME = "tech-tree-militia-factor"
DESCRIPTION = "Militia Rights raises att of the player militia by 10 percent; the live value is read back from a unit."
LIMIT_S = 240
POLL_WAIT_S = 30


def tree(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tech_tree_state")


def unlock_militia_rights(ctx) -> None:
    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="prosperity")
    ctx.actions.set_settlement_level(3)
    ctx.run_until(lambda: tree(ctx)["slots"] >= 3, 15, what="3 node slots")
    for node in ("fair_courts", "amnesty", "militia_rights"):
        ctx.mod.command("InvasionMod.tech_tree_unlock", node=node)


def scaled(ctx) -> bool:
    sample = tree(ctx)["militia"].get("sample")
    return sample is not None and abs(sample["att"] - sample["base_att"] * 1.1) < 0.01


def run(ctx) -> dict:
    unlock_militia_rights(ctx)
    ctx.run_until(lambda: tree(ctx)["militia"]["units"] > 0, POLL_WAIT_S, what="the poll to find militia units")
    ctx.run_until(lambda: scaled(ctx), POLL_WAIT_S, what="att x 1.1")
    militia = tree(ctx)["militia"]
    ctx.check("M1 militia att is 1.1 times the base", scaled(ctx), militia)
    ctx.check("M2 the attack factor is 1.1 and the defence factor is 1", abs(militia["attack_factor"] - 1.1) < 1e-9 and militia["defence_factor"] == 1, militia)
    ctx.time.run_game_seconds(20, speed=1)
    ctx.check("M3 the value holds after 20 game seconds", scaled(ctx), tree(ctx)["militia"])
    ctx.metric("militia_units", militia["units"])
    ctx.metric("att_base", militia["sample"]["base_att"])
    ctx.metric("att_now", militia["sample"]["att"])
    return ctx.result()
