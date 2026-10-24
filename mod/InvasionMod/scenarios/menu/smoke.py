"""add-mod-menu-access-rule, task 2.3: one smoke run for all mod menus.

Each registered menu has a button in the game's bottom bar. A real mouse click on the button opens the menu (1 click, no key).
A click on the Close button (bottom middle, the game's Close label style) closes it. A picture is taken of the bar and of each menu.
Each menu pauses the game when it opens and puts back the speed when it closes (change update-mod-menu-close-and-pause). Esc closes
an open menu, and the game's Esc menu does not open on that press; Esc with no mod menu opens the game's Esc menu.
Needs the paks: `run.py --scenario menu-smoke --slot 0 --pak InvasionMod`. Real mouse input: no other game on the slot.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

from runlib import osinput

NAME = "menu-smoke"
DESCRIPTION = "Every mod menu opens from its bottom bar button with one real click, shows its content, and closes. Needs --pak InvasionMod."
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
# The Close button of the base menu stands at the bottom middle (95 percent down). The hover hook names it "__close".
TRIBUTE_X = (0.34, 0.30, 0.38, 0.26, 0.42)
TRIBUTE_Y = (0.622, 0.60, 0.64, 0.58, 0.66)
CLOSE_X = (0.50, 0.48, 0.52, 0.46, 0.54)
CLOSE_Y = (0.95, 0.94, 0.96, 0.93, 0.97)
GAME_SPEED = 2          # speed index 2 = game speed factor 4
GAME_SPEED_FACTOR = 4.0
VK_ESCAPE = 0x1B
ESC_MENU = "mainMenu_widget_C"
COLLAPSED = 1


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


def game_esc_menu_open(ctx) -> bool:
    """True while the game's own Esc menu is on screen (the widget is made on the first Esc and collapsed when it closes)."""
    found = ctx.bridge._result("objects", class_name=ESC_MENU, limit=10)["objects"]
    live = [str(entry).split(" ", 1)[1] for entry in found if " /Engine/Transient" in str(entry)]
    if not live:
        return False
    return ctx.bridge._result("call", ref=live[0], function="GetVisibility", args=[]) != COLLAPSED


def speed_after(ctx, wait_s: float = 1.5) -> float:
    time.sleep(wait_s)
    return ctx.bridge.read_game_speed()


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

    ctx.time.set_speed(GAME_SPEED)
    expect.equals("S0 the game runs at the test speed before the menus", ctx.bridge.read_game_speed(), GAME_SPEED_FACTOR)
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
        expect.equals(f"S6 {menu_id}: the menu paused the game", ctx.bridge.read_game_speed(), 0)
        expect.equals(f"S6 {menu_id}: the speed before the open is stored", now["saved_speed"], GAME_SPEED_FACTOR)
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
        expect.equals(f"S6 {menu_id}: the Close click put back the speed", speed_after(ctx), GAME_SPEED_FACTOR)

    esc_checks(ctx, found["raid"])
    return ctx.result()


def esc_checks(ctx, raid_button: tuple) -> None:
    """Esc closes an open mod menu (the game's Esc menu stays shut); Esc with no mod menu opens the game's Esc menu."""
    expect = ctx.expect
    front(ctx)
    ctx.click_with_mouse(*raid_button)
    ctx.run_until(lambda: state(ctx).get("open_id") == "raid", 8, what="the raid menu opens for the Esc test", poll_s=0.5)
    time.sleep(SETTLE_S)
    ctx.press_key(VK_ESCAPE)
    ctx.run_until(lambda: not state(ctx)["open"], 8, what="Esc closes the raid menu", poll_s=0.5)
    time.sleep(2.0)  # the guard looks for the game's Esc menu for 1.5 s
    after = state(ctx)
    front(ctx)
    ctx.screenshot("esc-closed-menu")
    expect.equals("E1 Esc closed the open mod menu", after["open"], False)
    expect.equals("E1 the Esc handler ran once", after["esc_closes"], 1)
    expect.equals("E2 the game's Esc menu is not on screen", game_esc_menu_open(ctx), False)
    expect.equals("E3 Esc put back the speed", ctx.bridge.read_game_speed(), GAME_SPEED_FACTOR)

    ctx.press_key(VK_ESCAPE)  # no mod menu is open: the game opens its own menu
    time.sleep(1.5)
    expect.equals("E4 Esc with no mod menu opens the game's Esc menu", game_esc_menu_open(ctx), True)
    expect.equals("E4 the mod did not close it", state(ctx)["esc_closes"], 1)
    front(ctx)
    ctx.screenshot("esc-game-menu")
    ctx.press_key(VK_ESCAPE)  # close the game's menu again
    time.sleep(1.5)
    expect.equals("E5 a second Esc closes the game's Esc menu", game_esc_menu_open(ctx), False)

    # A game that was paused stays paused after a menu closes.
    ctx.pause()
    ctx.mod.command(PREFIX + "menu_open", id="raid")
    time.sleep(SETTLE_S)
    expect.equals("S7 opened while paused: saved speed is paused", state(ctx)["saved_speed"], 0)
    ctx.mod.command(PREFIX + "menu_close")
    expect.equals("S7 a menu closed after a pause: the game stays paused", speed_after(ctx), 0)
