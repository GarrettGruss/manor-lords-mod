"""add-scenario-settings-menu: Great raids Off. The clock does not run, no clock banner shows and the phase stays none.

Runs on a fixture (a loaded save: the menu does not open). It saves nothing.
"""

import re

NAME = "scenario-settings-great-raids-off"
DESCRIPTION = "Great raids Off: no great raid end day, no clock banner, no waves after 3 game days."
LIMIT_S = 240
SPEED = 3
DAYS = 3
PREFIX = "InvasionMod."
CLOCK_LINE = re.compile(r"INVASION clock (start|banner) ")


def clock_lines(ctx) -> int:
    log = ctx.run_dir / "mod.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return len([line for line in text.splitlines() if CLOCK_LINE.search(line)])


def run(ctx) -> dict:
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "scenario_settings_state")["decided"], 60, what="the settings decision")
    state = ctx.mod.command(PREFIX + "scenario_settings_set", great_raids=0)
    ctx.log.info(f"settings {state}")
    ctx.check("G1 the setting reads Off", state["great_raids"] == 0, state["great_raids"])
    ctx.check("G1 the menu is not open on a loaded save", state["open"] is False, state["open"])
    before = clock_lines(ctx)
    ctx.time.run_game_days(DAYS, speed=SPEED)
    clock = ctx.mod.command(PREFIX + "invasion_clock_state")
    great = ctx.mod.command(PREFIX + "invasion_great_state")
    ctx.check("G2 no great raid end day exists", clock["great_raid_day"] == 0, clock)
    ctx.check("G2 the phase stays none", great["phase"] == 0 and great["wave"] == 0, great)
    ctx.check("G3 no clock start or clock banner after the switch", clock_lines(ctx) == before, [before, clock_lines(ctx)])
    lines = ctx.mod.command(PREFIX + "raid_widget_state")["wanted_lines"]
    ctx.check("G4 the raid widget says the great raid is off", lines[2] == "Great raid: off", lines)
    return ctx.result()
