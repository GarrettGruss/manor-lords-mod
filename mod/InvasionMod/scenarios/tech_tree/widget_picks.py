"""Change update-tech-tree-widget-layout: common techs, free picks and the footer message of the tech tree window. No real mouse.

Needs the pak: `run.py --scenario tech-tree-widget-picks --pak InvasionMod`. The scenario calls the same handler that a click calls
(command tech_tree_widget_press). It saves nothing.
Card indexes (data order): 1 to 4 Oppression, 5 to 8 Prosperity, 9 Corpse Robbing, 10 Armory Census, 11 Night Watch.
"""

import time

NAME = "tech-tree-widget-picks"
DESCRIPTION = "Open the tech tree window: a common tech without a path, a click without a free pick, the picks counter and the footer. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 1.0
MARTIAL_LAW, CORPSE_ROBBING, ARMORY_CENSUS = 1, 9, 10


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def press(ctx, kind: str, index: int) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_press", kind=kind, index=index)


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.check("P0 the widget opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok") is True)
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    time.sleep(SETTLE_S)
    start = tree(ctx)
    state = widget(ctx)
    wanted = f"Tech picks: {start['free_picks']} free ({start['picks_earned'] - start['free_picks']} of {start['picks_earned']} used)"
    ctx.check("P1 the counter shows the free picks", state["picks"] == wanted, [state["picks"], wanted])

    refused = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind="node", index=MARTIAL_LAW)
    ctx.check("P2 a path tech with no path is refused", refused is not None and "no path is chosen" in refused, refused)
    ctx.check("P2 the footer names the tech and the reason", widget(ctx)["footer"] == "Martial Law refused: no path is chosen.", widget(ctx)["footer"])

    press(ctx, "node", CORPSE_ROBBING)
    ctx.check("P3 a common tech unlocks without a path", tree(ctx)["unlocked"] == ["corpse_robbing"] and tree(ctx)["path"] == "none", tree(ctx))
    state = widget(ctx)
    card = next(row for row in state["nodes"] if row["index"] == CORPSE_ROBBING)
    ctx.check("P3 its card says Unlocked", card["label"].startswith("[x] Corpse Robbing\nUnlocked"), card["label"])
    ctx.check("P3 the counter reads 0 free", state["picks"] == "Tech picks: 0 free (1 of 1 used)", state["picks"])
    ctx.check("P3 the footer says the pick was used", state["footer"] == "Corpse Robbing unlocked. 1 pick used.", state["footer"])

    refused = ctx.mod.refusal(PREFIX + "tech_tree_widget_press", kind="node", index=ARMORY_CENSUS)
    ctx.check("P4 a click without a free pick is refused", refused is not None and "no free pick" in refused, refused)
    ctx.check("P4 the footer says no free pick", widget(ctx)["footer"] == "Armory Census refused: no free pick.", widget(ctx)["footer"])
    card = next(row for row in widget(ctx)["nodes"] if row["index"] == ARMORY_CENSUS)
    ctx.check("P4 the card says No free pick", card["label"].split("\n")[1] == "No free pick", card["label"])

    ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=1)  # a new spring gives one pick
    time.sleep(SETTLE_S)
    ctx.check("P5 a new pick raises the counter on the next refresh", widget(ctx)["picks"] == "Tech picks: 1 free (1 of 2 used)", widget(ctx)["picks"])
    press(ctx, "node", ARMORY_CENSUS)
    ctx.check("P6 the second common tech unlocked", tree(ctx)["unlocked"] == ["corpse_robbing", "armory_census"], tree(ctx)["unlocked"])
    ctx.check("P6 the path is still none", tree(ctx)["path"] == "none", tree(ctx)["path"])
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
