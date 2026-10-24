"""M02 iteration 05, W1 to W4: the raid widget shows the raid information and F8 toggles it.

The three difficulty buttons were removed (change add-scenario-settings-menu): the player picks the difficulty in the scenario
settings menu. Needs the pak: `run.py --scenario invasion-raid-widget --pak InvasionMod`. Real key input: no other game at the same time.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

NAME = "invasion-raid-widget"
DESCRIPTION = "Open the raid widget, check its lines (no difficulty buttons), toggle it with F8. Needs --pak InvasionMod."
LIMIT_S = 300
EXCLUSIVE = True
LONG_REASON = "Waits for the widget and real key input."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
VK_F8 = 0x77


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "raid_widget_state")


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
    prefixes = ["Yearly raid", "Subjugation raid", "Great raid", "Raid levels", "Terms"]
    expect.equals("W2 the five lines are in order", [line.split(":")[0] for line in state["lines"]], prefixes)
    expect.equals("W3 the widget has no difficulty buttons", "buttons" in state, False)
    ctx.screenshot("raid-widget")

    ctx.press_key(VK_F8)
    expect.equals("W4 F8 closes the widget", widget(ctx)["open"], False)
    ctx.press_key(VK_F8)
    expect.equals("W4 F8 opens the widget", widget(ctx)["open"], True)
    ctx.mod.command(PREFIX + "raid_widget_close")
    return ctx.result()
