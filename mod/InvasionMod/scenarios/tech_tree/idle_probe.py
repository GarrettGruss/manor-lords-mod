"""Spec 34 spike (temporary): open the tech menu and wait with the mouse still."""

import time

NAME = "tech-tree-idle-probe"
DESCRIPTION = "Spike for spec 34: open the tech menu, wait 300 s. Needs --pak techmenu."
LIMIT_S = 500
EXCLUSIVE = False
LONG_REASON = "Waits."
PREFIX = "InvasionMod."


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.expect.equals("opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok"), True)
    for _ in range(600):
        time.sleep(0.5)
        state = ctx.mod.command(PREFIX + "tech_tree_widget_state")
    ctx.expect.equals("still open", state["open"], True)
    return ctx.result()
