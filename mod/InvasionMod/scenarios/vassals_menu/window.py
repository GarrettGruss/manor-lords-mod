"""Change add-vassals-menu (#564): the Vassals window shows the vassals, sets a policy, and restores a wiped village.

Needs the pak: `run.py --scenario vassals-menu-window --pak InvasionMod --slot 1` (or slot 2; never slot auto). It saves nothing.
The scenario adopts two AI-lord regions of the test map as vassals (command `vassals_adopt`): Krumme Leite (internal name immenreuth)
and Hochweg (internal name Goldhof). Then:
- the bottom bar entry opens the menu (`menu_press`, the same path as a bar click after the hook) and the header and cards show the state;
- a click on Heavy sets the policy of the card and the header tribute changes within 2 s;
- a sack wipes the second vassal: its card shows "Wiped" and the restore button; with too little silver the button is disabled;
- a click on "Restore the village" takes 100 silver and the card shows "Rebuilding".
Pictures (`ctx.screenshot`): two vassals and a free slot, policy Heavy, a wiped village, a disabled restore, a rebuilding village.
The menu pauses the game while it is open, so the game days of the sack run with the menu closed.
"""

import time

from runlib.osinput import Win32Input

from _new_game import begin_game

NAME = "vassals-menu-window"
DESCRIPTION = "Open the Vassals window, set a policy, see a wiped village, restore it, take pictures. Needs --pak InvasionMod."
LIMIT_S = 1500
SPEED = 3
LONG_REASON = "Two adoptions, a sack that runs until the wipe (up to 20 game days at speed 3), then the window checks."
PREFIX = "InvasionMod."
SETTLE_S = 2.2        # the window writes every value once more 1.5 s after the open
REFRESH_WAIT_S = 1.6  # the window refreshes twice a second
GROWTH_DAYS = 1
RESTORE_COST = 100
REGIONS = ("immenreuth", "Goldhof")


def front(ctx) -> None:
    """Other runs share the screen: bring this game window to the front (pictures and the clock need it)."""
    Win32Input().bring_to_front(ctx.game_window()["hwnd"])
    time.sleep(0.5)


def shot(ctx, name: str) -> None:
    front(ctx)
    ctx.screenshot(name)


def vassals(ctx) -> dict:
    return ctx.mod.command(PREFIX + "vassals_state")


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "vassals_menu_state")


def bar(ctx) -> dict:
    return ctx.mod.command(PREFIX + "menu_state")


def press(ctx, button: str) -> dict:
    """The same code as a click (vassals_menu_press). The PC may have no mouse device, so no real click is sent."""
    try:
        answer = ctx.mod.command(PREFIX + "vassals_menu_press", button=button)
    except Exception as error:  # noqa: BLE001 - a refused press is a result, the checks decide
        ctx.log.info(f"press {button}: {error}")
        answer = {}
    time.sleep(REFRESH_WAIT_S)
    return answer


def open_menu(ctx) -> None:
    front(ctx)
    """One click on the bottom bar entry (the request goes through the same tick as a bar click)."""
    ctx.mod.command(PREFIX + "menu_press", id="vassals")
    ctx.run_until(lambda: bar(ctx).get("open_id") == "vassals" and menu(ctx)["in_viewport"], 10, what="the Vassals window opens", poll_s=0.5)
    time.sleep(SETTLE_S)


def close_menu(ctx) -> None:
    ctx.mod.command(PREFIX + "vassals_menu_close")
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the window closes", poll_s=0.5)


def texts_match(ctx, label: str) -> None:
    state = menu(ctx)
    ctx.check(f"{label}: the shown texts equal the wanted texts", {k: state["texts"].get(k) for k in state["wanted_texts"]} == state["wanted_texts"],
              {k: [state["texts"].get(k), v] for k, v in state["wanted_texts"].items() if state["texts"].get(k) != v})


def make_vassals(ctx) -> None:
    for region in REGIONS:
        answer = ctx.mod.command(PREFIX + "vassals_adopt", region=region)
        ctx.log.info(f"adopted {region}: slot {answer['adopted_slot']}")


