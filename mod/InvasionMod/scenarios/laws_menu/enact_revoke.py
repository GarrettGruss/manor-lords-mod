"""add-laws-menu: enact and revoke through the Laws menu, with the confirmation dialog, the yearly actions and the slot limit.

Needs the pak: `run.py --scenario laws-menu-enact-revoke --pak InvasionMod --slot 2`. It saves nothing. The scenario calls the same handlers as a
click (command laws_menu_press). Cancel and Esc close the dialog and change nothing.
"""

import time

from _laws_menu import picture, PREFIX, SETTLE_S, card, check_dialog_texts, check_texts_match_cards, menu, open_menu, prepare_laws, press, refused_press, tech

NAME = "laws-menu-enact-revoke"
DESCRIPTION = "Enact and revoke laws through the Laws menu: dialog, cancel, Esc, confirm, one action a year, full slots, contract unlock. Needs --pak InvasionMod."
LIMIT_S = 300
SLOTS_FULL = "All law slots are used. Revoke a law first."


def run(ctx) -> dict:
    prepare_laws(ctx)
    state = open_menu(ctx)
    ctx.check("E1 four laws are unlocked", state["header"]["unlocked_text"] == "4 of 9", state["header"])
    ctx.check("E1 no law is in force and the slot is free", tech(ctx)["laws"] == [] and state["header"]["slots_text"] == "0 / 1", state["header"])

    # Full slot: a law enacted by the low-level tech command uses no yearly action.
    ctx.mod.command(PREFIX + "tech_tree_enact_law", law="militia_charter")
    time.sleep(SETTLE_S)
    state = menu(ctx)
    ctx.check("E2 the slot is full: Enact is disabled with the text", (card(state, "trade_pacts")["enabled"], card(state, "trade_pacts")["hint"]) == (False, SLOTS_FULL), card(state, "trade_pacts"))
    ctx.check("E2 the yearly actions are untouched", (state["header"]["enact_text"], state["header"]["revoke_text"]) == ("1 / 1", "1 / 1"), state["header"])
    check_texts_match_cards(ctx, "E2", state)
    picture(ctx, "laws-menu-slot-full")

    # Revoke: dialog, Esc closes the dialog only, then confirm.
    press(ctx, "revoke", id="militia_charter")
    state = menu(ctx)
    ctx.check("E3 the revoke dialog is open and nothing changed", state["dialog"] is not None and tech(ctx)["laws"] == ["militia_charter"], state.get("dialog"))
    check_dialog_texts(ctx, "E3", state)
    picture(ctx, "laws-menu-dialog-revoke")
    ctx.mod.command(PREFIX + "menu_press_esc")
    time.sleep(SETTLE_S + 0.5)
    state = menu(ctx)
    ctx.check("E4 Esc closed the dialog and the menu stays open", state["open"] is True and state.get("dialog") is None, (state["open"], state.get("dialog")))
    check_dialog_texts(ctx, "E4", state)
    ctx.check("E4 the law is still in force", tech(ctx)["laws"] == ["militia_charter"], tech(ctx)["laws"])
    press(ctx, "revoke", id="militia_charter")
    press(ctx, "confirm")
    state = menu(ctx)
    ctx.check("E5 revoke confirmed: the law is gone and the effects end", tech(ctx)["laws"] == [] and abs(tech(ctx)["totals"]["militia_attack_multiplier"] - 1.1) < 1e-6, tech(ctx)["totals"])  # only the node Militia Rights is left (+10%)
    ctx.check("E5 the revoke action is used", state["header"]["revoke_text"] == "0 / 1", state["header"])
    check_dialog_texts(ctx, "E5", state)

    # Enact: cancel changes nothing, confirm enacts and uses the action.
    press(ctx, "enact", id="trade_pacts")
    ctx.check("E6 the enact dialog is open", menu(ctx)["dialog"] is not None and tech(ctx)["laws"] == [], menu(ctx).get("dialog"))
    picture(ctx, "laws-menu-dialog-enact")
    press(ctx, "cancel")
    ctx.check("E6 Cancel closed the dialog and changed nothing", menu(ctx).get("dialog") is None and tech(ctx)["laws"] == [] and menu(ctx)["enact_left"] == 1, menu(ctx).get("dialog"))
    press(ctx, "enact", id="trade_pacts")
    press(ctx, "confirm")
    state = menu(ctx)
    ctx.check("E7 enact confirmed: the law is in force with its effect", tech(ctx)["laws"] == ["trade_pacts"] and abs(tech(ctx)["totals"]["tribute_share_multiplier"] - 1.25) < 1e-6, tech(ctx)["totals"])
    ctx.check("E7 the enact action is used and the card says Revoke", state["header"]["enact_text"] == "0 / 1" and card(state, "trade_pacts")["button"] == "Revoke", state["header"])

    # One enact a year.
    reason = refused_press(ctx, "enact", id="militia_charter")
    ctx.check("E8 a second enact is refused with the text", reason is not None and "No enact action left this year." in reason, reason)
    ctx.check("E8 the card says so", card(menu(ctx), "militia_charter")["hint"] == "No enact action left this year.", card(menu(ctx), "militia_charter"))
    ctx.check("E8 nothing changed", tech(ctx)["laws"] == ["trade_pacts"], tech(ctx)["laws"])
    check_texts_match_cards(ctx, "E8", menu(ctx))
    picture(ctx, "laws-menu-actions-used")

    # A contract law of the other path, and an extra slot.
    ctx.mod.command(PREFIX + "laws_unlock", id="conscription", source="Contract: Test Levy")
    added = ctx.mod.command(PREFIX + "laws_add_slot")
    time.sleep(SETTLE_S)
    state = menu(ctx)
    ctx.check("E9 the contract law shows Unlocked with its source", (card(state, "conscription")["status"], card(state, "conscription")["source"]) == ("Unlocked", "Unlocked by: Contract: Test Levy"), card(state, "conscription"))
    ctx.check("E9 the extra slot gives 2 slots", (added["slots"], added["added"], state["header"]["slots_text"]) == (2, True, "1 / 2"), (added, state["header"]))
    check_texts_match_cards(ctx, "E9", state)
    ctx.mod.command(PREFIX + "laws_menu_close")
    return ctx.result()
