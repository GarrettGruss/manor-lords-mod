"""fix-liege-contracts-first-spring: a new game (day 61, spring) is dealt nine contracts with no test command.

Run: `run.py --scenario liege-contracts-new-game-offer --new-game --pak InvasionMod --slot 1`. It saves nothing and never calls
`liege_contracts_offer_now`. It opens the window and takes one picture (nine cards, one Close button).
"""

import time

NAME = "liege-contracts-new-game-offer"
DESCRIPTION = "New game in spring: the liege offer has 9 contracts without the test command; the window shows nine cards and one Close. Needs --new-game --pak InvasionMod."
LIMIT_S = 240
PREFIX = "InvasionMod."
SETTLE_S = 2.5


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "scenario_settings_skip")  # the settings menu of a new game holds the season step until Begin
    ctx.run_until(lambda: len(ctx.mod.command(PREFIX + "liege_contracts_state")["offer"]) == 9, 60,
                  what="the first spring deals nine contracts", poll_s=1.0)
    state = ctx.mod.command(PREFIX + "liege_contracts_state")
    expect.equals("N1 the offer has 9 contracts", len(state["offer"]), 9)
    expect.equals("N2 the spring counter names the offer", state["spring_no"], state["season_no"])
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("N3 the window opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    view = ctx.mod.command(PREFIX + "liege_menu_state")
    expect.equals("N4 nine cards show a requirement", sum(1 for k, v in view["texts"].items() if k.startswith("ReqText") and v), 9)
    expect.equals("N5 the framework Close button is the only Close", ctx.mod.command(PREFIX + "menu_state").get("close_button"), True)
    expect.equals("N5b the widget has no Close button of its own", [b["name"] for b in view["buttons"] if "Close" in b["name"]], [])
    ctx.screenshot("window-new-game-nine-cards")
    ctx.mod.command(PREFIX + "liege_menu_close")
    return ctx.result()
