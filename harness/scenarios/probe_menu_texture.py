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


def run(ctx) -> dict:
    path = Path(ctx.variant_option("PNG_PATH", str(DEFAULT_PNG))).as_posix()
    loaded = send(ctx, action="load_png", path=path)
    ctx.expect.record("PNG loaded as a texture", bool(loaded.get("ok")), loaded.get("error", "ok"), "ok")
    if not loaded.get("ok"):
        return ctx.result()
    try:
        shown = send(ctx, action="show", width=1280, height=720)
        ctx.expect.record("image shown in the viewport", bool(shown.get("in_viewport")), shown.get("error", shown.get("in_viewport")), True)
        ctx.screenshot("png-fullscreen")
        for label, width, height in (("small", 200, 200), ("wide", 600, 300)):
            answer = send(ctx, action="box", width=width, height=height, margin=0.0625)
            ctx.expect.record(f"box draw {label}", bool(answer.get("ok")), answer.get("error", "ok"), "ok")
            ctx.screenshot(f"box-{label}")
    finally:
        send(ctx, action="close")
    return ctx.result()
