"""add-laws-menu: the Laws menu opens from the bar, shows the header and nine cards, and closes with the command and with Esc.

Needs the pak: `run.py --scenario laws-menu-open-close --pak InvasionMod --slot 2`. It saves nothing.
"""

import time

from _laws_menu import picture, PREFIX, SETTLE_S, check_dialog_texts, check_texts_match_cards, menu, open_menu

NAME = "laws-menu-open-close"
DESCRIPTION = "Open the Laws menu, check the header, nine cards and the bar button, close it with the command and with Esc. Needs --pak InvasionMod."
LIMIT_S = 300


def bar_labels(ctx) -> list:
    return [row["label"] for row in ctx.mod.command(PREFIX + "menu_state")["buttons"]]


def run(ctx) -> dict:
    ctx.check("O1 the bar has a Laws button", "Laws" in bar_labels(ctx), bar_labels(ctx))
    state = open_menu(ctx)
    ctx.check("O2 the menu is open and in the viewport", state["open"] is True and state["in_viewport"] is True, (state["open"], state["in_viewport"]))
    ctx.check("O3 nine cards show", len(state["cards"]) == 9, len(state["cards"]))
    header = state["header"]
    ctx.check("O4 the header: 0 of 1 slots, max 5, 1 enact, 1 revoke", (header["slots_text"], header["max_text"], header["enact_text"], header["revoke_text"]) == ("0 / 1", "(max 5)", "1 / 1", "1 / 1"), header)
    ctx.check("O5 the title text", state["texts"].get("TitleText") == "LAWS", state["texts"].get("TitleText"))
    check_texts_match_cards(ctx, "O6", state)
    check_dialog_texts(ctx, "O7", state)
    ctx.check("O8 the filter texts", [state["texts"].get(f"FilterText{i}") for i in range(3)] == ["All", "Unlocked", "Locked"], [state["texts"].get(f"FilterText{i}") for i in range(3)])
    picture(ctx, "laws-menu-open")

    ctx.mod.command(PREFIX + "laws_menu_close")
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close command closes the menu", poll_s=0.5)
    ctx.check("O9 the menu is closed", menu(ctx)["open"] is False, menu(ctx)["open"])

    open_menu(ctx)
    ctx.mod.command(PREFIX + "menu_press_esc")
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="Esc closes the menu", poll_s=0.5)
    ctx.check("O10 Esc closed the menu", menu(ctx)["open"] is False, menu(ctx)["open"])
    time.sleep(SETTLE_S)
    return ctx.result()
