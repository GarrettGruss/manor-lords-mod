"""M12 iterations 01 and 03: the path choice, the node slots and the node effects.

Steps: choose Oppression (the choice is final), unlock Martial Law with settlement level 1 (Public Order +10),
raise the level and unlock Iron Hand (Public Order +15 more, buy-back price x1.25), pay a buy-back at the new price.
It saves nothing. The path choice lives in the pawn tags of this run only.
"""

NAME = "tech-tree-path-choice"
DESCRIPTION = "The player picks a path, unlocks nodes by settlement level, and the effects reach Public Order and the buy-back price."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "A buy-back waits for game seconds, plus the start."
PRICE_PER_FAMILY = 10


def tree(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tech_tree_state")


def bandits(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def manor_term(ctx) -> int:
    """The manor term of a forced tick, from order 0 so that no clamp hides it."""
    ctx.mod.command("InvasionMod.bandits_set_order", value=0)
    return ctx.mod.command("InvasionMod.bandits_tick_now")["last_tick"]["manor_term"]


def check_start(ctx) -> None:
    ctx.run_until(lambda: tree(ctx).get("path") is not None, 30, what="the tech tree state")
    start = tree(ctx)
    ctx.check("T1 the start has no path and 8 nodes", start["path"] == "none" and len(start["nodes"]) == 8, start)
    reason = ctx.mod.refusal("InvasionMod.tech_tree_unlock", node="martial_law")
    ctx.check("T2 a node is refused before a path is chosen", reason is not None and "no path" in reason, reason)


def check_path(ctx) -> None:
    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="oppression")
    again = ctx.mod.refusal("InvasionMod.tech_tree_choose_path", path="prosperity")
    ctx.check("T3 the path choice is final", again is not None and tree(ctx)["path"] == "oppression", [again, tree(ctx)["path"]])
    other = ctx.mod.refusal("InvasionMod.tech_tree_unlock", node="fair_courts")
    ctx.check("T4 a node of the other path is refused", other is not None and "other path" in other, other)


def check_first_node(ctx) -> None:
    ctx.actions.set_settlement_level(1)
    ctx.run_until(lambda: tree(ctx)["settlement_level"] == 1, 15, what="settlement level 1")
    state = tree(ctx)
    ctx.check("T5 one slot at level 1", state["slots"] == 1 and state["free_slots"] == 1, state)
    skipped = ctx.mod.refusal("InvasionMod.tech_tree_unlock", node="iron_hand")
    ctx.check("T6 a node needs its required node", skipped is not None and "needs 'martial_law'" in skipped, skipped)
    before = bandits(ctx)
    ctx.mod.command("InvasionMod.tech_tree_unlock", node="martial_law")
    ctx.run_until(lambda: bandits(ctx)["modifiers"]["order_bonus"] == 10, 15, what="the Public Order bonus")
    after = bandits(ctx)
    ctx.check("T7 the manor term of a tick is 10 + 10", manor_term(ctx) == 20, [before["modifiers"], after["modifiers"]])
    full = ctx.mod.refusal("InvasionMod.tech_tree_unlock", node="iron_hand")
    ctx.check("T8 no free slot at level 1 after one node", full is not None and "no free node slot" in full, full)


def check_second_node(ctx) -> None:
    ctx.actions.set_settlement_level(2)
    ctx.run_until(lambda: tree(ctx)["slots"] == 2, 15, what="settlement level 2")
    ctx.mod.command("InvasionMod.tech_tree_unlock", node="iron_hand")
    ctx.run_until(lambda: bandits(ctx)["modifiers"]["order_bonus"] == 25, 15, what="the second Public Order bonus")
    after = bandits(ctx)
    ctx.check("T9 the manor term of a tick is 10 + 25", manor_term(ctx) == 35, after["modifiers"])
    ctx.check("T10 the buy-back price factor is 1.25", abs(after["buy_back_multiplier"] - 1.25) < 1e-9, after["buy_back_multiplier"])


def check_buy_back_price(ctx) -> None:
    ctx.mod.command("InvasionMod.bandits_leave_now", count=2)
    ctx.run_until(lambda: bandits(ctx)["outstanding_families"] >= 2, 20, what="the conversion")
    ctx.time.run_game_seconds(10, speed=SPEED)
    ctx.actions.set_silver(200)
    answer = ctx.mod.command("InvasionMod.bandits_buy_back")
    base = answer["expected_families"] * PRICE_PER_FAMILY
    ctx.check("T11 the buy-back price is 1.25 x 10 per family", answer["accepted"] is True and answer["price"] == -(-base * 125 // 100),
              [answer, base])
    for _ in range(8):
        if not bandits(ctx)["buy_back_pending"]:
            break
        ctx.time.run_game_seconds(30, speed=SPEED)
    ctx.metric("price", answer["price"])


def check_militia_factor(ctx) -> None:
    """The militia factor reaches the units: set through the tech tree totals is covered by the fake game. Here: the live write."""
    state = tree(ctx)
    ctx.check("T12 the militia factors are 1 on the Oppression path before Veteran Levies",
              state["militia"]["attack_factor"] == 1 and state["militia"]["defence_factor"] == 1, state["militia"])


def run(ctx) -> dict:
    check_start(ctx)
    check_path(ctx)
    check_first_node(ctx)
    check_second_node(ctx)
    check_buy_back_price(ctx)
    check_militia_factor(ctx)
    final = tree(ctx)
    ctx.check("T13 the unlocked nodes are kept in order", final["unlocked"] == ["martial_law", "iron_hand"], final["unlocked"])
    ctx.time.run_game_days(3, speed=SPEED)
    ctx.metric("unlocked", len(final["unlocked"]))
    return ctx.result()
