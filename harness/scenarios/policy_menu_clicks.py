"""Spec 34: real single clicks on a policy menu button each reach the click handler exactly once.

Needs the pak: `run.py --scenario policy-menu-clicks --fixture base --pak policymenu`. Real mouse input: no other game at the same time.
The click button of the menu is a Blueprint widget whose OnClicked event is a hook event (shared module HarnessClickHooks).
Each click signs or unsigns the first policy, so an even count of clicks ends where it started. The count `clicks` is the proof.
"""

import time


NAME = "policy-menu-clicks"
DESCRIPTION = "Click the first policy button of the policy menu with the real mouse 10 times, one click each second. Each click counts once. Needs --pak policymenu."
LIMIT_S = 600
EXCLUSIVE = True  # real mouse input: a parallel suite runs it with no other game
LONG_REASON = "Hover scan and real mouse clicks."
COVERS = []
PREFIX = "PolicyMenu."
SETTLE_S = 1.0
CLICKS = 10
GAP_S = 1.0
HOVER_WAIT_S = 0.3
FIRST_BUTTON_GUESS = (0.25, 0.57)
SCAN_DX = (0.0, -0.03, 0.03, -0.06, 0.06)
SCAN_DY = (0.0, -0.01, 0.01, -0.02, 0.02, -0.03, 0.03)


def read_menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "read")


def find_first_button(ctx) -> tuple:
    for dy in SCAN_DY:
        for dx in SCAN_DX:
            fx, fy = FIRST_BUTTON_GUESS[0] + dx, FIRST_BUTTON_GUESS[1] + dy
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            first = read_menu(ctx)["slots"][0]
            if first.get("hovered") and first.get("visibility") == 0:
                ctx.log.info(f"first button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered the first policy button")


def run(ctx) -> dict:
    ctx.mod.command(PREFIX + "close")
    ctx.expect.equals("the menu opened", ctx.mod.command(PREFIX + "open").get("ok"), True)
    time.sleep(SETTLE_S)
    menu = read_menu(ctx)
    policy_id = menu["slots"][0]["id"]
    if policy_id in ctx.actions.policy_state()["signed"]:
        ctx.actions.policy_sign(policy_id, False)
    fx, fy = find_first_button(ctx)
    before = read_menu(ctx)["clicks"]
    for _ in range(CLICKS):
        ctx.click_with_mouse(fx, fy)
        time.sleep(GAP_S)
    time.sleep(SETTLE_S)
    counted = read_menu(ctx)["clicks"] - before
    ctx.log.info(f"clicks counted {counted} of {CLICKS}")
    ctx.metric("clicks_sent", CLICKS)
    ctx.metric("clicks_counted", counted)
    ctx.expect.equals("each real click was counted exactly once", counted, CLICKS)
    ctx.expect.equals("an even number of clicks leaves the policy unsigned", policy_id in ctx.actions.policy_state()["signed"], False)
    ctx.mod.command(PREFIX + "close")
    return ctx.result()
