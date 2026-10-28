"""M12 iteration 05 (layout of change update-tech-tree-widget-layout): the law buttons on the cards and the laws strip work. No real mouse.

Needs the pak: `run.py --scenario tech-tree-widget-laws --pak InvasionMod`. The scenario calls the same handler that a click calls
(command tech_tree_widget_press). Real mouse clicks on the law buttons are open (issue #203). It saves nothing.
A law button stands on the card of its tech, so its index is the index of the card (the data order of the nodes).
"""

import time

NAME = "tech-tree-widget-laws"
DESCRIPTION = "Open the tech tree menu, check the law buttons on the cards and the laws strip, enact and repeal laws through the button handlers. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 1.0
VISIBLE = 0
CHARTER, PACTS, WARBANDS, CURFEW = 5, 6, 7, 11  # card indexes of the laws: Militia Charter, Trade Pacts, Pay Off Warbands, Curfew
LAW_BY_CARD = {5: "militia_charter", 6: "trade_pacts", 7: "pay_off_warbands", 11: "curfew"}


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def press(ctx, kind: str, index: int) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_press", kind=kind, index=index)


def shown_laws(ctx) -> dict:
    """card index -> label of the visible law buttons."""
    return {row["index"]: row["label"] for row in widget(ctx)["laws"] if row["visibility"] == VISIBLE}


def check_matches_state(ctx, name: str, in_force: list) -> None:
    state = widget(ctx)
    ctx.check(f"{name} the strip count equals the wanted count", state["strip_count"] == state["wanted_strip_count"], state["strip_count"])
    ctx.check(f"{name} the strip counts the laws in force", state["strip_count"] == f"{len(in_force)} of 2 max", state["strip_count"])
    filled = [row for row in state["strip"] if row["visibility"] == VISIBLE]
    ctx.check(f"{name} one strip place for each law in force", sorted(row["id"] for row in filled) == sorted(in_force), filled)
    for row in state["laws"]:
        if row["visibility"] == VISIBLE:
            enacted = row["id"] in in_force
            ctx.check(f"{name} label of {row['id']}", row["label"] == ("Repeal" if enacted else "Enact"), row["label"])
    ctx.check(f"{name} tree state has the same laws", sorted(tree(ctx)["laws"]) == sorted(in_force), tree(ctx)["laws"])


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    opened = ctx.mod.command(PREFIX + "tech_tree_widget_open")
    ctx.check("W1 the widget opened", opened.get("ok") is True, opened)
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    time.sleep(SETTLE_S)
    ctx.check("W1 no law button shows before a path and a tech", shown_laws(ctx) == {}, shown_laws(ctx))
    ctx.check("W1 the strip is empty", widget(ctx)["strip_count"] == "0 of 2 max", widget(ctx)["strip_count"])

    press(ctx, "path", 2)
    ctx.check("W2 the path button chose prosperity", tree(ctx)["path"] == "prosperity", tree(ctx)["path"])
    ensure_picks(ctx, 3)
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    time.sleep(SETTLE_S)
    check_matches_state(ctx, "W3", [])
    ctx.check("W3 Enact shows on the cards of the two unlocked techs", shown_laws(ctx) == {CHARTER: "Enact", PACTS: "Enact"}, shown_laws(ctx))
    ctx.screenshot("tech-tree-widget-laws-open")

    press(ctx, "law", PACTS)
    press(ctx, "law", CHARTER)
    check_matches_state(ctx, "W4", ["trade_pacts", "militia_charter"])
    ctx.check("W4 Repeal shows on both cards", shown_laws(ctx) == {CHARTER: "Repeal", PACTS: "Repeal"}, shown_laws(ctx))
    refused = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind="law", index=WARBANDS)
    ctx.check("W5 a press on the law of a locked tech is refused", refused is not None and "no law button" in refused, refused)

    ctx.mod.command(PREFIX + "tech_tree_unlock", node="night_watch")  # a common tech opens a common law
    time.sleep(SETTLE_S)
    ctx.check("W6 Enact shows on the common law card", shown_laws(ctx).get(CURFEW) == "Enact", shown_laws(ctx))
    third = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind="law", index=CURFEW)
    ctx.check("W6 a third law is refused", third is not None and "law place" in third, third)
    ctx.check("W6 the footer says 2 of 2 laws are in force", widget(ctx)["footer"] == "Curfew refused: 2 of 2 laws are in force.", widget(ctx)["footer"])
    ctx.screenshot("tech-tree-widget-laws-enacted")

    press(ctx, "strip", 1)
    state = widget(ctx)
    ctx.check("W7 a strip Repeal button repealed a law", len(tree(ctx)["laws"]) == 1 and state["strip_count"] == "1 of 2 max", state["strip"])
    press(ctx, "law", CURFEW)
    check_matches_state(ctx, "W8", sorted(tree(ctx)["laws"]))
    ctx.check("W8 the common law is in force", "curfew" in tree(ctx)["laws"], tree(ctx)["laws"])
    press(ctx, "law", PACTS) if "trade_pacts" in tree(ctx)["laws"] else press(ctx, "law", CHARTER)
    check_matches_state(ctx, "W9", sorted(tree(ctx)["laws"]))
    ctx.metric("laws_in_force_end", len(tree(ctx)["laws"]))
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()


def ensure_picks(ctx, wanted: int) -> None:
    """Wait for the start pick, then add picks (a test command) until `wanted` picks are earned."""
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    missing = wanted - ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
