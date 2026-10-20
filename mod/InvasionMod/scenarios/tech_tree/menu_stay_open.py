"""Spec 34 (issue #272): a mod menu stays open for 300 s and its clicks still count afterwards.

Needs the pak: `run.py --scenario tech-tree-menu-stay-open --pak techmenu`. Real mouse input: no other game at the same time.
A 50 ms scheduler tick once broke the Lua state after about 3 minutes with a menu open. The tick is now 100 ms.
The scenario reads the menu state twice a second for the whole wait. Every read must return an open menu without an error.
Then 10 real single clicks must be counted exactly once each. It saves nothing.
"""

import time

NAME = "tech-tree-menu-stay-open"
DESCRIPTION = "Open the tech tree menu, read its state twice a second for 300 s, then click a law button 10 times. The menu stays alive and 10 clicks count. Needs --pak techmenu."
LIMIT_S = 900
EXCLUSIVE = True
LONG_REASON = "300 s wait with the menu open, then hover scan and real mouse clicks."
PREFIX = "InvasionMod."
SETTLE_S = 1.0
WAIT_S = 300
READ_PERIOD_S = 0.5
CLICKS = 10
GAP_S = 1.0
HOVER_WAIT_S = 0.15
SCAN_X = (0.22, 0.24, 0.26, 0.28, 0.30, 0.32)
SCAN_Y = tuple(round(0.90 + 0.01 * step, 2) for step in range(8))


def widget(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_widget_state")


def find_law_button(ctx) -> tuple:
    for fy in SCAN_Y:
        for fx in SCAN_X:
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if any(row.get("hovered") and row.get("visibility") == 0 for row in widget(ctx)["laws"]):
                ctx.log.info(f"law button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered a visible law button")


def watch_menu(ctx) -> tuple:
    """Return (reads, bad_reads). A bad read is a closed menu, a state error or a failed command."""
    reads = bad_reads = 0
    end = time.monotonic() + WAIT_S
    while time.monotonic() < end:
        reads += 1
        try:
            state = widget(ctx)
            bad = not state.get("open") or bool(state.get("last_error"))
        except Exception as error:  # a dead Lua state shows here; count it and keep reading
            ctx.log.info(f"state read {reads} failed: {error}")
            bad = True
        if bad:
            bad_reads += 1
            ctx.log.info(f"state read {reads} is not healthy")
        time.sleep(READ_PERIOD_S)
    return reads, bad_reads


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    ctx.expect.equals("the widget opened", ctx.mod.command(PREFIX + "tech_tree_widget_open").get("ok"), True)
    time.sleep(SETTLE_S)
    ctx.mod.command(PREFIX + "tech_tree_widget_press", kind="path", index=2)  # the laws need a path and two unlocked nodes
    ctx.actions.set_settlement_level(2)
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["slots"] >= 2, 15, what="two node slots")
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)
    time.sleep(SETTLE_S)

    reads, bad_reads = watch_menu(ctx)
    ctx.metric("state_reads", reads)
    ctx.metric("bad_state_reads", bad_reads)
    ctx.expect.equals("every state read in the wait was healthy", bad_reads, 0)
    ctx.screenshot("tech-tree-menu-stay-open")

    fx, fy = find_law_button(ctx)
    before = widget(ctx)["clicks"]
    for _ in range(CLICKS):
        ctx.click_with_mouse(fx, fy)
        time.sleep(GAP_S)
    time.sleep(SETTLE_S)
    counted = widget(ctx)["clicks"] - before
    ctx.log.info(f"clicks counted {counted} of {CLICKS}")
    ctx.metric("clicks_sent", CLICKS)
    ctx.metric("clicks_counted", counted)
    ctx.expect.equals("each real click after the wait was counted exactly once", counted, CLICKS)
    ctx.mod.command(PREFIX + "tech_tree_widget_close")
    return ctx.result()
