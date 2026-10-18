"""Spec 34 spike: N real single clicks on a pak button widget must each reach a hook exactly once.

Needs the pak: `run.py --scenario invasion-click-probe --pak clickprobe`. Real mouse input: no other game at the same time.
"""

import time

from runlib import osinput

NAME = "invasion-click-probe"
DESCRIPTION = "Spike for spec 34: count hook events for real single clicks on a pak button. Needs --pak clickprobe."
LIMIT_S = 400
EXCLUSIVE = True
LONG_REASON = "Real mouse input."
PREFIX = "InvasionMod."
CLICKS = 10
GAP_S = 1.0
HOVER_WAIT_S = 0.15
SCAN_X = tuple(round(0.30 + 0.02 * step, 3) for step in range(16))
SCAN_Y = tuple(round(0.30 + 0.02 * step, 3) for step in range(18))


def state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "click_probe_state")


def find_button(ctx) -> tuple:
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if state(ctx)["hovered"]:
                ctx.log.info(f"button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered the button")


def run(ctx) -> dict:
    opened = ctx.mod.command(PREFIX + "click_probe_open")
    ctx.expect.equals("the probe widget opened", opened.get("ok"), True)
    time.sleep(1.0)
    ctx.screenshot("click-probe")
    fx, fy = find_button(ctx)
    before = state(ctx)["clicks"]
    for _ in range(CLICKS):
        ctx.click_with_mouse(fx, fy)
        time.sleep(GAP_S)
    after = state(ctx)
    ctx.log.info(f"clicks {before} -> {after['clicks']} times {after['times']}")
    ctx.expect.equals("each click reached the hook once", after["clicks"] - before, CLICKS)
    return ctx.result()
