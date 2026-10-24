"""add-scenario-start-kit: the liege screen button "Request arms shipment" (a real mouse click).

Needs the pak: `run.py --scenario liege-arms-shipment --pak raidmenu` (a fixture). Real mouse input (the Keep is placed with the mouse):
no other game at the same time. It saves nothing. The manor is a harness shortcut (`finish_manor_site`): the test village cannot build a Keep.
Pictures: the button enabled, and the button in the cooldown with the days left.
"""

import time

from runlib import osinput

NAME = "liege-arms-shipment"
DESCRIPTION = "Open the liege screen with a manor and silver, click Request arms shipment, check the goods in the manor, the silver and the cooldown. Needs --pak raidmenu."
LIMIT_S = 500
EXCLUSIVE = True
HIDDEN = True
LONG_REASON = "Places a Keep and clicks with the real mouse."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
HOVER_WAIT_S = 0.2
KEEP = 57
WOOD, PLANKS, RUBBLE = 16, 17, 15
SHIELD, SPEAR = 271, 133
SCAN_X = (0.22, 0.26, 0.30, 0.34, 0.38)
SCAN_Y = tuple(round(0.20 + 0.02 * step, 3) for step in range(30))


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_menu_state")


def front(ctx) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)


def find_button(ctx, name: str) -> tuple:
    front(ctx)
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(b["name"] == name and b.get("hovered") for b in menu(ctx)["buttons"]):
                return fx, fy
    raise AssertionError(f"the mouse never hovered {name}")


def manor_units(ctx, good: int) -> int:
    return ctx.actions.manor_stock(good)


def build_manor(ctx) -> bool:
    """Place a Keep with the real mouse and finish it (shortcut). Returns False when the placement fails (see the notes in the evidence README)."""
    if any(module["built"] for module in ctx.actions.manor_state()["modules"]):
        return True  # the fixture village already has a built manor
    for good in (WOOD, PLANKS, RUBBLE):
        ctx.actions.give_item(good, 100)
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(1.0)
    try:
        ctx.actions.place_building(KEEP)
        ctx.actions.finish_manor_site(KEEP)
        return True
    except Exception as error:  # noqa: BLE001 - the mouse placement can fail on a busy PC
        ctx.log.info(f"no manor: {error}")
        return False


def run(ctx) -> dict:
    expect = ctx.expect
    has_manor = build_manor(ctx)
    ctx.metric("manor_built", 1 if has_manor else 0)
    ctx.actions.set_silver(500)
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("the menu opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    expect.equals("A1 the label offers the shipment", state["arms_label"], "Request arms shipment")
    expect.equals("A1 the shown texts equal the wanted texts", state["texts"], state["wanted_texts"])
    ctx.screenshot("arms-button-enabled")
    fx, fy = find_button(ctx, "ArmsButton")
    silver = ctx.mod.command(PREFIX + "liege_state")["silver"]

    if has_manor:
        shields, spears = manor_units(ctx, SHIELD), manor_units(ctx, SPEAR)
        front(ctx)
        ctx.click_with_mouse(fx, fy)
        ctx.run_until(lambda: menu(ctx)["shipments"] >= 1, 8, what="the click requests a shipment", poll_s=0.5)
        time.sleep(1.5)
        after = ctx.mod.command(PREFIX + "liege_state")
        expect.equals("A2 30 more large shields in the manor", manor_units(ctx, SHIELD) - shields, 30)
        expect.equals("A2 30 more spears in the manor", manor_units(ctx, SPEAR) - spears, 30)
        expect.equals("A2 the silver is 200 lower", silver - after["silver"], 200)
        expect.equals("A3 the days left are 180", after["arms_days_left"], 180)
    else:
        # No manor: the click must fail and cost nothing. Then the cooldown is set by the test helper for the picture.
        front(ctx)
        ctx.click_with_mouse(fx, fy)
        time.sleep(1.5)
        after = ctx.mod.command(PREFIX + "liege_state")
        expect.equals("A2 no manor: the click takes no silver", after["silver"], silver)
        expect.equals("A2 no manor: no cooldown starts", after["arms_last_day"], -1)
        ctx.mod.command(PREFIX + "liege_test_set_arms_day", day=after["day"] - 100)
        after = ctx.mod.command(PREFIX + "liege_state")
        expect.equals("A3 the days left are 80", after["arms_days_left"], 80)
    expect.equals("A3 the button is disabled for the cooldown", after["arms_enabled"], False)
    time.sleep(1.5)  # the label refreshes at most each 500 ms
    expect.equals("A3 the label shows the days left", menu(ctx)["arms_label"], f"Request arms shipment ({int(after['arms_days_left'])} days left)")
    ctx.screenshot("arms-button-cooldown")

    front(ctx)
    ctx.click_with_mouse(fx, fy)
    time.sleep(1.5)
    expect.equals("A4 a click in the cooldown takes no silver", ctx.mod.command(PREFIX + "liege_state")["silver"], after["silver"])

    fx, fy = find_button(ctx, "CloseButton")
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the menu", poll_s=0.5)
    return ctx.result()
