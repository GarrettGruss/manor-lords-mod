"""fix-settings-menu-pause (#418): the settings menu keeps the game paused in a player launch (no HarnessBoot pause).

Needs: `run.py --scenario scenario-settings-player-launch-pause --new-game --pak InvasionMod --env HARNESS_BOOT_NO_PAUSE=1 --slot N`.
HARNESS_BOOT_NO_PAUSE=1 makes HarnessBoot skip its pauseGame step, so the intro cinematic ends on a running game as it does for a
player. The scenario samples the clock, the game speed and the menu state until the menu is open, then watches that the clock stays
still for HOLD_S seconds, then clicks Begin. It saves nothing.
"""

import time

from runlib import osinput

NAME = "scenario-settings-player-launch-pause"
DESCRIPTION = "Player launch (HarnessBoot pause off): the menu keeps the clock still through and after the intro. Needs --new-game --pak InvasionMod --env HARNESS_BOOT_NO_PAUSE=1."
LIMIT_S = 300
PREFIX = "InvasionMod."
HOLD_S = 10
SAMPLE_S = 1.0
SPACE_KEY, KEY_2 = 0x20, 0x32
RECOVER_S = 2.0  # the mod may need a poll to pause again


def sample(ctx, label: str) -> dict:
    state = ctx.mod.command(PREFIX + "scenario_settings_state")
    clock = ctx.bridge.read_clock_value()
    speed = ctx.bridge.read_game_speed()
    ctx.log.info(f"[{label}] clock={clock:.3f} speed={speed} open={state['open']} paused_by_menu={state['paused']} intro={state['intro_playing']} kind={state['kind']}")
    return {"clock": clock, "speed": speed, **state}


def run(ctx) -> dict:
    ctx.log.info("sampling from READY (no HarnessBoot pause)")
    last = {}
    deadline = time.time() + 150
    while time.time() < deadline:
        last = sample(ctx, "before-menu")
        if last["open"]:
            break
        time.sleep(SAMPLE_S)
    ctx.check("P1 the menu opened", last.get("open") is True, last)
    ctx.metric("clock_at_open", last["clock"])
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(1.5)
    ctx.screenshot("menu-open")
    start = sample(ctx, "hold-start")
    moved_at = None
    for second in range(int(HOLD_S / SAMPLE_S)):
        time.sleep(SAMPLE_S)
        now = sample(ctx, "hold")
        if abs(now["clock"] - start["clock"]) >= 0.01 and moved_at is None:
            moved_at = second
    end = sample(ctx, "hold-end")
    change = round(end["clock"] - start["clock"], 3)
    ctx.metric("clock_change_while_menu_open", change)
    ctx.check("P2 the game clock does not move while the menu is open", abs(change) < 0.01, change, [0, 0.01])
    ctx.check("P2 the menu is still open", end["open"] is True, end)
    ctx.screenshot("menu-open-later")

    # The player un-pauses with the Space key or a speed key while the menu is open (the menu does not take the keyboard).
    input_ = osinput.Win32Input()
    input_.bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.3)
    for key in (SPACE_KEY, KEY_2):
        input_.key(key, True)
        time.sleep(0.1)
        input_.key(key, False)
        time.sleep(0.4)
    time.sleep(RECOVER_S)
    after_key = ctx.read_clock(3.0)
    ctx.log.info(f"after the player keys: {after_key} state={sample(ctx, 'after-keys')}")
    ctx.metric("clock_change_after_player_keys", after_key["change"])
    ctx.check("P4 the clock is still after the player pressed Space and 2", after_key["paused"], after_key["change"], [0, 0.001])
    ctx.mod.command(PREFIX + "scenario_settings_click", action="begin")
    ctx.run_until(lambda: not ctx.mod.command(PREFIX + "scenario_settings_state")["open"], 20, what="Begin closes the menu", poll_s=0.5)
    running = ctx.read_clock(3.0)
    ctx.check("P3 the game runs after Begin", running["paused"] is False, running["change"], [0.001, 100])
    ctx.pause()
    return ctx.result()
