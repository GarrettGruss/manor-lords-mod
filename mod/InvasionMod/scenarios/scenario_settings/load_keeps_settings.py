"""add-scenario-settings-menu: a save keeps the settings, and the menu stays closed after the load.

Two parts in two runs (the harness action `save_game` is the only save call; spec 24):
  1. `run.py --scenario scenario-settings-load-keeps-settings --new-game --pak InvasionMod --env SETTINGS_PART=save`:
     begin a new game with the levels yearly 3 (hard), great 0 (off) and vassal 1 (easy), 3 years and Large, then save with the guarded `save_game` (keep=True).
  2. `run.py --scenario scenario-settings-load-keeps-settings --save <the saved slot> --pak InvasionMod`:
     after the load the menu is closed and the five values are the same.
NOT RUN YET: the first real `save_game` needs a fresh save backup and the owner told first (CLAUDE.md, Safety).
"""

NAME = "scenario-settings-load-keeps-settings"
DESCRIPTION = "Part save: begin with non-default settings and save (guarded). Part load: the values are the same and the menu stays closed."
LIMIT_S = 300
PREFIX = "InvasionMod."
CHANGED = {"yearly": 3, "great": 0, "vassal": 1, "first_raid_years": 3, "size_class": 3}


def settings(ctx) -> dict:
    return ctx.mod.command(PREFIX + "scenario_settings_state")


def save_part(ctx) -> None:
    ctx.run_until(lambda: settings(ctx)["open"], 150, what="the settings menu opens", poll_s=1.0)
    for key, value in CHANGED.items():
        ctx.mod.command(PREFIX + "scenario_settings_click", action="choose", key=key, value=value)
    ctx.mod.command(PREFIX + "scenario_settings_click", action="begin")
    ctx.run_until(lambda: not settings(ctx)["open"], 20, what="Begin closes the menu", poll_s=0.5)
    ctx.check("L1 the values are set", {k: settings(ctx)[k] for k in CHANGED} == CHANGED, settings(ctx))
    record = ctx.actions.save_game("settings kept", keep=True)
    ctx.log.info(f"saved {record}")
    ctx.check("L1 the guarded save worked", bool(record), record)


def load_part(ctx) -> None:
    ctx.run_until(lambda: settings(ctx)["decided"], 60, what="the settings decision")
    state = settings(ctx)
    ctx.check("L2 the menu did not open and the game is not paused by the mod", state["open"] is False and state["paused"] is False, state)
    ctx.check("L2 the five values are the saved ones", {k: state[k] for k in CHANGED} == CHANGED, state)
    ctx.check("L2 the settings count as applied", state["settings_applied"] is True, state["settings_applied"])


def run(ctx) -> dict:
    part = ctx.variant_option("SETTINGS_PART", "load")
    (save_part if part == "save" else load_part)(ctx)
    return ctx.result()
