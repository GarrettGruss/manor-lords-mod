"""add-scenario-start-kit: the liege screen button "Request arms shipment" (a real mouse click).

Needs the pak: `run.py --scenario liege-arms-shipment --pak InvasionMod`. Real mouse input: no other game at the same time. It saves nothing.
Two starts (change fix-arms-button-manor, #455):
- a fixture with a built manor (the default fixture): the button is enabled, a real click delivers, then the cooldown look shows;
- `--new-game` (no manor): the button is disabled with "Build a manor first", a real click does nothing.
Pictures: the button enabled, disabled with no manor, and in the cooldown with the days left.
"""

import time

from runlib import osinput

NAME = "liege-arms-shipment"
DESCRIPTION = "Open the liege screen with a manor and silver, click Request arms shipment, check the goods in the manor, the silver and the cooldown. Needs --pak InvasionMod."
LIMIT_S = 500
EXCLUSIVE = True
LONG_REASON = "Places a Keep and clicks with the real mouse."
PREFIX = "InvasionMod."
SETTLE_S = 2.2
HOVER_WAIT_S = 0.2
SHIELD, SPEAR = 271, 133
# The contracts window with no offer (change update-liege-tribute-to-contracts): the arms button is at about (0.19, 0.50), Close below it.
SCAN_X = tuple(round(0.16 + 0.01 * step, 3) for step in range(10))
SCAN_Y = tuple(round(0.44 + 0.01 * step, 3) for step in range(20))


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


def has_built_manor(ctx) -> bool:
    return any(module["built"] for module in ctx.actions.manor_state()["modules"])


def run(ctx) -> dict:
    expect = ctx.expect
    has_manor = has_built_manor(ctx)
    ctx.metric("manor_built", 1 if has_manor else 0)
    ctx.actions.set_silver(500)
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("the menu opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    expect.equals("A1 the label is always the plain label", state["arms_label"], "Request arms shipment")
    reason = "Build a manor first"
    expect.equals("A1 the reason shows under the button only without a manor", reason in state["texts"]["ArmsInfoText"], not has_manor)
    expect.equals("A1 the button look is disabled without a manor", state["arms_disabled"], not has_manor)
    expect.equals("A1 the shown texts equal the wanted texts", {k: state["texts"].get(k) for k in state["wanted_texts"]}, state["wanted_texts"])
    ctx.screenshot("arms-button-enabled" if has_manor else "arms-button-no-manor")
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
        time.sleep(1.5)  # the look refreshes at most each 500 ms
        expect.equals("A3 the look is disabled in the cooldown", menu(ctx)["arms_disabled"], True)
        ctx.screenshot("arms-button-cooldown")
    else:
        # No manor: the click must do nothing and cost nothing.
        front(ctx)
        ctx.click_with_mouse(fx, fy)
        time.sleep(1.5)
        after = ctx.mod.command(PREFIX + "liege_state")
        expect.equals("A2 no manor: the click takes no silver", after["silver"], silver)
        expect.equals("A2 no manor: no cooldown starts", after["arms_last_day"], -1)
        expect.equals("A2 no manor: the shipment counter stays 0", menu(ctx)["shipments"], 0)
        expect.equals("A2 no manor: the reason is the manor", after["arms_reason"], reason)
        fx, fy = find_button(ctx, "CloseButton")
        front(ctx)
        ctx.click_with_mouse(fx, fy)
        ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the menu", poll_s=0.5)
        return ctx.result()
    expect.equals("A3 the button is disabled for the cooldown", after["arms_enabled"], False)
    expect.equals("A3 the reason under the button shows the days left", f"{int(after['arms_days_left'])} days left" in menu(ctx)["texts"]["ArmsInfoText"], True)

 
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    time.sleep(1.5)
    expect.equals("A4 a click in the cooldown takes no silver", ctx.mod.command(PREFIX + "liege_state")["silver"], after["silver"])

    fx, fy = find_button(ctx, "CloseButton")
    front(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the menu", poll_s=0.5)
    return ctx.result()
