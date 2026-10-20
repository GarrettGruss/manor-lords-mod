"""Spike 308: a Lua-made "Mods" button in the viewport opens the raid menu with one real mouse click. Hidden spike."""

import time

NAME = "spike-ui-entry-button"
DESCRIPTION = "Spike 308: put a Mods button in the viewport, click it with the real mouse, check that the raid menu opens. Needs --pak raidmenu."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "Hover scan and real mouse clicks."
HIDDEN = True
PREFIX = "InvasionMod."
HOVER_WAIT_S = 0.2
SCAN_X = tuple(round(0.05 + 0.012 * i, 3) for i in range(14))
SCAN_Y = tuple(round(0.05 + 0.012 * i, 3) for i in range(14))


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "raid_widget_close")
    opened = ctx.mod.command(PREFIX + "spike_entry_open")
    ctx.log.info(f"entry open {opened}")
    ctx.expect.equals("the entry button was made", opened.get("ok"), True)
    time.sleep(1.5)
    ctx.screenshot("entry-button-before")
    found = None
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if ctx.mod.command(PREFIX + "spike_entry_state").get("hovered"):
                found = (fx, fy)
                break
        if found:
            break
    ctx.expect.equals("the mouse hovered the entry button", found is not None, True)
    ctx.click_with_mouse(*found)
    time.sleep(2.0)
    state = ctx.mod.command(PREFIX + "spike_entry_state")
    ctx.log.info(f"after click {state}")
    ctx.expect.equals("one click was counted", state["clicks"], 1)
    ctx.expect.equals("the raid menu is open", ctx.mod.command(PREFIX + "raid_widget_state")["open"], True)
    ctx.screenshot("entry-button-after-click")
    return ctx.result()
