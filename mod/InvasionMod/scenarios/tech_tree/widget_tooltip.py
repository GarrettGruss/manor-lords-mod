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
SCAN_X = tuple(round(0.10 + 0.025 * step, 3) for step in range(18))
SCAN_Y = tuple(round(0.10 + 0.02 * step, 3) for step in range(36))
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


def find_button(ctx, group: str, only_id: str) -> tuple:
    """Returns (fx, fy, row) of the visible button that the mouse hovers (same scan as the scenario tech-tree-widget)."""
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            for row in widget(ctx)[group]:
                if row.get("hovered") and row.get("visibility") == VISIBLE and row.get("id") == only_id:
                    return fx, fy, row
    raise AssertionError(f"the mouse never hovered the {group} button {only_id}")


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
