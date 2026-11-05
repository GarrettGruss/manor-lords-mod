"""Spec 34: real single clicks on a tech tree menu button each reach the click handler exactly once.

Needs the pak: `run.py --scenario tech-tree-widget-clicks --pak InvasionMod`. Real mouse input: no other game at the same time.
The click button of the menu is a Blueprint widget whose OnClicked event is a hook event (shared module HarnessClickHooks).
The handler counts each press in `clicks`, also a refused one. It saves nothing.
"""

import time

NAME = "tech-tree-widget-clicks"
DESCRIPTION = "Click a node button of the tech tree menu with the real mouse 10 times, one click each second. Each click counts once. Needs --pak InvasionMod."
LIMIT_S = 600
EXCLUSIVE = True
LONG_REASON = "Hover scan and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
CLICKS = 10
GAP_S = 1.0
HOVER_WAIT_S = 0.15
SCAN_X = tuple(round(0.20 + 0.02 * step, 3) for step in range(24))
SCAN_Y = tuple(round(0.30 + 0.02 * step, 3) for step in range(30))
# Where a node button is on the screen, as a fraction of the game window (measured from run 20261028-033058-6580, window 1302 x 776).
WINDOW_X0, WINDOW_Y0, WINDOW_KX, WINDOW_KY = 0.148, 0.161, 0.000619, 0.001031
NODE_BUTTON_SIZE = (216, 102)


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def hovered_node(ctx) -> bool:
    return any(row.get("hovered") and row.get("visibility") == 0 for row in widget(ctx)["nodes"])


def find_node_button(ctx) -> tuple:
    """The expected point of each visible node button first, then a scan of the window."""
    for row in widget(ctx)["nodes"]:
        if row.get("visibility") != 0:
            continue
        fx = round(WINDOW_X0 + WINDOW_KX * (row["x"] + NODE_BUTTON_SIZE[0] / 2), 3)
        fy = round(WINDOW_Y0 + WINDOW_KY * (row["y"] + NODE_BUTTON_SIZE[1] / 2), 3)
        ctx.hover_with_mouse(fx, fy)
        time.sleep(HOVER_WAIT_S)
        if hovered_node(ctx):
            ctx.log.info(f"node button found at the expected point ({fx:.3f}, {fy:.3f})")
            return fx, fy
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if hovered_node(ctx):
                ctx.log.info(f"node button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered a visible node button")


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.expect.equals("the widget opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok"), True)
    time.sleep(SETTLE_S)
    time.sleep(SETTLE_S)  # the node buttons show from the start; a click on one without a path is refused, and a refused click counts too
    ctx.screenshot("tech-tree-widget-clicks")
    fx, fy = find_node_button(ctx)
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


def ensure_picks(ctx, wanted: int) -> None:
    """Wait for the start pick, then add picks (a test command) until `wanted` picks are earned."""
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    missing = wanted - ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
