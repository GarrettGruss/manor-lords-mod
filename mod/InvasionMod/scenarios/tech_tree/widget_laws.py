"""M12 iteration 05 (change add-laws-menu, #563): the tech window has no law buttons and no laws strip. It names the Laws menu. No real mouse.

Needs the pak: `run.py --scenario tech-tree-widget-laws --pak InvasionMod --slot 2`. Enact and revoke moved to the Laws menu (scenarios laws_menu/*).
The tech window still shows the law name on the card of the tech that opens it. It saves nothing.
"""

import time

NAME = "tech-tree-widget-laws"
DESCRIPTION = "Open the tech tree menu with laws unlocked: no law button, no strip button, the line Laws: open the Laws menu, the law names on the cards. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 1.0
VISIBLE = 0
LAW_LINE = "Laws: open the Laws menu"


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def press(ctx, kind: str, index: int) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_press", kind=kind, index=index)


def check_no_law_buttons(ctx, name: str) -> None:
    state = widget(ctx)
    ctx.check(f"{name} no law button shows", all(row["visibility"] != VISIBLE for row in state["laws"]), [row for row in state["laws"] if row["visibility"] == VISIBLE])
    ctx.check(f"{name} no strip button shows", all(row["visibility"] != VISIBLE for row in state["strip"]), [row for row in state["strip"] if row["visibility"] == VISIBLE])
    ctx.check(f"{name} the band shows the line that names the Laws menu", (state["laws_line"], state["strip_title"], state["strip_count"]) == (LAW_LINE, "", ""), state["laws_line"])


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    opened = ctx.mod.command(PREFIX + "tech_tree_widget_open")
    ctx.check("W1 the widget opened", opened.get("ok") is True, opened)
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    time.sleep(SETTLE_S)
    check_no_law_buttons(ctx, "W1")

    press(ctx, "path", 2)
    ctx.check("W2 the path button chose prosperity", tree(ctx)["path"] == "prosperity", tree(ctx)["path"])
    missing = 3 - tree(ctx)["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    ctx.mod.command(PREFIX + "tech_tree_enact_law", law="trade_pacts")
    time.sleep(SETTLE_S)
    check_no_law_buttons(ctx, "W3")
    cards = {row["id"]: row for row in widget(ctx)["nodes"] if row["visibility"] == VISIBLE}
    ctx.check("W3 the card of Amnesty shows the law name", cards["amnesty"]["card_law"] == "Trade Pacts", cards["amnesty"])
    ctx.screenshot("tech-tree-widget-laws-line")

    for kind in ("law", "strip"):
        refused = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind=kind, index=1)
        ctx.check(f"W4 a press on a {kind} button is refused", refused is not None and "Laws menu" in refused, refused)
    ctx.check("W4 the law stays in force", tree(ctx)["laws"] == ["trade_pacts"], tree(ctx)["laws"])
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
