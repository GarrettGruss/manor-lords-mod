"""Change add-tech-tooltip: the tech tree menu sets a tooltip text on each node and law button.

Needs the pak: `run.py --scenario tech-tree-widget-tooltip --pak InvasionMod`. Part 1 reads the tooltip property (no mouse).
Part 2 hovers with the real OS mouse and takes a picture (needs exclusive use of the screen). It saves nothing.
"""

import time

NAME = "tech-tree-widget-tooltip"
DESCRIPTION = "Open the tech tree menu, read the tooltip text of node and law buttons, hover a node and a law with the real mouse. Needs --pak InvasionMod."
LIMIT_S = 600
EXCLUSIVE = True
LONG_REASON = "Hover scans with a real mouse, many short waits."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
TOOLTIP_WAIT_S = 2.0
VISIBLE = 0
HOVER_WAIT_S = 0.18
SCAN_X = tuple(round(0.10 + 0.025 * step, 3) for step in range(30))
SCAN_Y = tuple(round(0.10 + 0.02 * step, 3) for step in range(40))

# Where a control of the window is on the screen, as a fraction of the game window. Measured from the pictures of the run
# 20261028-033058-6580 (window 1302 x 776): the window canvas starts at (193, 125) and one canvas pixel is 0.806 x 0.8 screen pixels.
WINDOW_X0, WINDOW_Y0, WINDOW_KX, WINDOW_KY = 0.148, 0.161, 0.000619, 0.001031
BUTTON_SIZE = {"paths": (124, 32), "nodes": (216, 102), "laws": (66, 24), "strip": (94, 32)}


def hint_point(group: str, row: dict) -> tuple:
    """Fraction of the game window at the middle of a button (x and y of the row are the canvas position of its Border)."""
    width, height = BUTTON_SIZE[group]
    return round(WINDOW_X0 + WINDOW_KX * (row["x"] + width / 2), 3), round(WINDOW_Y0 + WINDOW_KY * (row["y"] + height / 2), 3)
EXPECT_NODES = {
    "fair_courts": ["Approval +5", "Opens vassal policy light"],
    "amnesty": ["Buy-back price -50%", "Manor storage capacity +200"],
}
EXPECT_LAWS = {
    "militia_charter": ["Militia attack +5%", "Approval +2"],
    "trade_pacts": ["Tribute share +25%"],
}


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def hovered_rows(state: dict, group: str) -> list:
    return [row for row in state[group] if row.get("hovered") and row.get("visibility") == VISIBLE]


def find_button(ctx, group: str, only_id: str) -> tuple:
    """Returns (fx, fy, row) of the visible button of the group that the mouse hovers. It tries the expected point of each visible
    button first, and scans the window only when that fails (the geometry calls of the widget return a zero size in the real game)."""
    rows = [row for row in widget(ctx)[group] if row.get("visibility") == 0 and row.get("id") == only_id]
    for row in rows:
        fx, fy = hint_point(group, row)
        ctx.hover_with_mouse(fx, fy)
        time.sleep(HOVER_WAIT_S)
        found = [r for r in hovered_rows(widget(ctx), group) if r.get("id") == only_id]
        if found:
            ctx.log.info(f"{group} button {found[0].get('id', found[0].get('index'))} found at the expected point ({fx:.3f}, {fy:.3f})")
            return fx, fy, found[0]
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            found = [r for r in hovered_rows(widget(ctx), group) if r.get("id") == only_id]
            if found:
                ctx.log.info(f"{group} button {found[0].get('id', found[0].get('index'))} found by scan at ({fx:.3f}, {fy:.3f})")
                return fx, fy, found[0]
    raise AssertionError(f"the mouse never hovered a visible {group} button (wanted {only_id})")


def check_tooltips(ctx, name: str, rows: list, expected: dict) -> None:
    by_id = {row.get("id"): row for row in rows}
    for row_id, wanted in expected.items():
        text = (by_id.get(row_id) or {}).get("tooltip")
        ctx.check(f"{name} tooltip of {row_id}", text == "\n".join(wanted), text)


def hover_picture(ctx, group: str, row_id: str, picture: str) -> None:
    fx, fy, _ = find_button(ctx, group, only_id=row_id)
    ctx.hover_with_mouse(fx, fy)
    time.sleep(TOOLTIP_WAIT_S)
    ctx.screenshot(picture)


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.check("T1 the widget opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok") is True)
    time.sleep(SETTLE_S)
    state = widget(ctx)
    ctx.check("T1 no tooltip error", state.get("tooltip_error") is None, state.get("tooltip_error"))
    nodes = state["nodes"]
    ctx.check("T2 every visible node button has a tooltip", all(r["tooltip"] for r in nodes if r["visibility"] == VISIBLE), nodes)
    ctx.check("T2 hidden buttons have no tooltip", all(not r["tooltip"] for r in nodes if r["visibility"] != VISIBLE), nodes)
    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="path", index=2)
    ensure_picks(ctx, 2)
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)  # the law buttons show only for unlocked techs
    time.sleep(SETTLE_S)
    state = widget(ctx)
    check_tooltips(ctx, "T3", state["nodes"], EXPECT_NODES)
    check_tooltips(ctx, "T4", state["laws"], EXPECT_LAWS)
    ctx.metric("tooltip_nodes", sum(1 for r in state["nodes"] if r["tooltip"]))
    ctx.screenshot("tech-tree-widget-tooltip-menu")
    try:
        hover_picture(ctx, "nodes", "amnesty", "tech-tree-tooltip-node")
        hover_picture(ctx, "laws", "trade_pacts", "tech-tree-tooltip-law")
    except Exception as problem:  # the real mouse is optional here; the property checks above stand
        ctx.log.info(f"real hover failed: {problem}")
        ctx.metric("real_hover_failed", 1)
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()


def ensure_picks(ctx, wanted: int) -> None:
    """Wait for the start pick, then add picks (a test command) until `wanted` picks are earned."""
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    missing = wanted - ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
