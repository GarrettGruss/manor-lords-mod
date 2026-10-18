"""M02 iteration 05, W1 to W4: the raid widget shows the raid information and a click picks the difficulty.

Needs the pak: `run.py --scenario invasion-raid-widget --pak raidmenu`. Real mouse input: no other game at the same time.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

from runlib import osinput

NAME = "invasion-raid-widget"
DESCRIPTION = "Open the raid widget, check its lines, pick the difficulty with a real mouse click, toggle it with F8. Needs --pak raidmenu."
LIMIT_S = 300
EXCLUSIVE = True
LONG_REASON = "Waits for the widget and real mouse input."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
VK_F8 = 0x77
HOVER_WAIT_S = 0.2
# The geometry calls of the widget return a zero size in the real game, so the scenario finds a difficulty button by hover.
# The scan covers the lower left of the window, where the widget stands (position 300, 200 plus the five text lines).
SCAN_X = (0.34, 0.28, 0.40, 0.22, 0.46)
SCAN_Y = tuple(round(0.30 + 0.02 * step, 3) for step in range(34))


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "raid_widget_state")


def find_button(ctx) -> tuple:
    """Returns (fx, fy, value) of the first difficulty button the mouse hovers."""
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            hovered = [b["value"] for b in widget(ctx)["buttons"] if b.get("hovered")]
            if hovered:
                ctx.log.info(f"button {hovered[0]} found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy, hovered[0]
    raise AssertionError("the mouse never hovered a difficulty button")


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "raid_widget_close")
    opened = ctx.mod.command(PREFIX + "raid_widget_open")
    expect.equals("W1 the widget opened", opened.get("ok"), True)
    time.sleep(SETTLE_S)  # the widget needs a frame before it is painted
    state = widget(ctx)
    ctx.log.info(f"widget {state}")
    expect.equals("W1 the widget is in the viewport", state["in_viewport"], True)
    expect.equals("W2 the shown lines equal the wanted lines", state["lines"], state["wanted_lines"])
    prefixes = ["Next raid", "Size estimate", "Great raid", "Difficulty", "Terms"]
    expect.equals("W2 the five lines are in order", [line.split(":")[0] for line in state["lines"]], prefixes)
    expect.equals("W2 the difficulty is not picked yet", state["lines"][3].endswith("(not picked yet)"), True)
    ctx.screenshot("raid-widget")

    fx, fy, value = find_button(ctx)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "invasion_difficulty_state")["chosen"], 8, what="the click picks the difficulty", poll_s=0.5)
    expect.equals("W3 a click picked the difficulty of the button", ctx.mod.command(PREFIX + "invasion_difficulty_state")["difficulty"], value)
    time.sleep(SETTLE_S)
    after = widget(ctx)
    expect.equals("W3 the difficulty line shows the pick", after["lines"][3], f"Difficulty: {value}")
    ctx.screenshot("raid-widget-picked")

    ctx.press_key(VK_F8)
    expect.equals("W4 F8 closes the widget", widget(ctx)["open"], False)
    ctx.press_key(VK_F8)
    expect.equals("W4 F8 opens the widget", widget(ctx)["open"], True)
    ctx.mod.command(PREFIX + "raid_widget_close")
    return ctx.result()
