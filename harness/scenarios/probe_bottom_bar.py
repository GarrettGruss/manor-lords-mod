"""Spike scenario (change add-mod-menu-access-rule, task 1.3, #308): find the bottom bar HUD widget and add a button to it.

Options: WIDGET (name part of the HUD widget), PANEL (name part of the panel), TEMPLATE (name part of a game button),
STAGE (scan, tree, add, click, overlay). Each step answer is logged. A failed step is a result, not a harness error.
"""
import time

NAME = "probe-bottom-bar"
DESCRIPTION = "Spike: find the bottom bar widget, add a button after the game's buttons, click it, test click blocking."
COVERS: list[str] = []
LIMIT_S = 300
HIDDEN = True
EXCLUSIVE = True
LONG_REASON = "Real mouse clicks in the click and overlay stages."


def send(ctx, **fields) -> dict:
    try:
        answer = ctx.commands.send("ui_probe", **fields)
    except Exception as error:  # a refused step is data for the spike
        ctx.log.info(f"ui_probe {fields.get('action')} refused: {error}")
        return {"ok": False, "error": str(error)}
    ctx.log.info(f"ui_probe {fields.get('action')}: {answer}")
    return answer


def raise_game_window(ctx) -> None:
    """Put the game window on top without the focus, so other windows are not in the screenshots."""
    import ctypes
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window
    try:
        window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
        ctypes.windll.user32.SetWindowPos(window["hwnd"], -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)  # TOPMOST, no move, size, activate
    except Exception as error:  # noqa: BLE001 - a spike helper
        ctx.log.info(f"raise_game_window failed: {error}")


def run(ctx) -> dict:
    raise_game_window(ctx)
    stage = ctx.variant_option("STAGE", "scan")
    widget = ctx.variant_option("WIDGET", "")
    panel = ctx.variant_option("PANEL", "")
    template = ctx.variant_option("TEMPLATE", "")
    time.sleep(2.0)
    ctx.screenshot("hud-before")
    scanned = send(ctx, action="scan") if stage == "scan" else {"ok": True}
    ctx.expect.record("widget scan answered", bool(scanned.get("ok")), scanned.get("error", scanned.get("count")), "ok")
    if stage == "scan":
        return ctx.result()
    for part in widget.split(","):
        send(ctx, action="tree", name=part, limit=int(ctx.variant_option("LIMIT", "500")))
    if stage == "tree":
        return ctx.result()
    first = widget.split(",")[0]
    if stage == "clone":
        return run_clone(ctx, first, panel)
    added = send(ctx, action="add_button", name=first, panel=panel, template=template)
    ctx.expect.record("button added to the panel", bool(added.get("ok")), added.get("error", "ok"), "ok")
    time.sleep(1.0)
    ctx.screenshot("button-added")
    if stage == "add":
        return ctx.result()
    return ctx.result()


SCAN_X = tuple(round(0.50 + 0.01 * i, 3) for i in range(18))
SCAN_Y = (0.935, 0.945, 0.955)


def find_hover(ctx):
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(0.15)
            if send(ctx, action="state").get("hovered"):
                return fx, fy
    return None


def run_clone(ctx, widget, panel) -> dict:
    added = send(ctx, action="add_clone", name=widget, panel=panel)
    ctx.expect.record("clone added to the bar", bool(added.get("ok")), added.get("error", "ok"), "ok")
    time.sleep(1.0)
    ctx.screenshot("clone-added")
    found = find_hover(ctx)
    ctx.expect.record("mouse hovered the clone", found is not None, str(found), "found")
    if not found:
        return ctx.result()
    time.sleep(0.5)
    ctx.screenshot("clone-hover")
    ctx.click_with_mouse(*found)
    time.sleep(1.5)
    state = send(ctx, action="state")
    ctx.expect.record("one click reached the Lua callback", state.get("clicks") == 1, state.get("clicks"), "1")
    ctx.screenshot("clone-after-click")
    if ctx.variant_option("BLOCK", "0") == "1":
        # World point that selected a burgage plot in run 20261021-035925-a56f. Overlay first, then the same click without it.
        world_xy = (found[0] - 0.291, found[1])
        send(ctx, action="add_overlay")
        time.sleep(1.0)
        ctx.screenshot("overlay-on")
        ctx.hover_with_mouse(*world_xy)
        time.sleep(0.4)
        ctx.click_with_mouse(*world_xy)
        time.sleep(1.5)
        ctx.screenshot("world-click-with-overlay")
        send(ctx, action="close")
        time.sleep(0.8)
        ctx.hover_with_mouse(*world_xy)
        time.sleep(0.4)
        ctx.click_with_mouse(*world_xy)
        time.sleep(1.5)
        ctx.screenshot("world-click-without-overlay")
    return ctx.result()
