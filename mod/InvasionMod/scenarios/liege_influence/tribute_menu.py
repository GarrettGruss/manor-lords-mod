"""add-liege-influence: the tribute menu opens, and a real mouse click on the tribute button sends one tribute.

Needs the pak: `run.py --scenario liege-tribute-menu --new-game --pak InvasionMod`. Real mouse input: no other game at the same time.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

NAME = "liege-tribute-menu"
DESCRIPTION = "Open the liege tribute menu, click the tribute button with the real mouse, check silver and influence, close it. Needs --pak InvasionMod."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "Hover scan and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
HOVER_WAIT_S = 0.2
SILVER = 1000
AMOUNT = 200
# The widget stands at (300, 150) in the viewport. The geometry calls return a zero size, so the scenario finds the button by hover.
SCAN_X = (0.22, 0.26, 0.30, 0.34, 0.38)
SCAN_Y = tuple(round(0.20 + 0.02 * step, 3) for step in range(30))


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_menu_state")


def find_button(ctx, name: str) -> tuple:
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(b["name"] == name and b.get("hovered") for b in menu(ctx)["buttons"]):
                ctx.log.info(f"{name} found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError(f"the mouse never hovered {name}")


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.set_silver(SILVER)
    ctx.mod.command(PREFIX + "liege_menu_close")
    opened = ctx.mod.command(PREFIX + "liege_menu_open")
    expect.equals("the menu opened", opened.get("ok"), True)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    ctx.log.info(f"menu {state}")
    expect.equals("the menu is in the viewport", state["in_viewport"], True)
    expect.equals("the shown texts equal the wanted texts", state["texts"], state["wanted_texts"])
    ctx.screenshot("liege-menu-open")

    before = ctx.mod.command(PREFIX + "liege_state")
    fx, fy = find_button(ctx, "TributeButton")
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: menu(ctx)["tributes"] >= 1, 8, what="the click sends a tribute", poll_s=0.5)
    time.sleep(1.5)  # the labels refresh at most each 500 ms
    after = ctx.mod.command(PREFIX + "liege_state")
    ctx.metric("silver_taken", before["silver"] - after["silver"])
    ctx.metric("influence_gained", after["influence"] - before["influence"])
    expect.equals("one click took the button amount", before["silver"] - after["silver"], AMOUNT)
    expect.equals("influence rose by 20", round(after["influence"] - before["influence"], 2), 20.0)
    expect.equals("exactly one tribute was counted", menu(ctx)["tributes"], 1)
    expect.equals("the influence label shows the new value", menu(ctx)["texts"]["InfluenceText"], menu(ctx)["wanted_texts"]["InfluenceText"])
    ctx.screenshot("liege-menu-after-tribute")

    fx, fy = find_button(ctx, "CloseButton")
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the menu", poll_s=0.5)
    return ctx.result()
