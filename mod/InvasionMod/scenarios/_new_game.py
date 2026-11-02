"""Shared helper for test scenarios that run with --new-game.

A new game opens the scenario settings start screen after the intro. The screen has no Close button and Esc does nothing
(change update-scenario-settings-window-style, #545). The game stays paused until "Begin the game". So a new-game test
scenario presses Begin first, with the named command `scenario_settings_click` (the same code as the Begin click button).
"""

PREFIX = "InvasionMod."
OPEN_WAIT_S = 150  # the menu opens after the intro (config intro_wait_s is 60)


def begin_game(ctx) -> dict:
    """Wait for the start screen of a new game, press Begin and wait until it is closed. Does nothing on a loaded save."""
    def state():
        return ctx.mod.command(PREFIX + "scenario_settings_state")

    ctx.run_until(lambda: state()["open"] or state()["settings_applied"], OPEN_WAIT_S, what="the start screen opens", poll_s=1.0)
    if state()["open"]:
        ctx.mod.command(PREFIX + "scenario_settings_click", action="begin")
        ctx.run_until(lambda: not state()["open"], 20, what="Begin closes the start screen", poll_s=0.5)
    return state()
