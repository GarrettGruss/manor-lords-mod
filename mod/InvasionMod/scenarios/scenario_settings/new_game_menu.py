"""add-scenario-settings-menu: a new game opens the scenario settings menu. The game stays paused until "Begin the game".

Needs a new game and the pak: `run.py --scenario scenario-settings-new-game-menu --new-game --pak InvasionMod --slot N`. The menu opens
by itself after the intro. The scenario chooses with the named command `scenario_settings_click` (the same code as a click button).
It saves nothing and does not open the game's Game Setup screen. Pictures (`ctx.screenshot`): the menu at the defaults, after the
changes and after Begin.
"""

import time

from runlib import osinput

NAME = "scenario-settings-new-game-menu"
DESCRIPTION = "New game: the menu opens and pauses the game, the choices apply on Begin, the game runs and the autosave stays far away. Needs --new-game --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
DEFAULTS = {"yearly": 2, "great": 2, "vassal": 2, "first_raid_years": 2, "size_class": 2}
CHANGED = {"yearly": 3, "great": 0, "vassal": 1, "first_raid_years": 3, "size_class": 3}
MIN_REMAINING_S = 1_000_000
SETTLE_S = 1.5


def front(ctx) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)


def settings(ctx) -> dict:
    return ctx.mod.command(PREFIX + "scenario_settings_state")


def menu_is_open(ctx) -> bool:
    """The player pawn is not live right after READY; the state command then fails. Treat that as not open yet."""
    try:
        return bool(settings(ctx)["open"])
    except Exception as error:
        if "no live player pawn" in str(error):
            return False
        raise


def click(ctx, **args) -> dict:
    return ctx.mod.command(PREFIX + "scenario_settings_click", **args)


def run(ctx) -> dict:
    ctx.run_until(lambda: menu_is_open(ctx), 150, what="the settings menu opens", poll_s=1.0)
    time.sleep(SETTLE_S)  # the widget needs a frame before it is painted
    first = settings(ctx)
    ctx.log.info(f"menu open: {first}")
    ctx.metric("new_game_day", first["day"] if first["day"] is not None else -1)
    ctx.metric("save_file_length", len(first["save_file"] or ""))
    ctx.check("N1 the game is told as new (empty save file name)", first["save_file"] == "", first["save_file"])
    ctx.check("N1 the menu opened and the game was paused by it", first["open"] is True and first["paused"] is True, first)
    ctx.check("N1 the intro is over", first["intro_playing"] is False, first["intro_playing"])
    ctx.check("N1 the choices are the defaults (three levels at 2, no Difficulty setting)", first["selection"] == DEFAULTS, first["selection"])
    ctx.check("N1 the settings are not applied before Begin", first["settings_applied"] is False, first["settings_applied"])
    clock = ctx.read_clock()
    ctx.check("N2 the game clock stands still while the menu is open", clock["paused"], clock["change"], [0, 0.001])
    ctx.log.info(f"gameSpeed while the menu is open: {ctx.bridge.read_game_speed()}")
    front(ctx)
    ctx.screenshot("menu-defaults")

    for key, value in CHANGED.items():
        click(ctx, action="choose", key=key, value=value)
    changed = settings(ctx)
    ctx.check("N3 the choices changed", {k: changed["selection"][k] for k in CHANGED} == CHANGED, changed["selection"])
    ctx.check("N3 the menu is still open and nothing is applied yet", changed["open"] is True and changed["settings_applied"] is False, changed)
    time.sleep(SETTLE_S)
    front(ctx)
    ctx.screenshot("menu-changed")
    click(ctx, action="defaults")
    reset = settings(ctx)
    ctx.check("N3 Use defaults resets all five", {k: reset["selection"][k] for k in DEFAULTS} == DEFAULTS, reset["selection"])
    for key, value in CHANGED.items():
        click(ctx, action="choose", key=key, value=value)

    click(ctx, action="begin")
    ctx.run_until(lambda: not settings(ctx)["open"], 20, what="Begin closes the menu", poll_s=0.5)
    after = settings(ctx)
    ctx.check("N4 the menu is closed and the settings are applied", after["open"] is False and after["settings_applied"] is True, after)
    ctx.check("N4 the settings are the chosen ones", {k: after[k] for k in CHANGED} == CHANGED, after)
    ctx.check("N4 the levels count as chosen (no pick banner)", after["difficulty_chosen"] is True, after["difficulty_chosen"])
    ctx.check("N4 the game is not paused by the menu any more", after["paused"] is False, after["paused"])
    speed = ctx.bridge.read_game_speed()
    running = ctx.read_clock(3.0)
    ctx.log.info(f"after Begin: gameSpeed={speed} clock={running}")
    ctx.metric("game_speed_after_begin", speed if speed is not None else -1)
    ctx.check("N5 the game runs after Begin (the mod un-paused it, no harness call)", running["paused"] is False, running["change"], [0.001, 100])
    ctx.check("N5 the game speed is 1 after Begin", speed == 1, speed)
    time.sleep(SETTLE_S)
    front(ctx)
    ctx.screenshot("after-begin")

    autosave = ctx.actions.autosave_status()
    ctx.check("N6 the autosave timer is far away after Begin", autosave.get("remaining_s", 0) >= MIN_REMAINING_S, autosave.get("remaining_s"))
    difficulty = ctx.mod.command(PREFIX + "invasion_difficulty_state")
    ctx.check("N7 the levels are yearly 3, great 0, vassal 1 and chosen",
              (difficulty["yearly"], difficulty["great"], difficulty["vassal"]) == (3, 0, 1) and difficulty["chosen"] is True, difficulty)
    ctx.mod.command(PREFIX + "invasion_set_difficulty", value=1)
    after_set = ctx.mod.command(PREFIX + "invasion_difficulty_state")
    ctx.check("N7 invasion_set_difficulty sets all three levels afterwards", (after_set["yearly"], after_set["great"], after_set["vassal"]) == (1, 1, 1), after_set)
    ctx.pause()
    return ctx.result()
