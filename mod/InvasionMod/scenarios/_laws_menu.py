"""Shared helpers of the test scenarios laws_menu/* (change add-laws-menu, #563).

The press command calls the same handlers as a click on a pak button. The PC may have no mouse device, so no real click is sent.
"""

import time

from runlib import windows
from runlib.game import find_game_processes

PREFIX = "InvasionMod."
SETTLE_S = 1.2  # the menu refreshes the texts every 0.5 s


def picture(ctx, name: str) -> None:
    """A screenshot copies screen pixels. Another slot may run at the same time: its UE4SS debug windows can lie over this game, so they
    are minimized first (no input is sent, no focus is taken). A problem here must not fail the checks."""
    try:
        mine = ctx.game_window()["rect"]
        everyone = {process.pid for process in find_game_processes()}
        for overlay in windows.overlay_windows(windows.list_windows(), everyone):
            left, top, right, bottom = overlay["rect"]
            if left < mine[2] and right > mine[0] and top < mine[3] and bottom > mine[1]:
                windows.minimize_window(overlay["hwnd"])
        time.sleep(0.5)
    except Exception as problem:  # noqa: BLE001
        ctx.log.info(f"overlay windows not minimized: {problem}")
    ctx.screenshot(name)


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "laws_menu_state")


def tech(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def press(ctx, action: str, **args) -> dict:
    """A press the menu accepts. Raises when the mod refuses it."""
    result = ctx.mod.command(PREFIX + "laws_menu_press", action=action, **args)
    time.sleep(SETTLE_S)
    return result


def refused_press(ctx, action: str, **args) -> str | None:
    """A press that the menu must refuse. Returns the message of the mod, or None when it was accepted."""
    reason = ctx.mod.refusal(PREFIX + "laws_menu_press", action=action, **args)
    time.sleep(SETTLE_S)
    return reason


def card(state: dict, law_id: str) -> dict:
    return next(row for row in state["cards"] if row["id"] == law_id)


def card_index(state: dict, law_id: str) -> int:
    return [row["id"] for row in state["cards"]].index(law_id)


def open_menu(ctx) -> dict:
    ctx.mod.command(PREFIX + "laws_menu_close")
    opened = ctx.mod.command(PREFIX + "laws_menu_open")
    ctx.check("the Laws menu opened", opened.get("ok") is True, opened)
    time.sleep(SETTLE_S)
    return menu(ctx)


def prepare_laws(ctx, nodes=("fair_courts", "amnesty", "militia_rights"), common=("night_watch",)) -> None:
    """Swear to Prosperity, add picks and unlock the nodes. Waits for the start pick first."""
    ctx.run_until(lambda: tech(ctx)["picks_earned"] >= 1, 30, what="the start pick")
    ctx.mod.command(PREFIX + "tech_tree_choose_path", path="prosperity")
    missing = len(nodes) + len(common) - tech(ctx)["picks_earned"]
    if missing > 0:
        ctx.mod.command(PREFIX + "tech_tree_test_grant_picks", count=missing)
    for node in list(nodes) + list(common):
        ctx.mod.command(PREFIX + "tech_tree_unlock", node=node)


def check_texts_match_cards(ctx, name: str, state: dict) -> None:
    """The texts of the widget equal the cards of the model, card by card."""
    texts = state["texts"]
    for index in range(9):
        shown = state["cards"][index] if index < len(state["cards"]) else None
        expected_name = shown["name"] if shown else ""
        ctx.check(f"{name} card {index} name", texts.get(f"NameText{index}") == expected_name, (texts.get(f"NameText{index}"), expected_name))
        if shown is None:
            continue
        ctx.check(f"{name} card {index} status", texts.get(f"StatusText{index}") == shown["status"].upper(), texts.get(f"StatusText{index}"))
        ctx.check(f"{name} card {index} source", texts.get(f"SourceText{index}") == shown["source"], texts.get(f"SourceText{index}"))
        ctx.check(f"{name} card {index} hint", texts.get(f"HintText{index}") == shown["hint"], texts.get(f"HintText{index}"))
        ctx.check(f"{name} card {index} button text", texts.get(f"ActText{index}") == shown["button"], texts.get(f"ActText{index}"))
        for line, effect in enumerate(shown["effects"]):
            ctx.check(f"{name} card {index} effect {line}", texts.get(f"EffText{index}_{line}") == effect["text"], texts.get(f"EffText{index}_{line}"))
    header = state["header"]
    for key, wanted in (("HdrSlotsValue", "slots_text"), ("HdrSlotsMax", "max_text"), ("HdrEnactValue", "enact_text"),
                        ("HdrRevokeValue", "revoke_text"), ("HdrUnlockValue", "unlocked_text"), ("RefreshText", "refresh_text")):
        ctx.check(f"{name} header {key}", texts.get(key) == header[wanted], (texts.get(key), header[wanted]))


def check_dialog_texts(ctx, name: str, state: dict) -> None:
    dialog = state.get("dialog")
    texts = state["texts"]
    if dialog is None:
        for key in ("DlgTitle", "DlgQuestion", "DlgCost", "DlgCancelText", "DlgConfirmText", "DlgEff0"):
            ctx.check(f"{name} dialog text {key} is empty", texts.get(key) == "", texts.get(key))
        return
    ctx.check(f"{name} dialog title", texts.get("DlgTitle") == dialog["title"].upper(), texts.get("DlgTitle"))
    ctx.check(f"{name} dialog question", texts.get("DlgQuestion") == dialog["question"], texts.get("DlgQuestion"))
    ctx.check(f"{name} dialog cost", texts.get("DlgCost") == dialog["cost"], texts.get("DlgCost"))
    ctx.check(f"{name} dialog buttons", (texts.get("DlgCancelText"), texts.get("DlgConfirmText")) == (dialog["cancel"], dialog["confirm"]),
              (texts.get("DlgCancelText"), texts.get("DlgConfirmText")))
    for line, effect in enumerate(dialog["effects"]):
        ctx.check(f"{name} dialog effect {line}", texts.get(f"DlgEff{line}") == effect["text"], texts.get(f"DlgEff{line}"))
