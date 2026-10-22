"""add-mod-menu-access-rule, task 2.3: one smoke run for all mod menus.

Each registered menu has a button in the game's bottom bar. A real mouse click on the button opens the menu (1 click, no key).
A click on the Close button (top left) closes it. A picture is taken of the bar and of each menu.
Needs the paks: `run.py --scenario menu-smoke --slot 0 --pak raidmenu --pak techmenu`. Real mouse input: no other game on the slot.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

from runlib import osinput

NAME = "menu-smoke"
DESCRIPTION = "Every mod menu opens from its bottom bar button with one real click, shows its content, and closes. Needs --pak raidmenu --pak techmenu."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "Hover sweep over the bottom bar and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.2
HOVER_WAIT_S = 0.2
MENUS = ("raid", "tech", "tribute")
SILVER = 1000
# The bottom bar stands at the bottom centre. The geometry calls return zero, so a button is found by the hover hook.
BAR_X = tuple(round(0.30 + 0.01 * step, 3) for step in range(41))
BAR_Y = (0.945, 0.96)
# The Close button of the base menu stands at the top left. The hover hook names it "__close".
TRIBUTE_X = (0.34, 0.30, 0.38, 0.26, 0.42)
TRIBUTE_Y = (0.622, 0.60, 0.64, 0.58, 0.66)
CLOSE_X = (0.045, 0.040, 0.050, 0.035, 0.055)
CLOSE_Y = (0.113, 0.100, 0.125, 0.090)


def state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "menu_state")


def wait_for_bar(ctx) -> None:
    """Waits until every menu button is in the bar. On a timeout the state is logged first (it says why)."""
    try:
        ctx.run_until(lambda: all(b["in_bar"] for b in state(ctx)["buttons"]), 60, what="the bar buttons exist", poll_s=1.0)
    except Exception:
        ctx.log.info(f"menu state at the timeout: {state(ctx)}")
        raise


def front(ctx) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)


def find_buttons(ctx) -> dict:
    """Sweeps the bar once. Returns menu id -> (fx, fy) of the first point where the hover hook named the menu."""
    found = {}
    for fy in BAR_Y:
        for fx in BAR_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            hover = state(ctx).get("hover_id")
            if hover in MENUS and hover not in found:
                found[hover] = (fx, fy)
                ctx.log.info(f"button {hover} found at ({fx:.3f}, {fy:.3f})")
            if len(found) == len(MENUS):
                return found
    return found


def find_close(ctx) -> tuple:
    for fy in CLOSE_Y:
        for fx in CLOSE_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if state(ctx).get("hover_id") == "__close":
                ctx.log.info(f"close button found at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered the Close button")


def click_tribute_button(ctx) -> None:
    """A click on a button of the menu content must still act on the menu (the content stands above the backdrop)."""
    for fy in TRIBUTE_Y:
        for fx in TRIBUTE_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(b["name"] == "TributeButton" and b.get("hovered") for b in content_state(ctx, "tribute")["buttons"]):
                ctx.log.info(f"TributeButton found at ({fx:.3f}, {fy:.3f})")
                ctx.click_with_mouse(fx, fy)
                return
    raise AssertionError("the mouse never hovered TributeButton")


def content_state(ctx, menu_id: str) -> dict:
    command = {"raid": "raid_widget_state", "tech": "tech_tree_widget_state", "tribute": "liege_menu_state"}[menu_id]
    return ctx.mod.command(PREFIX + command)


def run(ctx) -> dict:
    expect = ctx.expect
    front(ctx)  # a game window behind another window may be throttled
    wait_for_bar(ctx)
    first = state(ctx)
    ctx.log.info(f"menu state {first}")
    expect.equals("S1 the three menus are registered", [b["id"] for b in first["buttons"]], list(MENUS))
    expect.equals("S1 the bar has no error", first.get("bar_error"), None)
    time.sleep(SETTLE_S)
    front(ctx)
    ctx.screenshot("bottom-bar")

    found = find_buttons(ctx)
    expect.equals("S2 the mouse found a button for each menu", sorted(found), sorted(MENUS))
    if sorted(found) != sorted(MENUS):
        return ctx.result()
    front(ctx)
    ctx.hover_with_mouse(*found["raid"])
    time.sleep(0.5)
    ctx.screenshot("bottom-bar-hover")

    for menu_id in MENUS:
        before = state(ctx)["press_count"]
        ctx.click_with_mouse(*found[menu_id])  # the one click that the rule counts
        ctx.run_until(lambda: state(ctx).get("open_id") == menu_id, 8, what=f"the {menu_id} menu opens", poll_s=0.5)
        time.sleep(SETTLE_S)
        now = state(ctx)
        expect.equals(f"S3 {menu_id}: one click opened the menu", now["press_count"] - before, 1)
        expect.equals(f"S3 {menu_id}: the backdrop is in the viewport", now["blocker"], True)
        inner = content_state(ctx, menu_id)
        expect.equals(f"S3 {menu_id}: the content is in the viewport", inner["in_viewport"], True)
        front(ctx)
        ctx.screenshot(f"menu-{menu_id}")
        expect.equals(f"S3 {menu_id}: the Close button exists", now["close_button"], True)
        if menu_id == "tribute":
            ctx.actions.set_silver(SILVER)
            click_tribute_button(ctx)
            ctx.run_until(lambda: content_state(ctx, "tribute")["tributes"] >= 1, 8, what="a click on a content button acts", poll_s=0.5)
            expect.equals("S5 tribute: one click on the content button sent one tribute", content_state(ctx, "tribute")["tributes"], 1)
            expect.equals("S5 tribute: the menu stays open", state(ctx)["open_id"], "tribute")
            front(ctx)
            ctx.screenshot("menu-tribute-after-click")
        ctx.click_with_mouse(*find_close(ctx))
        ctx.run_until(lambda: not state(ctx)["open"], 8, what=f"the Close button closes the {menu_id} menu", poll_s=0.5)
        expect.equals(f"S4 {menu_id}: the Close click closed the menu", state(ctx)["open"], False)
        expect.equals(f"S4 {menu_id}: the content is gone", content_state(ctx, menu_id)["open"], False)
    return ctx.result()