def run(ctx) -> dict:
    begin_game(ctx)  # a new game waits at the start screen
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    make_vassals(ctx)
    ctx.time.run_game_days(GROWTH_DAYS, speed=SPEED)
    ctx.actions.set_silver(500)

    # 1. A sack wipes the second vassal. All game days run before the window opens: a window that was open and closed leaves the game
    # in a pause that the clock control cannot lift (run 20261105-041504-4068), so no game day runs after the first open.
    front(ctx)
    ctx.mod.command(PREFIX + "vassals_sack", slot=2)
    for _ in range(20):  # the wipe takes several polls after the collapses
        ctx.time.run_game_days(1, speed=SPEED)
        if vassals(ctx)["lost"] == 1:
            break
    ctx.check("V1 the second slot is wiped", vassals(ctx)["lost"] == 1 and len(vassals(ctx)["wiped"]) == 1, vassals(ctx)["wiped"])

    # 2. The bar entry opens the window; the header and the cards show the state.
    entry = next((row for row in bar(ctx)["buttons"] if row["id"] == "vassals"), None)
    ctx.check("V2 the bottom bar has the entry Vassals", entry is not None and entry["in_bar"] and entry["label"] == "Vassals", entry)
    open_menu(ctx)
    state = menu(ctx)
    cards = state["view"]["cards"]
    ctx.check("V3 the window is in the viewport and open", state["open"] and state["in_viewport"], state)
    ctx.check("V4 the header shows 1 / 3 vassals", state["view"]["count_text"] == "1 / 3" and state["texts"].get("HeadValue0") == "1 / 3", state["texts"].get("HeadValue0"))
    ctx.check("V5 the cards are vassal, wiped, free", [c["kind"] for c in cards] == ["vassal", "wiped", "free"], [c["kind"] for c in cards])
    ctx.check("V6 the vassal card shows a status, rich goods and a tribute", cards[0]["status_text"] in ("Thriving", "Stalled") and cards[0]["stats"][1] != "-" and cards[0]["stats"][2] != "none",
              cards[0]["stats"])
    ctx.check("V7 the wiped card shows Wiped, no lord and an enabled restore button", cards[1]["status_text"] == "Wiped" and cards[1]["lord_line"] == "No lord" and cards[1]["restore"]["enabled"],
              cards[1])
    ctx.check("V8 the wiped card has no policy option text", all(state["texts"].get(f"PolicyText1_{p}") == "" for p in range(3)), [state["texts"].get(f"PolicyText1_{p}") for p in range(3)])
    ctx.check("V9 the free slot card says how to gain a vassal", state["texts"].get("NoteText2") == "Claim and settle a region to gain a vassal.", state["texts"].get("NoteText2"))
    texts_match(ctx, "V10")
    ctx.log.info(f"header {state['texts'].get('HeadValue1')} | cards {[c['title'] for c in cards]}")
    shot(ctx, "01-vassal-wiped-village-free-slot")

    # 3. Too little silver: the button is disabled and a click does nothing.
    ctx.actions.set_silver(RESTORE_COST - 50)
    time.sleep(REFRESH_WAIT_S)
    restore = menu(ctx)["view"]["cards"][1]["restore"]
    ctx.check("V11 with 50 silver the restore is disabled and the hint says so", restore["enabled"] is False and restore["hint"] == "Needs 100 silver.", restore)
    shot(ctx, "02-restore-disabled")
    wiped_before = len(vassals(ctx)["wiped"])
    press(ctx, "RestoreButton1")
    ctx.check("V12 a click on the disabled button changes nothing", len(vassals(ctx)["wiped"]) == wiped_before and vassals(ctx)["silver"] == RESTORE_COST - 50, vassals(ctx)["silver"])

    # 4. A policy click.
    ctx.actions.set_silver(500)
    time.sleep(REFRESH_WAIT_S)
    tribute_before = menu(ctx)["texts"].get("HeadValue1")
    press(ctx, "PolicyButton0_2")
    state = menu(ctx)
    ctx.check("V13 a click on Heavy sets the policy of the first slot", vassals(ctx)["vassals"][0]["policy"] == "heavy", vassals(ctx)["vassals"][0])
    ctx.check("V14 the header tribute changed", state["texts"].get("HeadValue1") != tribute_before, [tribute_before, state["texts"].get("HeadValue1")])
    ctx.check("V15 the hint shows the heavy factor", state["view"]["cards"][0]["policy_hint"].startswith("Tribute x1.5: 150"), state["view"]["cards"][0]["policy_hint"])
    texts_match(ctx, "V16")
    shot(ctx, "03-policy-heavy")

    # 5. Enough silver: the click restores the village.
    press(ctx, "RestoreButton1")
    time.sleep(SETTLE_S)
    state = menu(ctx)
    cards = state["view"]["cards"]
    ctx.check("V17 the restore took 100 silver", int(vassals(ctx)["silver"]) == 500 - RESTORE_COST, vassals(ctx)["silver"])
    ctx.check("V18 the second card is a rebuilding vassal with no tribute", cards[1]["kind"] == "vassal" and cards[1]["status_text"] == "Rebuilding" and cards[1]["stats"][2] == "none",
              cards[1])
    ctx.check("V19 the header shows 2 / 3 and the treasury", state["view"]["count_text"] == "2 / 3" and state["texts"].get("HeadValue2") == "400 silver", state["texts"].get("HeadValue2"))
    texts_match(ctx, "V20")
    shot(ctx, "04-rebuilding-village")
    close_menu(ctx)
    ctx.check("V21 the window is closed", not menu(ctx)["open"] and bar(ctx).get("open_id") in (None, ""), bar(ctx).get("open_id"))
    ctx.metric("vassals_at_end", vassals(ctx)["count"])
    ctx.check("V22 the game runs on", vassals(ctx)["day"] is not None, vassals(ctx)["day"])
    return ctx.result()
