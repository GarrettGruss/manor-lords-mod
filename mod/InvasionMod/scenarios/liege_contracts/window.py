"""update-liege-contracts-tiers: the liege window shows nine contracts in three tiers; presses fulfil them.

Needs the pak: `run.py --scenario liege-contracts-window --pak InvasionMod --slot 1`. It saves nothing. Two starts, as the arms shipment scenario had (a manor decides what the Fulfil buttons do):
- the default fixture (a built manor): buttons are enabled when goods and the tier limit allow; real clicks fulfil;
- `--new-game` (no manor): all Fulfil buttons are greyed, the line "Build a manor to fulfil contracts." shows, a click does nothing.
Pictures: empty state, nine cards, after a fulfilment (or without a manor).
"""

import time

NAME = "liege-contracts-window"
DESCRIPTION = "Open the liege window, show nine contracts, fulfil with the press command (manor) or see greyed buttons (no manor), take pictures. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 2.2  # the window writes the visibility once more 1.5 s after the open
PLANKS, BERRIES, SALT, CLAY = 17, 171, 145, 146
METAL_BARS, CUT_STONE, TOOLS, SWORDS = 35, 283, 6, 177
HELMETS, PLATE, SAUSAGES = 273, 293, 320


def contract(tier, good, amount, kind, reward_good, reward_amount):
    return f"{tier}-{good}-{amount}-{kind}-{reward_good}-{reward_amount}-0"


OFFER = ".".join([
    contract("s", PLANKS, 50, "g", CLAY, 30), contract("s", BERRIES, 70, "r", 0, 60), contract("s", SALT, 30, "g", PLANKS, 25),
    contract("m", METAL_BARS, 24, "w", SWORDS, 15), contract("m", CUT_STONE, 30, "s", 0, 200), contract("m", TOOLS, 15, "g", METAL_BARS, 20),
    contract("l", HELMETS, 9, "t", 0, 1), contract("l", PLATE, 5, "i", 0, 1000), contract("l", SAUSAGES, 18, "t", 0, 1),
])
def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_menu_state")


def contracts(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_contracts_state")


def click(ctx, name: str) -> None:
    """The same code as a click (liege_menu_press). The PC has no mouse device, so no real click is sent."""
    try:
        ctx.mod.command(PREFIX + "liege_menu_press", button=name)
    except Exception as error:  # noqa: BLE001 - a refused press is a result, the asserts decide
        ctx.log.info(f"press {name}: {error}")
    time.sleep(SETTLE_S)


def stock(ctx, good: int) -> int:
    return int(ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False]))


def disabled(state: dict, name: str):
    return next(b["disabled"] for b in state["buttons"] if b["name"] == name)


def has_built_manor(ctx) -> bool:
    return any(module["built"] for module in ctx.actions.manor_state()["modules"])


def check_layout(ctx, state: dict, has_manor: bool) -> None:
    expect = ctx.expect
    texts = state["texts"]
    expect.equals("W4 the shown texts equal the wanted texts", {k: texts.get(k) for k in state["wanted_texts"]}, state["wanted_texts"])
    expect.equals("W5 nine cards show their requirement", sum(1 for k, v in texts.items() if k.startswith("ReqText") and v), 9)
    expect.equals("W6 the first card text", texts.get("ReqText0_0"), "Deliver 50 planks")
    expect.equals("W7 the first reward text", texts.get("RewText0_0"), "+30 clay")
    expect.equals("W8 the tier boxes show the name and the count", [(texts.get(f"TierName{i}"), texts.get(f"TierCount{i}")) for i in range(3)],
                  [("Small", "0 / 1"), ("Medium", "0 / 1"), ("Large", "0 / 1")])
    expect.equals("W9 the top bar has the two countdowns", ["days remaining" in texts["RemainText"], "In spring, in" in texts["RefreshText"]], [True, True])
    names = {b["name"] for b in state["buttons"]}
    expect.equals("W10 nine Fulfil buttons and the Close button exist", len(names), 10)
    expect.equals("W11 no arms button", [n for n in names if "Arms" in n or "Pick" in n or "Complete" in n], [])
    notice = texts.get("NoticeText")
    if has_manor:
        expect.equals("W12 with a manor there is no notice line", notice, "")
    else:
        expect.equals("W12 without a manor the notice line shows", notice, "Build a manor to fulfil contracts.")
        expect.equals("W13 without a manor every Fulfil button is greyed",
                      all(disabled(state, f"FulfilButton{r}_{c}") for r in range(3) for c in range(3)), True)


