"""add-laws-menu: picture evidence of the Laws menu (no law, two laws in force, filter Locked, full slots, the dialog) and a check that the
texts of the widget equal the model.

Needs the pak: `run.py --scenario laws-menu-layout --pak InvasionMod --slot 2`. It saves nothing. The pictures go to evidence/.
"""

import time

from _laws_menu import picture, PREFIX, SETTLE_S, card, check_dialog_texts, check_texts_match_cards, menu, open_menu, prepare_laws, press, tech

NAME = "laws-menu-layout"
DESCRIPTION = "Take pictures of the Laws menu in its main states and compare the widget texts with the model. Needs --pak InvasionMod."
LIMIT_S = 300


def run(ctx) -> dict:
    ctx.run_until(lambda: tech(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    state = open_menu(ctx)
    check_texts_match_cards(ctx, "L1 no law", state)
    picture(ctx, "laws-menu-no-law")
    ctx.mod.command(PREFIX + "laws_menu_close")

    prepare_laws(ctx)
    ctx.mod.command(PREFIX + "laws_unlock", id="conscription", source="Reward of a Large contract")
    ctx.mod.command(PREFIX + "laws_add_slot")
    ctx.mod.command(PREFIX + "tech_tree_enact_law", law="militia_charter")
    ctx.mod.command(PREFIX + "tech_tree_enact_law", law="trade_pacts")
    state = open_menu(ctx)
    ctx.check("L2 two laws are in force with 2 slots", (state["header"]["slots_text"], len(tech(ctx)["laws"])) == ("2 / 2", 2), state["header"])
    check_texts_match_cards(ctx, "L2 two laws", state)
    picture(ctx, "laws-menu-two-laws")

    press(ctx, "filter", filter="locked")
    state = menu(ctx)
    ctx.check("L3 the filter Locked shows the locked cards only", len(state["cards"]) == 4 and all(row["status"] == "Locked" for row in state["cards"]), [row["id"] for row in state["cards"]])
    check_texts_match_cards(ctx, "L3 locked", state)
    picture(ctx, "laws-menu-filter-locked")
    press(ctx, "filter", filter="unlocked")
    state = menu(ctx)
    ctx.check("L4 the filter Unlocked shows the unlocked cards only", len(state["cards"]) == 5 and all(row["status"] != "Locked" for row in state["cards"]), [row["id"] for row in state["cards"]])
    check_texts_match_cards(ctx, "L4 unlocked", state)
    press(ctx, "filter", filter="all")

    press(ctx, "revoke", id="trade_pacts")
    state = menu(ctx)
    check_dialog_texts(ctx, "L5 dialog", state)
    picture(ctx, "laws-menu-dialog-revoke")
    press(ctx, "cancel")
    ctx.check("L5 the dialog texts are empty after Cancel", menu(ctx).get("dialog") is None, menu(ctx).get("dialog"))
    check_dialog_texts(ctx, "L5 closed", menu(ctx))
    time.sleep(SETTLE_S)
    ctx.mod.command(PREFIX + "laws_menu_close")
    return ctx.result()
