"""Change update-tech-tree-widget-layout: the tech tree window follows the layout of the mockup. Pictures for the owner.

Needs the pak: `run.py --scenario tech-tree-widget-layout --pak InvasionMod --slot 2`. No real mouse. It saves nothing.
The pictures are the evidence (the owner compares them with openspec/specs/mod/tech_tree_widget/mockups/tech-tree-layout.html).
The checks cover the parts that text can prove: the header, column heads, row labels, card order and the footer.
"""

import time

from runlib import windows
from runlib.game import find_game_processes

NAME = "tech-tree-widget-layout"
DESCRIPTION = "Open the tech tree window in three states (no path, a path with two techs, two laws in force), check the parts and take pictures. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 1.5
VISIBLE = 0
FIXED_TEXT = "One tech pick each spring. The path you swear to is final."
CARD_ORDER = ["martial_law", "iron_hand", "veteran_levies", "fear_of_the_lord", "fair_courts", "amnesty", "militia_rights", "golden_age",
              "corpse_robbing", "armory_census", "night_watch"]
ROW_Y = {"oppression": 0, "prosperity": 1, "common": 2}


def picture(ctx, name: str) -> None:
    """A screenshot copies screen pixels. The harness minimizes the debug windows of this game. Another slot may run at the same time:
    its UE4SS debug windows can lie over this game, so they are minimized here too (no input is sent, no focus is taken)."""
    try:
        mine = ctx.game_window()["rect"]
        everyone = {process.pid for process in find_game_processes()}
        for overlay in windows.overlay_windows(windows.list_windows(), everyone):
            left, top, right, bottom = overlay["rect"]
            if left < mine[2] and right > mine[0] and top < mine[3] and bottom > mine[1]:
                windows.minimize_window(overlay["hwnd"])
        time.sleep(0.5)
    except Exception as problem:  # noqa: BLE001 - a picture problem must not fail the checks
        ctx.log.info(f"overlay windows not minimized: {problem}")
    ctx.screenshot(name)


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def tree(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def visible_cards(state: dict) -> list:
    return sorted((row for row in state["nodes"] if row["visibility"] == VISIBLE), key=lambda row: row["index"])


def check_parts(ctx, name: str) -> None:
    """The header, the column heads, the rows, the cards in order, the footer text."""
    state = widget(ctx)
    ctx.check(f"{name} the widget is in the viewport", state["in_viewport"] is True, state)
    ctx.check(f"{name} the title is at the top", state["title"] == "Charters of the Realm", state["title"])
    ctx.check(f"{name} the picks counter follows the picks", state["picks"] == state["wanted_picks"], [state["picks"], state["wanted_picks"]])
    ctx.check(f"{name} the column heads are by order", state["columns"] == ["I  First tech", "II  Second tech", "III  Third tech", "IV  Fourth tech"], state["columns"])
    ctx.check(f"{name} the row labels", [row["name"] for row in state["rows"]] == ["Oppression", "Prosperity", "Common"], state["rows"])
    cards = visible_cards(state)
    ctx.check(f"{name} eleven cards in the data order", [row["id"] for row in cards] == CARD_ORDER, [row["id"] for row in cards])
    wrong = []
    for row in cards:
        want_y = 100 + 160 * (ROW_Y["common"] if row["id"] in CARD_ORDER[8:] else ROW_Y["oppression" if row["id"] in CARD_ORDER[:4] else "prosperity"])
        if row.get("y") != want_y:
            wrong.append((row["id"], row.get("y"), want_y))
    ctx.check(f"{name} the cards stand in the rows (Oppression above Prosperity above Common)", not wrong, wrong)
    columns = [row["x"] for row in cards]
    ctx.check(f"{name} the cards stand in the order columns", columns == [160, 408, 656, 904] * 2 + [160, 408, 656], columns)
    ctx.check(f"{name} the fixed footer text", state["footer_fixed"] == FIXED_TEXT, state["footer_fixed"])
    ctx.check(f"{name} the strip count follows the laws", state["strip_count"] == state["wanted_strip_count"], state["strip_count"])


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    opened = ctx.mod.command(PREFIX + "tech_tree_widget_open")
    ctx.check("L1 the widget opened", opened.get("ok") is True, opened)
    ctx.run_until(lambda: tree(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    time.sleep(SETTLE_S)
    check_parts(ctx, "L1")
    state = widget(ctx)
    ctx.check("L1 two path buttons show before the choice", sum(1 for row in state["paths"] if row["visibility"] == VISIBLE) == 2, state["paths"])
    ctx.check("L1 the path buttons say Swear to this path", all(row["label"] == "Swear to this path" for row in state["paths"]), state["paths"])
    ctx.check("L1 the footer waits for the first click", state["footer"] == "Pick a tech, or swear to a path.", state["footer"])
    picture(ctx, "layout-1-no-path")

    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="path", index=2)
    ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=1)
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    time.sleep(SETTLE_S)
    check_parts(ctx, "L2")
    state = widget(ctx)
    ctx.check("L2 the path buttons are hidden", all(row["visibility"] != VISIBLE for row in state["paths"]), state["paths"])
    ctx.check("L2 the rows say Sworn path and Closed", [row["status"] for row in state["rows"]][:2] == ["Closed", "Sworn path"], state["rows"])
    laws = {row["id"]: row for row in state["laws"] if row["visibility"] == VISIBLE}
    ctx.check("L2 the laws of the two unlocked techs show Enact", sorted(laws) == ["militia_charter", "trade_pacts"], laws)
    picture(ctx, "layout-2-path-two-techs")

    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="law", index=5)
    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="law", index=6)
    time.sleep(SETTLE_S)
    check_parts(ctx, "L3")
    state = widget(ctx)
    filled = [row for row in state["strip"] if row["visibility"] == VISIBLE]
    ctx.check("L3 two filled places in the laws strip", len(filled) == 2 and state["strip_count"] == "2 of 2 max", state["strip"])
    ctx.check("L3 the footer names the last law", state["footer"] == "Trade Pacts enacted.", state["footer"])
    picture(ctx, "layout-3-two-laws")
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
