"""Policy menu (spec 16, issue #60): the mod PolicyMenu lists the policies, a real click signs one, a second click unsigns it.

Needs the mod PolicyMenu with its pak: `uv run python harness\\run.py --scenario policy-menu --fixture base --pak policymenu`.
The pak is built by `pakmod.py build policymenu` from the files in mod/PolicyMenu/ue (a copy is in mod/PolicyMenu/paks).
Proof steps:
  1. The menu opens (command PolicyMenu.open) and shows the available policies of the game, with names.
  2. A real OS mouse click on a button signs the policy (policiesSigned has the id). A second click removes it.
  3. The key F7 closes and opens the menu.
The scenario takes screenshots of the open menu. Do not run the UE editor while a screenshot is taken: its firewall pop-up covers the game.
"""

import time

from runlib import osinput

NAME = "policy-menu"
DESCRIPTION = "Open the policy menu, click a policy button (signed), click again (unsigned), toggle the menu with F7. Needs --pak policymenu."
LIMIT_S = 300
LONG_REASON = "Waits for the widget and real mouse input."
COVERS = []
PREFIX = "PolicyMenu."
SETTLE_S = 1.0

# The geometry calls of the widget return a zero size in the real game, so the scenario finds the first button by hover.
# The start point comes from a screenshot (window 2582x1496, first button at about 27 % and 53 %).
FIRST_BUTTON_GUESS = (0.2735, 0.531)
SCAN_DX = (0.0, -0.03, 0.03, -0.06, 0.06)
SCAN_DY = (0.0, -0.01, 0.01, -0.02, 0.02, -0.03, 0.03)
HOVER_WAIT_S = 0.3


def signed_ids(ctx) -> list:
    return ctx.actions.policy_state()["signed"]


def read_menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "read")


def wait_for_signed(ctx, policy_id: int, wanted: bool, what: str) -> None:
    ctx.run_until(lambda: (policy_id in signed_ids(ctx)) == wanted, 8, what=what, poll_s=0.5)


def find_first_button(ctx) -> tuple:
    for dy in SCAN_DY:
        for dx in SCAN_DX:
            fx, fy = FIRST_BUTTON_GUESS[0] + dx, FIRST_BUTTON_GUESS[1] + dy
            ctx.hover_with_mouse(fx, fy)
            time.sleep(HOVER_WAIT_S)
            if read_menu(ctx)["slots"][0].get("hovered"):
                ctx.log.info(f"first button found by hover at ({fx:.3f}, {fy:.3f})")
                return fx, fy
    raise AssertionError("the mouse never hovered the first policy button")


def click_first_button(ctx) -> None:
    fx, fy = find_first_button(ctx)
    ctx.click_with_mouse(fx, fy)


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "close")
    opened = ctx.mod.command(PREFIX + "open")
    ctx.log.info(f"open {opened}")
    expect.equals("the menu opened", opened.get("ok"), True)
    time.sleep(SETTLE_S)  # the widget needs a frame before it is painted

    menu = read_menu(ctx)
    ctx.log.info(f"menu {menu}")
    expect.equals("the menu is in the viewport", menu["in_viewport"], True)
    expect.at_least("the menu lists the available policies", len(menu["slots"]), 1)
    names = [slot["name"] for slot in menu["slots"]]
    ctx.log.info(f"names {names}")
    expect.equals("every policy has a game name (not the fallback Policy N)", [n for n in names if n.startswith("Policy ")], [])
    ctx.screenshot("policy-menu")

    policy_id = menu["slots"][0]["id"]
    if policy_id in signed_ids(ctx):
        ctx.actions.policy_sign(policy_id, False)
    click_first_button(ctx)
    wait_for_signed(ctx, policy_id, True, "the click signs the policy")
    expect.equals("a click signed the policy", policy_id in signed_ids(ctx), True)
    time.sleep(SETTLE_S)
    ctx.screenshot("policy-menu-signed")
    shown = {entry["id"]: entry["signed"] for entry in read_menu(ctx)["slots"]}
    expect.equals("the menu shows the policy as signed", shown.get(policy_id), True)

    click_first_button(ctx)
    wait_for_signed(ctx, policy_id, False, "the second click unsigns the policy")
    expect.equals("a second click unsigned the policy", policy_id in signed_ids(ctx), False)

    ctx.press_key(osinput.VK_F7)
    expect.equals("F7 closes the menu", read_menu(ctx)["open"], False)
    ctx.press_key(osinput.VK_F7)
    expect.equals("F7 opens the menu", read_menu(ctx)["open"], True)
    ctx.mod.command(PREFIX + "close")
    return ctx.result()
