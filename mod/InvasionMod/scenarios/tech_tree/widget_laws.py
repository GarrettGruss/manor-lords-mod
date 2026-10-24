"""M12 iteration 05: the tech tree menu lists the laws and its law buttons work. No real mouse.

Needs the pak: `run.py --scenario tech-tree-widget-laws --pak InvasionMod`. The scenario calls the same handler that a click calls
(command tech_tree_widget_press). Real mouse clicks on the law buttons are open (issue #203). It saves nothing.
"""

import time

NAME = "tech-tree-widget-laws"
DESCRIPTION = "Open the tech tree menu, check the law lines and labels, enact and repeal laws through the button handlers. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 1.0
VISIBLE = 0
LAW_ORDER = ["militia_charter", "trade_pacts", "pay_off_warbands"]


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def press(ctx, kind: str, index: int) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_press", kind=kind, index=index)


def law_rows(ctx) -> list:
    return sorted(widget(ctx)["laws"], key=lambda row: row["index"])


def check_matches_state(ctx, name: str, in_force: list) -> None:
    state = widget(ctx)
    ctx.check(f"{name} the laws line equals the wanted line", state["laws_line"] == state["wanted_laws_line"], state["laws_line"])
    ctx.check(f"{name} the line counts the laws in force", f"{len(in_force)} of 2" in state["laws_line"], state["laws_line"])
    rows = law_rows(ctx)
    ctx.check(f"{name} three visible law buttons", [row["visibility"] for row in rows] == [VISIBLE] * 3, rows)
    ctx.check(f"{name} the law ids follow the tree data", [row["id"] for row in rows] == LAW_ORDER, rows)
    for row in rows:
        enacted = row["id"] in in_force
        ctx.check(f"{name} label of {row['id']}", ("[in force] " in row["label"]) == enacted, row["label"])
    ctx.check(f"{name} tree state has the same laws", sorted(tree(ctx)["laws"]) == sorted(in_force), tree(ctx)["laws"])


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    opened = ctx.mod.command(PREFIX + "tech_tree_widget_open")
    ctx.check("W1 the widget opened", opened.get("ok") is True, opened)
    time.sleep(SETTLE_S)
    state = widget(ctx)
    ctx.check("W1 the laws line says to choose a path", state["laws_line"] == "Laws: choose a path first", state["laws_line"])
    ctx.check("W1 no law button shows before the path", all(row["visibility"] != VISIBLE for row in law_rows(ctx)), law_rows(ctx))

    press(ctx, "path", 2)
    ctx.check("W2 the path button chose prosperity", tree(ctx)["path"] == "prosperity", tree(ctx)["path"])
    ctx.actions.set_settlement_level(2)
    ctx.run_until(lambda: tree(ctx)["slots"] >= 2, 15, what="two node slots")
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    time.sleep(SETTLE_S)
    check_matches_state(ctx, "W3", [])
    ctx.screenshot("tech-tree-widget-laws-open")

    press(ctx, "law", 2)
    press(ctx, "law", 1)
    check_matches_state(ctx, "W4", ["trade_pacts", "militia_charter"])
    ctx.check("W4 the closed law shows (closed)", law_rows(ctx)[2]["label"].endswith("(closed)"), law_rows(ctx)[2])
    refused = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind="law", index=3)
    ctx.check("W5 a press on a closed law is refused", refused is not None and "pay_off_warbands" in refused, refused)
    ctx.screenshot("tech-tree-widget-laws-enacted")

    press(ctx, "law", 2)
    check_matches_state(ctx, "W6", ["militia_charter"])
    ctx.metric("laws_in_force_end", len(tree(ctx)["laws"]))
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
