"""Spec 34: real single clicks on a tech tree menu button each reach the click handler exactly once.

Needs the pak: `run.py --scenario tech-tree-widget-clicks --pak InvasionMod`. Real mouse input: no other game at the same time.
The click button of the menu is a Blueprint widget whose OnClicked event is a hook event (shared module HarnessClickHooks).
The handler counts each press in `clicks`, also a refused one. It saves nothing.
"""

import time

NAME = "tech-tree-widget-clicks"
DESCRIPTION = "Click a law button of the tech tree menu with the real mouse 10 times, one click each second. Each click counts once. Needs --pak InvasionMod."
LIMIT_S = 600
EXCLUSIVE = True
LONG_REASON = "Hover scan and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
CLICKS = 10
GAP_S = 1.0
HOVER_WAIT_S = 0.15
SCAN_X = (0.22, 0.24, 0.26, 0.28, 0.30, 0.32)
SCAN_Y = tuple(round(0.90 + 0.01 * step, 2) for step in range(8))


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def find_law_button(ctx) -> tuple:
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(row.get("hovered") and row.get("visibility") == 0 for row in widget(ctx)["laws"]):
                ctx.log.info(f"law button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered a visible law button")


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.expect.equals("the widget opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok"), True)
    time.sleep(SETTLE_S)
    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="path", index=2)  # the laws need a path and two unlocked nodes
    ctx.actions.set_settlement_level(2)
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["slots"] >= 2, 15, what="two node slots")
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    time.sleep(SETTLE_S)
    ctx.screenshot("tech-tree-widget-clicks")
    fx, fy = find_law_button(ctx)
    before = widget(ctx)["clicks"]
    for _ in range(CLICKS):
        ctx.click_with_mouse(fx, fy)
        time.sleep(GAP_S)
    time.sleep(SETTLE_S)
    counted = widget(ctx)["clicks"] - before
    ctx.log.info(f"clicks counted {counted} of {CLICKS}")
    ctx.metric("clicks_sent", CLICKS)
    ctx.metric("clicks_counted", counted)
    ctx.expect.equals("each real click was counted exactly once", counted, CLICKS)
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
