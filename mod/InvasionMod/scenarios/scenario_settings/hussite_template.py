"""add-hussite-scenario-template: the game's New Game screen shows a 6th template "The Hussites Are Coming".

Needs the pak: `run.py --scenario scenario-settings-hussite-template --pak InvasionMod --slot 0` (fixture `base`; the real mouse
is used, so no other program may use the screen). The scenario opens the game's main menu and the Game Setup screen with the
console command `open` and the menu function `GoToGameSetup` (as the spike #416 did), clicks the 6th template with the real
mouse, reads the game setup, and takes pictures. It saves nothing. `HUSSITE_CONTINUE` clicks "Continue" and checks that a new
game starts and that the mod start menu opens.
"""

import ctypes
import os
import time

from runlib import osinput

NAME = "scenario-settings-hussite-template"
DESCRIPTION = "Game Setup screen: six templates, a real click on the sixth sets the Hussite game settings. Needs --pak InvasionMod."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "real mouse and screen"
PREFIX = "InvasionMod."
# Fractions of the game window (read from the first pictures).
SIXTH_TEMPLATE = (float(os.environ.get("HT_FX", "0.442")), float(os.environ.get("HT_FY", "0.242")))
CONTINUE_BUTTON = (float(os.environ.get("HT_CX", "0.83")), float(os.environ.get("HT_CY", "0.95")))
EXPECTED = {
    "ai_lords": 0, "adversary_baron": False, "raiding_frequency": 0, "max_bandit_camps": 0, "initial_bandit_camps": 0,
    "starting_day": 61, "starting_supplies": 1, "royal_tax": 0, "armament_delivery": False, "requirement_bias": 0,
    "spoilage": 2, "approval_loss": 0.5, "water_veins": True, "weather": 2,
}
SETTLE_S = 2.0
SETTINGS_LIST = (0.28, 0.75)  # a point inside the settings list of the Game Setup screen


def live_objects(ctx, class_name: str) -> list:
    found = ctx.bridge._result("objects", class_name=class_name, limit=20)["objects"]
    return [str(entry).split(" ", 1)[1] for entry in found if " /Engine/Transient" in str(entry)]


def wait_for(predicate, timeout_s: float, what: str, poll_s: float = 1.0) -> None:
    """Poll without the game clock: the menu map has no game engine object, so ctx.run_until cannot read the clock."""
    end = time.time() + timeout_s
    while time.time() < end:
        if predicate():
            return
        time.sleep(poll_s)
    raise TimeoutError(f"timeout after {timeout_s:.0f} s: {what}")


def with_focus(ctx, action, attempts: int = 6):
    """Run a real-mouse action. Another game that starts on this computer can take the focus, so the action is tried again."""
    for attempt in range(1, attempts + 1):
        front(ctx)
        try:
            return action()
        except osinput.InputError as error:
            ctx.log.info(f"focus lost (attempt {attempt}): {error}")
            time.sleep(3.0)
    raise osinput.InputError(f"the game window did not keep the focus in {attempts} attempts")


def scroll_down(ctx, clicks: int) -> None:
    """Wheel clicks over the settings list (the cursor is moved there first)."""
    with_focus(ctx, lambda: ctx.hover_with_mouse(*SETTINGS_LIST))
    time.sleep(0.4)
    for _ in range(clicks):
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, -120, 0)  # MOUSEEVENTF_WHEEL, one click down
        time.sleep(0.15)
    time.sleep(0.8)


def front(ctx) -> None:
    osinput.Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.4)


def open_setup_screen(ctx) -> None:
    ctx.bridge._result("console", command="open /Game/NotStronghold/Maps/MainMenu")
    wait_for(lambda: bool(live_objects(ctx, "mainMenu_widget_C")), 90, "the main menu opens")
    time.sleep(SETTLE_S)
    ctx.bridge.call_function(live_objects(ctx, "mainMenu_widget_C")[0], "GoToGameSetup")
    wait_for(lambda: bool(live_objects(ctx, "mainMenu_GameSetup_C")), 30, "the Game Setup screen opens")
    time.sleep(SETTLE_S)


def run(ctx) -> dict:
    open_setup_screen(ctx)
    buttons = live_objects(ctx, "mainMenu_GameSetupPresetButton_C")
    time.sleep(3.0)  # the thumbnails load a moment after the screen opens
    ctx.metric("template_buttons", len(buttons))
    ctx.check("T1 the template row shows six templates", len(buttons) == 6, len(buttons))
    front(ctx)
    ctx.screenshot("setup-before-click")

    with_focus(ctx, lambda: ctx.click_with_mouse(*SIXTH_TEMPLATE))
    time.sleep(SETTLE_S)
    setup = ctx.actions.game_setup_state()
    ctx.log.info(f"setup after the click: {setup}")
    for field, expected in EXPECTED.items():
        ctx.check(f"T2 {field} is {expected}", setup.get(field) == expected, setup.get(field))
    front(ctx)
    ctx.screenshot("sixth-selected")
    with_focus(ctx, lambda: ctx.hover_with_mouse(*SIXTH_TEMPLATE))  # the tooltip shows the title and the text of the template
    time.sleep(1.5)
    front(ctx)
    ctx.screenshot("sixth-hover-tooltip")
    scroll_down(ctx, 6)
    with_focus(ctx, lambda: ctx.hover_with_mouse(0.5, 0.075))  # off the rows, so no tooltip covers the values
    time.sleep(1.0)
    front(ctx)
    ctx.screenshot("sixth-selected-settings")

    if os.environ.get("HUSSITE_CONTINUE"):
        with_focus(ctx, lambda: ctx.click_with_mouse(*CONTINUE_BUTTON))
        PREFIXED = PREFIX + "scenario_settings_state"
        wait_for(lambda: ctx.mod.command(PREFIXED).get("open"), 240, "the mod start menu opens", poll_s=2.0)
        state = ctx.mod.command(PREFIXED)
        ctx.check("T3 the mod start menu opened after the new game", state["open"] is True, state)
        ctx.check("T3 the marker says the Hussite template was chosen", state["hussite_template"] is True, state["hussite_template"])
        front(ctx)
        ctx.screenshot("mod-start-menu")
    return ctx.result()
