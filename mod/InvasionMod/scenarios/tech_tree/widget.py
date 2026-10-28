"""M12 iteration 02, U1 to U6: the tech tree menu shows the data driven tree and takes real mouse clicks.

Needs the pak: `run.py --scenario tech-tree-widget --pak InvasionMod`. Real mouse input: no other game at the same time.
It saves nothing. Do not run the UE editor while a screenshot is taken.
"""

import time

NAME = "tech-tree-widget"
DESCRIPTION = "Open the tech tree menu, pick a path and a node with real mouse clicks, check the node positions. Needs --pak InvasionMod."
LIMIT_S = 600
EXCLUSIVE = True
LONG_REASON = "Hover scans with a real mouse, many short waits."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
HOVER_WAIT_S = 0.18
ORIGIN_X, ORIGIN_Y = 160, 100
STEP_X = 248
STEP_Y = 160
# The geometry calls of the widget return a zero size in the real game, so the scenario finds a button by hover.
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


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def hovered(state: dict, group: str) -> list:
    return [row for row in state[group] if row.get("hovered") and row.get("visibility") == 0]


def find_button(ctx, group: str, only_id: str | None = None) -> tuple:
    """Returns (fx, fy, row) of the visible button of the group that the mouse hovers. It tries the expected point of each visible
    button first, and scans the window only when that fails (the geometry calls of the widget return a zero size in the real game)."""
    rows = [row for row in widget(ctx)[group] if row.get("visibility") == 0 and (only_id is None or row.get("id") == only_id)]
    for row in rows:
        fx, fy = hint_point(group, row)
        ctx.hover_with_mouse(fx, fy)
        time.sleep(HOVER_WAIT_S)
        found = [r for r in hovered(widget(ctx), group) if only_id is None or r.get("id") == only_id]
        if found:
            ctx.log.info(f"{group} button {found[0].get('id', found[0].get('index'))} found at the expected point ({fx:.3f}, {fy:.3f})")
            return fx, fy, found[0]
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            found = [r for r in hovered(widget(ctx), group) if only_id is None or r.get("id") == only_id]
            if found:
                ctx.log.info(f"{group} button {found[0].get('id', found[0].get('index'))} found by scan at ({fx:.3f}, {fy:.3f})")
                return fx, fy, found[0]
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
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    time.sleep(SETTLE_S)
    state = widget(ctx)
    expect.equals("U2 the shown picks counter equals the wanted counter", state["picks"], state["wanted_picks"])
    expect.equals("U2 the counter shows the free picks", state["picks"], "Tech picks: 1 free (0 of 1 used)")
    visible = [row for row in state["nodes"] if row["visibility"] == 0]
    expect.equals("U3 one visible button for each node of the data (8 path nodes and 3 common techs)", len(visible), len(tree(ctx)["nodes"]) + len(tree(ctx)["common_nodes"]))
    ctx.screenshot("tech-tree-widget")


def check_positions(ctx) -> None:
    """The layout data of tree.json moves the buttons (x and y of the canvas slot)."""
    layout = {row["id"]: row["layout"] for row in tree(ctx)["nodes"]}
    for column, row in enumerate(tree(ctx)["common_nodes"]):
        layout[row["id"]] = {"x": column, "y": 2}  # the common techs stand in the third row
    wrong = []
    for row in widget(ctx)["nodes"]:
        if row.get("id") is None:
            continue
        want = (ORIGIN_X + layout[row["id"]]["x"] * STEP_X, ORIGIN_Y + layout[row["id"]]["y"] * STEP_Y)
        if (row.get("x"), row.get("y")) != want:
            wrong.append((row["id"], (row.get("x"), row.get("y")), want))
    ctx.check("U4 every node stands at its layout position", not wrong, wrong)


def check_clicks(ctx) -> None:
    expect = ctx.expect
    fx, fy, row = find_button(ctx, "paths")
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: tree(ctx)["path"] != "none", 8, what="the click chooses the path", poll_s=0.5)
    expect.equals("U5 a path click chose the path of the button", tree(ctx)["path"], "oppression" if row["index"] == 1 else "prosperity")
    ensure_picks(ctx, 1)
    time.sleep(SETTLE_S)
    first = tree(ctx)["nodes"]
    first_id = next(node["id"] for node in first if node["path"] == tree(ctx)["path"] and not node["requires"])
    fx, fy, _ = find_button(ctx, "nodes", only_id=first_id)
    ctx.click_with_mouse(fx, fy)
    ctx.run_until(lambda: first_id in tree(ctx)["unlocked"], 8, what="the click unlocks the node", poll_s=0.5)
    expect.equals("U6 a node click unlocked the node", tree(ctx)["unlocked"], [first_id])
    time.sleep(SETTLE_S)
    shown = widget(ctx)
    expect.equals("U7 the counter shows the used pick", shown["picks"], "Tech picks: 0 free (1 of 1 used)")
    ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=1)  # a new spring gives one pick
    time.sleep(SETTLE_S)
    expect.equals("U8 a new pick raises the counter on the next refresh", widget(ctx)["picks"], "Tech picks: 1 free (1 of 2 used)")
    expect.equals("U6 the node label shows the unlock mark", next(r["label"] for r in shown["nodes"] if r.get("id") == first_id).startswith("[x] "), True)
    ctx.screenshot("tech-tree-widget-unlocked")


def run(ctx) -> dict:
    check_open(ctx)
    check_positions(ctx)
    check_clicks(ctx)
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()


def ensure_picks(ctx, wanted: int) -> None:
    """Wait for the start pick, then add picks (a test command) until `wanted` picks are earned."""
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    missing = wanted - ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
