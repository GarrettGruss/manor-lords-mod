"""Spike scenario (change spike-menu-custom-textures, #333, candidate 2): show a PNG that is loaded at run time in an Image.

Steps: load the test PNG, show it full screen (screenshot), draw it as Box (9-slice) at two sizes (two screenshots), close.
Each step answer is logged. A failed step is a result, not a harness error: read the log and the answers.
Option: PNG_PATH (default: the test picture in the change folder).
"""
from pathlib import Path

NAME = "probe-menu-texture"
DESCRIPTION = "Spike: ImportFileAsTexture2D + Image:SetBrushFromTexture in a mod widget; Box margins at two sizes; screenshots."
COVERS: list[str] = []
LIMIT_S = 180
HIDDEN = True

DEFAULT_PNG = Path(__file__).resolve().parents[2] / "openspec/changes/spike-menu-custom-textures/assets/test_frame.png"


def send(ctx, **fields) -> dict:
    try:
        answer = ctx.commands.send("texture_probe", **fields)
    except Exception as error:  # a refused step is data for the spike
        ctx.log.info(f"texture_probe {fields.get('action')} refused: {error}")
        return {"ok": False, "error": str(error)}
    ctx.log.info(f"texture_probe {fields.get('action')}: {answer}")
    return answer


def raise_game_window(ctx) -> None:
    """Put the game window on top without the focus, so other windows are not in the screenshots."""
    import ctypes
    from runlib.game import find_game_processes
    from runlib.windows import list_windows, pick_game_window
    try:
        window = pick_game_window(list_windows(), {process.pid for process in find_game_processes()})
        ctypes.windll.user32.SetWindowPos(window["hwnd"], -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)  # TOPMOST, no move, no size, no activate
    except Exception as error:  # noqa: BLE001 - a spike helper
        ctx.log.info(f"raise_game_window failed: {error}")


def run(ctx) -> dict:
    raise_game_window(ctx)
    path = Path(ctx.variant_option("PNG_PATH", str(DEFAULT_PNG))).as_posix()
    loaded = send(ctx, action="load_png", path=path)
    ctx.expect.record("PNG loaded as a texture", bool(loaded.get("ok")), loaded.get("error", "ok"), "ok")
    if not loaded.get("ok"):
        return ctx.result()
    try:
        shown = send(ctx, action="show", width=1280, height=720)
        ctx.expect.record("image shown in the viewport", bool(shown.get("in_viewport")), shown.get("error", shown.get("in_viewport")), "in viewport")
        import time
        time.sleep(1.0)  # one layout pass before the picture
        ctx.screenshot("png-fullscreen")
        for label, width, height in (("small", 200, 200), ("wide", 600, 300)):
            answer = send(ctx, action="box", width=width, height=height, margin=0.0625)
            ctx.expect.record(f"box draw {label}", bool(answer.get("ok")), answer.get("error", "ok"), "ok")
            ctx.screenshot(f"box-{label}")
    finally:
        send(ctx, action="close")
    return ctx.result()
