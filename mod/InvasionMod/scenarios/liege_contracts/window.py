"""update-liege-tribute-to-contracts: the liege window shows three contract cards; real mouse clicks pick and complete.

Needs the pak: `run.py --scenario liege-contracts-window --new-game --pak InvasionMod`. Real mouse input: other mouse scenarios wait.
It saves nothing. Pictures: empty state, three cards, a pick, the active panel, a tooltip hover.
"""

import time

from runlib import osinput

NAME = "liege-contracts-window"
DESCRIPTION = "Open the liege window, show three cards, pick one and complete it with the real mouse, take pictures. Needs --pak InvasionMod."
LIMIT_S = 500
EXCLUSIVE = True
LONG_REASON = "Hover scans and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 2.2  # the window writes the visibility once more 1.5 s after the open
HOVER_WAIT_S = 0.2
IDS = "timber_for_the_walls.clear_the_roads.keep_the_peace"
# Click points as fractions of the game window, found with the first pictures (see evidence/README.md). The scan around
# each point checks with the `hovered` flag of the click button that the point is on the button.
SCAN_X = tuple(round(0.02 * step, 3) for step in range(2, 49))
SCAN_Y = tuple(round(0.02 * step, 3) for step in range(2, 49))
HINTS = {"PickButton1": (0.188, 0.68), "CompleteButton": (0.179, 0.816), "ArmsButton": (0.233, 0.921), "CloseButton": (0.194, 0.526)}


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_menu_state")


def front(ctx) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)


def find_button(ctx, name: str) -> tuple:
    front(ctx)
    hint = HINTS.get(name)
    xs, ys = SCAN_X, SCAN_Y
    if hint:
        xs = tuple(round(hint[0] + 0.01 * d, 3) for d in range(-5, 6))
        ys = tuple(round(hint[1] + 0.01 * d, 3) for d in range(-5, 6))
    for fy in ys:
        for fx in xs:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(b["name"] == name and b.get("hovered") for b in menu(ctx)["buttons"]):
                ctx.log.info(f"BUTTON {name} at ({fx:.3f}, {fy:.3f})")
                HINTS[name] = (fx, fy)
                return fx, fy
    raise AssertionError(f"the mouse never hovered {name}")


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("W1 the window opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    expect.equals("W2 the window is in the viewport", state["in_viewport"], True)
    expect.equals("W3 no offer: the empty text shows", "start of spring" in state["texts"].get("EmptyText", ""), True)
    expect.equals("W4 the shown texts equal the wanted texts", {k: state["texts"].get(k) for k in state["wanted_texts"]}, state["wanted_texts"])
    expect.equals("W3b no offer: the empty cards are collapsed", state.get("card_visibility"), 1)
    ctx.screenshot("window-empty")

    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=IDS)
    time.sleep(SETTLE_S + 0.8)
    state = menu(ctx)
    ctx.log.info(f"CARDS tooltips={state['tooltips']} visible={state['visible']}")
    expect.equals("W5 three card names show", [state["texts"].get(f"CardName{i}") for i in range(3)], ["Timber for the Walls", "Clear the Roads", "Keep the Peace"])
    expect.equals("W6 the first objective shows an amount", state["texts"].get("ObjText0_0"), "60 Wood")
    expect.equals("W7 the penalty badge shows", state["texts"].get("CardPenalty0"), "Fail: -500 influence")
    expect.equals("W8 an item has a tooltip", bool(state["tooltips"].get("ObjItem0_0")), True)
    ctx.screenshot("window-three-cards")

    front(ctx)
    ctx.hover_with_mouse(0.08, 0.552)  # the first objective item of the first card
    time.sleep(2.5)
    ctx.screenshot("window-tooltip")
    hovered = menu(ctx)
    ctx.log.info(f"HOVER text={hovered.get('hover_text')} panel_visibility={hovered.get('panel_visibility')} panel={hovered.get('panel_name')}")
    expect.equals("W8b the footer shows the text of the hovered item", "Wood" in (hovered.get("hover_text") or ""), True)
    expect.equals("W8c the active panel is collapsed with no active contract", hovered.get("panel_visibility"), 1)
    if ctx.variant_option("CONTRACTS_PICTURES_ONLY", "0") == "1":
        return ctx.result()

    fx, fy = find_button(ctx, "PickButton1")
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: menu(ctx)["picks"] >= 1, 8, what="the click picks a contract", poll_s=0.5)
    time.sleep(SETTLE_S + 0.8)
    contracts = ctx.mod.command(PREFIX + "liege_contracts_state")
    expect.equals("W9 the second contract is active", contracts["active"]["id"], "clear_the_roads")
    state = menu(ctx)
    expect.equals("W10 the active panel shows the name", state["texts"].get("ActiveName"), "Clear the Roads")
    expect.equals("W11 the other cards show as discarded", [state["texts"].get(f"CardState{i}") for i in range(3)], ["Discarded", "Active", "Discarded"])
    ctx.screenshot("window-picked")

    ctx.mod.command(PREFIX + "liege_contracts_test_progress", index=1, value=15)
    time.sleep(SETTLE_S + 0.8)
    ctx.screenshot("window-complete-ready")
    before = ctx.mod.command(PREFIX + "liege_state")
    fx, fy = find_button(ctx, "CompleteButton")
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: menu(ctx)["completes"] >= 1, 8, what="the click completes the contract", poll_s=0.5)
    time.sleep(SETTLE_S + 0.8)
    after = ctx.mod.command(PREFIX + "liege_state")
    expect.equals("W12 the influence rose by 25", round(after["influence"] - before["influence"], 2), 25.0)
    expect.equals("W13 the silver rose by 150", int(after["silver"]) - int(before["silver"]), 150)
    state = menu(ctx)
    expect.equals("W14 the influence text follows", state["texts"].get("InfluenceText"), state["wanted_texts"]["InfluenceText"])
    expect.equals("W15 the silver text follows", state["texts"].get("SilverText"), state["wanted_texts"]["SilverText"])
    ctx.screenshot("window-after-complete")

    fx, fy = find_button(ctx, "CloseButton")
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the window", poll_s=0.5)
    return ctx.result()
