"""add-game-settings-guard: the guard value `vassals` and the warning "vassals are not enabled" in the mod start menu.

Three uses (it saves nothing):
  1. State of a loaded fixture (old save, live check):
     `run.py --scenario scenario-settings-game-settings-guard --pak InvasionMod --fixture base --env EXPECT_VASSALS=1`
     `run.py --scenario scenario-settings-game-settings-guard --pak InvasionMod --fixture playtest-noai --env EXPECT_VASSALS=0`
  2. New game from the 6th template "The Hussites Are Coming" (AI opponents 0): the warning shows in the mod start menu.
     `run.py --scenario scenario-settings-game-settings-guard --pak InvasionMod --env GUARD_PART=hussite` (real mouse, like
     scenario-settings-hussite-template, which this part runs first with HUSSITE_CONTINUE).
The state of the fixture is read as soon as the settings decision is made.
"""

import os
import sys
import time

from runlib import osinput

NAME = "scenario-settings-game-settings-guard"
DESCRIPTION = "The vassals guard: fixture base has AI lords (no warning); fixture playtest-noai and the Hussite template have none (warning). Needs --pak InvasionMod."
LIMIT_S = 500
EXCLUSIVE = True
LONG_REASON = "the hussite part uses the real mouse and screen"
PREFIX = "InvasionMod."
WARNING = "vassals are not enabled"


def settings(ctx) -> dict:
    return ctx.mod.command(PREFIX + "scenario_settings_state")


def check_state(ctx, expected: int, label: str) -> None:
    state = settings(ctx)
    warning = state.get("warning")
    ctx.metric("vassals", state["vassals"])
    ctx.check(f"{label} vassals is {expected}", state["vassals"] == expected, state["vassals"])
    if expected == 0:
        ctx.check(f"{label} the warning is shown", isinstance(warning, str) and WARNING in warning, warning)
    else:
        ctx.check(f"{label} no warning", warning is None, warning)
    ctx.check(f"{label} no row is locked: a level above 0 is accepted",
              ctx.mod.command(PREFIX + "scenario_settings_set", yearly=3).get("yearly") == 3 if state["open"] is False else True, state)


def hussite_part(ctx) -> None:
    os.environ["HUSSITE_CONTINUE"] = "1"
    module = next(m for n, m in sys.modules.items() if n.endswith("scenario_settings_hussite_template"))
    module.run(ctx)  # the 6th template, Continue, the mod start menu opens (checks T1 to T3)
    state = settings(ctx)
    check_state_before_close = state["vassals"] == 0 and isinstance(state.get("warning"), str)
    ctx.check("G1 the Hussite template gives vassals 0 and the warning", check_state_before_close, state)
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(1.0)
    ctx.screenshot("vassals-warning")


def run(ctx) -> dict:
    if ctx.variant_option("GUARD_PART", "state") == "hussite":
        hussite_part(ctx)
        return ctx.result()
    ctx.run_until(lambda: settings(ctx)["decided"], 90, what="the settings decision")
    check_state(ctx, int(ctx.variant_option("EXPECT_VASSALS", "1")), "G2")
    return ctx.result()
