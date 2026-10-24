"""update-mod-menu-close-and-pause, spike 2b: how to close the game's Esc menu from Lua and get the HUD back. Hidden probe.

For each candidate function: Esc opens the game's menu, the function is called on the widget, the HUD (W_HUD_Timer_C) and the
game speed are read. It saves nothing. Run: `run.py --scenario probe-esc-menu` (fixture load).
"""

import time

from runlib import osinput

NAME = "probe-esc-menu"
HIDDEN = True
LIMIT_S = 250
VK_ESCAPE = 0x1B
CANDIDATES = ("DoCloseAndHideSelf", "continue", "unpauseAndResetDLSS", "OnPauseMenuReopen", "GoToPreviousMenu")


def esc_widget(ctx):
    found = ctx.bridge._result("objects", class_name="mainMenu_widget_C", limit=10)["objects"]
    live = [str(e).split(" ", 1)[1] for e in found if " /Engine/Transient" in str(e)]
    return live[0] if live else None


def hud_present(ctx) -> int:
    found = ctx.bridge._result("objects", class_name="W_HUD_Timer_C", limit=10)["objects"]
    return len([e for e in found if " /Engine/Transient" in str(e)])


def esc(input_) -> None:
    input_.key(VK_ESCAPE, True)
    time.sleep(0.1)
    input_.key(VK_ESCAPE, False)


def run(ctx) -> dict:
    input_ = osinput.Win32Input()
    input_.bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(1.0)
    ctx.log.info(f"start: hud={hud_present(ctx)} speed={ctx.bridge.read_game_speed()}")
    for name in CANDIDATES:
        esc(input_)
        time.sleep(1.5)
        path = esc_widget(ctx)
        vis = ctx.bridge._result("call", ref=path, function="GetVisibility", args=[])
        ctx.log.info(f"[{name}] after Esc: hud={hud_present(ctx)} speed={ctx.bridge.read_game_speed()} vis={vis}")
        try:
            ctx.bridge._result("call", ref=path, function=name, args=[])
        except Exception as problem:  # noqa: BLE001
            ctx.log.info(f"[{name}] call failed: {str(problem)[:120]}")
        time.sleep(1.5)
        vis = ctx.bridge._result("call", ref=path, function="GetVisibility", args=[])
        ctx.log.info(f"[{name}] after the call: hud={hud_present(ctx)} speed={ctx.bridge.read_game_speed()} vis={vis}")
        ctx.screenshot(f"after-{name}")
        if vis != 1:  # still open: a real Esc closes it, for the next candidate
            esc(input_)
            time.sleep(1.5)
            ctx.log.info(f"[{name}] after a real Esc: hud={hud_present(ctx)} speed={ctx.bridge.read_game_speed()}")
    return ctx.result()
