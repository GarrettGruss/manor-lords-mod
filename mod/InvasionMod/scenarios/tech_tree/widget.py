"""M12 iteration 02, U1 to U6: the tech tree menu shows the data driven tree and takes real mouse clicks.

Needs the pak: `run.py --scenario tech-tree-widget --pak techmenu`. Real mouse input: no other game at the same time.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

NAME = "tech-tree-widget"
DESCRIPTION = "Open the tech tree menu, pick a path and a node with real mouse clicks, check the node positions. Needs --pak techmenu."
LIMIT_S = 600
EXCLUSIVE = True
LONG_REASON = "Hover scans with a real mouse, many short waits."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
HOVER_WAIT_S = 0.18
STEP_X = 180
STEP_Y = 60
# The geometry calls of the widget return a zero size in the real game, so the scenario finds a button by hover.
SCAN_X = tuple(round(0.10 + 0.025 * step, 3) for step in range(18))
SCAN_Y = tuple(round(0.10 + 0.02 * step, 3) for step in range(36))


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def hovered(state: dict, group: str) -> list:
    return [row for row in state[group] if row.get("hovered") and row.get("visibility") == 0]


def find_button(ctx, group: str, only_id: str | None = None) -> tuple:
    """Returns (fx, fy, row) of the first visible button of the group that the mouse hovers."""
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            rows = [row for row in hovered(widget(ctx), group) if only_id is None or row.get("id") == only_id]
            if rows:
                ctx.log.info(f"{group} button {rows[0].get('id', rows[0].get('index'))} found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy, rows[0]
    raise AssertionError(f"the mouse never hovered a visible {group} button (wanted {only_id})")


def check_open(ctx) -> None:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    opened = ctx.mod.command(PREFIX + "tech_tree_widget_open")
    expect.equals("U1 the widget opened", opened.get("ok"), True)
    time.sleep(SETTLE_S)
    state = widget(ctx)
    ctx.log.info(f"widget {state}")
    expect.equals("U1 the widget is in the viewport", state["in_viewport"], True)
    expect.equals("U2 the shown lines equal the wanted lines", state["lines"], state["wanted_lines"])
    visible = [row for row in state["nodes"] if row["visibility"] == 0]
    expect.equals("U3 one visible button for each node of the data", len(visible), len(tree(ctx)["nodes"]))
    ctx.screenshot("tech-tree-widget")


def check_positions(ctx) -> None:
    """The layout data of tree.json moves the buttons (x and y of the canvas slot)."""
    layout = {row["id"]: row["layout"] for row in tree(ctx)["nodes"]}
    wrong = []
    for row in widget(ctx)["nodes"]:
        if row.get("id") is None:
            continue
        want = (layout[row["id"]]["x"] * STEP_X, layout[row["id"]]["y"] * STEP_Y)
        if (row.get("x"), row.get("y")) != want:
            wrong.append((row["id"], (row.get("x"), row.get("y")), want))
    ctx.check("U4 every node stands at its layout position", not wrong, wrong)


def check_clicks(ctx) -> None:
    expect = ctx.expect
    fx, fy, row = find_button(ctx, "paths")
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: tree(ctx)["path"] != "none", 8, what="the click chooses the path", poll_s=0.5)
    expect.equals("U5 a path click chose the path of the button", tree(ctx)["path"], "oppression" if row["index"] == 1 else "prosperity")
    ctx.actions.set_settlement_level(1)
    ctx.run_until(lambda: tree(ctx)["slots"] == 1, 15, what="one node slot")
    time.sleep(SETTLE_S)
    first = tree(ctx)["nodes"]
    first_id = next(node["id"] for node in first if node["path"] == tree(ctx)["path"] and not node["requires"])
    fx, fy, _ = find_button(ctx, "nodes", only_id=first_id)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: first_id in tree(ctx)["unlocked"], 8, what="the click unlocks the node", poll_s=0.5)
    expect.equals("U6 a node click unlocked the node", tree(ctx)["unlocked"], [first_id])
    time.sleep(SETTLE_S)
    shown = widget(ctx)
    expect.equals("U6 the node label shows the unlock mark", next(r["label"] for r in shown["nodes"] if r.get("id") == first_id).startswith("[x] "), True)
    ctx.screenshot("tech-tree-widget-unlocked")


def run(ctx) -> dict:
    check_open(ctx)
    check_positions(ctx)
    check_clicks(ctx)
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
