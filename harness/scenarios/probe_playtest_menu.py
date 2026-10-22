"""Spike scenario (change spike-playtest-telemetry, #384, task 1.5): a report menu with a text box and a check box.

The widget is built at run time from C++ UMG classes (no pak widget). The scenario checks that the widget is in the viewport,
sets text and the check box state through Lua, reads them back, and tries to type with WM_CHAR messages posted to the window
(no real mouse, no real keyboard device). Screenshots may show other windows on slot 2: clean pictures need slot 0.
"""
import ctypes
import time

NAME = "probe-playtest-menu"
DESCRIPTION = "Spike: mod widget with MultiLineEditableTextBox, CheckBox and Button; screenshots; typing by WM_CHAR."
COVERS: list[str] = []
LIMIT_S = 180
HIDDEN = True

PREFIX = "PlaytestProbe."
WM_CHAR = 0x0102


def raise_game_window(ctx) -> dict:
    """Put the game window on top without the focus, so other windows are not in the screenshots."""
    window = ctx.game_window()
    ctypes.windll.user32.SetWindowPos(window["hwnd"], -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
    return window


def run(ctx) -> dict:
    cmd = lambda name, **a: ctx.mod.command(PREFIX + name, **a)  # noqa: E731
    window = raise_game_window(ctx)
    opened = cmd("menu_open", checked=1)
    ctx.log.info(f"menu_open {opened}")
    ctx.expect.equals("widget is in the viewport", opened.get("in_viewport"), True)
    time.sleep(1.5)
    state = cmd("menu_state")
    ctx.log.info(f"state after open {state}")
    ctx.expect.equals("check box is ticked by default", state.get("checked"), True)
    ctx.screenshot("menu-open-ticked")
    ctx.log.info(f"set_text {cmd('menu_set_text', text='The raid never arrived after day 40')}")
    time.sleep(0.5)
    state = cmd("menu_state")
    ctx.log.info(f"state after set_text {state}")
    ctx.expect.equals("text box shows the text that Lua set", state.get("text"), "The raid never arrived after day 40")
    ctx.screenshot("menu-text-set")
    focus = cmd("menu_focus")
    ctx.log.info(f"focus {focus}")
    for char in " +typed":
        ctypes.windll.user32.PostMessageW(window["hwnd"], WM_CHAR, ord(char), 0)
        time.sleep(0.05)
    time.sleep(0.5)
    state = cmd("menu_state")
    ctx.log.info(f"state after WM_CHAR {state}")
    ctx.record = ctx.expect.record("WM_CHAR typing reached the text box", "+typed" in (state.get("text") or ""), state.get("text"), "contains +typed")
    ctx.screenshot("menu-typed")
    cmd("menu_set_checked", on=0)
    time.sleep(0.5)
    state = cmd("menu_state")
    ctx.log.info(f"state after untick {state}")
    ctx.expect.equals("check box can be unticked", state.get("checked"), False)
    ctx.screenshot("menu-unticked")
    cmd("menu_close")
    return ctx.result()
