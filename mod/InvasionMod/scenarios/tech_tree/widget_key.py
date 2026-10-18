"""M12 fix: the real F9 key opens and closes the tech tree menu and the game keeps answering.

Needs the pak: `run.py --scenario tech-tree-widget-key --pak techmenu`. Real keyboard input only.
The menu is never opened by command, so the key path is the only way in.
"""

import time

NAME = "tech-tree-widget-key"
DESCRIPTION = "Press the real F9 key to open and close the tech tree menu, then check the bridge answers. Needs --pak techmenu."
LIMIT_S = 300
EXCLUSIVE = True
LONG_REASON = "Waits for the widget and real keyboard input."
PREFIX = "InvasionMod."
VK_F9 = 0x78
SETTLE_S = 1.5


def state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def run(ctx) -> dict:
    expect = ctx.expect
    expect.equals("K0 the menu starts closed", state(ctx)["open"], False)
    ctx.press_key(VK_F9)
    time.sleep(SETTLE_S)
    after_open = state(ctx)  # a hung game thread makes this command time out
    expect.equals("K1 F9 opens the menu", after_open["open"], True)
    expect.equals("K1 the menu is in the viewport", after_open["in_viewport"], True)
    expect.equals("K2 the shown lines equal the wanted lines", after_open["lines"], after_open["wanted_lines"])
    ctx.screenshot("tech-menu-key-open")
    ctx.press_key(VK_F9)
    time.sleep(SETTLE_S)
    expect.equals("K3 F9 closes the menu", state(ctx)["open"], False)
    ctx.press_key(VK_F9)
    time.sleep(SETTLE_S)
    expect.equals("K4 F9 opens the menu again", state(ctx)["open"], True)
    ctx.press_key(VK_F9)
    time.sleep(SETTLE_S)
    expect.equals("K5 F9 closes the menu again", state(ctx)["open"], False)
    return ctx.result()
