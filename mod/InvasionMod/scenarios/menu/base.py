"""add-mod-menu-access-rule, task 2.3: the base menu in the real game (bottom bar, fullscreen backdrop, click blocking).

The camera is moved over a building, so a click at the screen centre would select it (the game opens a panel).
1. A real click on the bar button opens the menu (the content stands over the centre).
2. Menu open: a real click at the centre must not open the building panel. The picture shows it. The menu stays open.
3. Menu closed: the same click opens the panel (the control).
Needs the paks: `run.py --scenario menu-base --slot 0 --pak InvasionMod`. Real mouse input: no other game on the slot.
The menu pauses the game on open and puts back the speed on close (change update-mod-menu-close-and-pause): the scenario runs the game
at speed 2 before the open. It saves nothing. Options: POINT=x,y (the world click point, default 0.5,0.5), MENU (raid, tech or tribute; default tribute).
"""

import time

from runlib import osinput

NAME = "menu-base"
DESCRIPTION = "Base menu: bar button opens the menu, the backdrop covers the screen, a click does not reach a building. Needs --pak InvasionMod."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "Hover sweep over the bottom bar and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.2
HOVER_WAIT_S = 0.2
BAR_X = tuple(round(0.30 + 0.01 * step, 3) for step in range(41))
BAR_Y = (0.945, 0.96)
GAME_SPEED = 2          # speed index 2 = game speed factor 4
GAME_SPEED_FACTOR = 4.0


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


def find_button(ctx, menu_id: str) -> tuple:
    for fy in BAR_Y:
        for fx in BAR_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if state(ctx).get("hover_id") == menu_id:
                ctx.log.info(f"button {menu_id} found at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError(f"the mouse never hovered the {menu_id} bar button")


def run(ctx) -> dict:
    expect = ctx.expect
    menu_id = ctx.variant_option("MENU", "tribute")
    px, py = (float(part) for part in ctx.variant_option("POINT", "0.5,0.5").split(","))
    front(ctx)  # a game window behind another window may be throttled
    wait_for_bar(ctx)
    focused = ctx.commands.send("ui_probe", action="focus", name="")
    ctx.log.info(f"focus {focused}")
    expect.equals("B0 the camera moved over a building", focused.get("ok"), True)
    time.sleep(2.0)

    fx, fy = find_button(ctx, menu_id)
    ctx.time.set_speed(GAME_SPEED)
    front(ctx)
    ctx.screenshot("before-open")
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: state(ctx).get("open_id") == menu_id, 8, what=f"the {menu_id} menu opens", poll_s=0.5)
    time.sleep(SETTLE_S)
    opened = state(ctx)
    expect.equals("B1 one bar click opened the menu", opened["press_count"], 1)
    expect.equals("B2 the backdrop is Visible (hit testable)", opened["blocker_visibility"], 0)
    expect.equals("B3 the menu paused the game", ctx.bridge.read_game_speed(), 0)
    expect.equals("B3 the speed before the open is stored", opened["saved_speed"], GAME_SPEED_FACTOR)
    front(ctx)
    ctx.screenshot("menu-open")

    ctx.hover_with_mouse(px, py)
    time.sleep(0.4)
    ctx.click_with_mouse(px, py)
    time.sleep(1.5)
    after = state(ctx)
    ctx.log.info(f"after the world click with the menu open: {after}")
    ctx.metric("menu_still_open", 1 if after["open"] else 0)
    front(ctx)
    ctx.screenshot("click-with-menu")

    if after["open"]:
        ctx.mod.command(PREFIX + "menu_close")
        time.sleep(0.8)
        expect.equals("B4 the close put back the speed", ctx.bridge.read_game_speed(), GAME_SPEED_FACTOR)
    ctx.hover_with_mouse(px, py)
    time.sleep(0.4)
    ctx.click_with_mouse(px, py)
    time.sleep(1.5)
    front(ctx)
    ctx.screenshot("control-click-no-menu")
    return ctx.result()