def run(ctx) -> dict:
    expect = ctx.expect
    has_manor = has_built_manor(ctx)
    ctx.metric("manor_built", 1 if has_manor else 0)
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("W1 the window opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    expect.equals("W2 the window is in the viewport", state["in_viewport"], True)
    expect.equals("W3 no offer: the notice text shows", "start of spring" in state["texts"].get("NoticeText", ""), True)
    expect.equals("W3b no offer: the cards are collapsed", state.get("card_visibility"), 1)
    ctx.screenshot("window-empty" if has_manor else "window-empty-no-manor")

    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=OFFER)
    for good, amount in ((PLANKS, 55), (CUT_STONE, 30), (PLATE, 5)):
        ctx.actions.give_item(good, amount)
    time.sleep(SETTLE_S + 0.8)
    state = menu(ctx)
    check_layout(ctx, state, has_manor)
    ctx.screenshot("window-nine-cards" if has_manor else "window-nine-cards-no-manor")

    if not has_manor:
        before, planks = menu(ctx)["presses"], stock(ctx, PLANKS)
        click(ctx, "FulfilButton0_0")
        expect.equals("W14 without a manor a click on Fulfil does nothing", (menu(ctx)["presses"], stock(ctx, PLANKS)), (before, planks))
        expect.equals("W15 no contract was fulfilled", contracts(ctx)["done"], 0)
        click(ctx, "CloseButton")
        ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the window", poll_s=0.5)
        return ctx.result()

    expect.equals("W14 enabled: small-1 (planks 55), medium-2 (cut stone), large-2 (plate armor)",
                  [not disabled(state, f"FulfilButton{r}_{c}") for r, c in ((0, 0), (1, 1), (2, 1))], [True, True, True])
    expect.equals("W15 greyed: small-2 (no berries)", disabled(state, "FulfilButton0_1"), True)

    planks, clay = stock(ctx, PLANKS), stock(ctx, CLAY)
    click(ctx, "FulfilButton0_0")
    ctx.run_until(lambda: menu(ctx)["fulfils"] >= 1, 8, what="the click fulfils small-1", poll_s=0.5)
    time.sleep(SETTLE_S)
    expect.equals("W16 50 planks left the stores and 30 clay arrived", (planks - stock(ctx, PLANKS), stock(ctx, CLAY) - clay), (50, 30))
    state = menu(ctx)
    expect.equals("W17 the tier count and the card label changed", (state["texts"].get("TierCount0"), next(b["label"] for b in state["buttons"] if b["name"] == "FulfilButton0_0")),
                  ("1 / 1", "Fulfilled"))
    expect.equals("W18 the other Small buttons are greyed by the tier limit", [disabled(state, f"FulfilButton0_{c}") for c in (1, 2)], [True, True])

    ctx.actions.give_item(BERRIES, 70)
    time.sleep(SETTLE_S)
    before = menu(ctx)["presses"]
    berries = stock(ctx, BERRIES)
    click(ctx, "FulfilButton0_1")
    expect.equals("W19 a click on a greyed button changes nothing", (menu(ctx)["presses"], stock(ctx, BERRIES)), (before, berries))

    silver = int(ctx.mod.command(PREFIX + "liege_state")["silver"])
    click(ctx, "FulfilButton1_1")
    ctx.run_until(lambda: menu(ctx)["fulfils"] >= 2, 8, what="the click fulfils medium-2", poll_s=0.5)
    expect.equals("W20 the silver rose by 200", int(ctx.mod.command(PREFIX + "liege_state")["silver"]) - silver, 200)
    influence = ctx.mod.command(PREFIX + "liege_state")["influence"]
    click(ctx, "FulfilButton2_1")
    ctx.run_until(lambda: menu(ctx)["fulfils"] >= 3, 8, what="the click fulfils large-2", poll_s=0.5)
    expect.equals("W21 the influence rose by 1000", round(ctx.mod.command(PREFIX + "liege_state")["influence"] - influence, 2), 1000.0)
    time.sleep(SETTLE_S)
    state = menu(ctx)
    expect.equals("W22 all three tiers show 1 / 1", [state["texts"].get(f"TierCount{i}") for i in range(3)], ["1 / 1"] * 3)
    expect.equals("W23 the shown texts equal the wanted texts", {k: state["texts"].get(k) for k in state["wanted_texts"]}, state["wanted_texts"])
    expect.equals("W24 three contracts are done and no reward failed", (contracts(ctx)["done"], contracts(ctx)["failed_rewards"]), (3, 0))
    ctx.screenshot("window-after-fulfil")

    click(ctx, "CloseButton")
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the close button closes the window", poll_s=0.5)
    return ctx.result()
