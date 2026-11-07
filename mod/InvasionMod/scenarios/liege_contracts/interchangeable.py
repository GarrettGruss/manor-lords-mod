"""update-contract-interchangeable-goods (#589): a contract card for a pair of goods (berries or mushrooms, hides or pelts).

Needs the pak: `run.py --scenario liege-contracts-interchangeable --pak InvasionMod --slot 1`. It saves nothing. The default fixture has a built manor.
It deals two pair contracts, gives a mix of the two goods, checks the card texts and the storage line, takes a picture, and fulfils the berries card
with the press command: the larger stock is taken first.
"""

import time

from _new_game import begin_game

NAME = "liege-contracts-interchangeable"
DESCRIPTION = "Show contract cards for the pairs berries or mushrooms and hides or pelts, fulfil with a mix of both goods. Needs --pak InvasionMod."
LIMIT_S = 300
PREFIX = "InvasionMod."
SETTLE_S = 2.2
BERRIES, MUSHROOMS, HIDES, PELTS = 171, 279, 3, 9
EEL, STONE, CLAY, SALT = 32, 27, 146, 145
SAUSAGES, SMOKED_FISH, BREAD, TOOLS, ALE, CLOTHES = 320, 323, 172, 6, 28, 149


def contract(tier, good, amount, kind, reward_good, reward_amount):
    return f"{tier}-{good}-{amount}-{kind}-{reward_good}-{reward_amount}-0"


OFFER = ".".join([
    contract("s", BERRIES, 40, "g", SALT, 25), contract("s", HIDES, 20, "g", CLAY, 25), contract("s", EEL, 30, "g", STONE, 20),
    contract("m", SAUSAGES, 24, "g", TOOLS, 15), contract("m", SMOKED_FISH, 20, "g", ALE, 20), contract("m", BREAD, 36, "g", CLOTHES, 10),
    contract("l", 2, 3, "k", 0, 10), contract("l", 1, 1, "l", 0, 1), contract("l", 3, 3, "p", 0, 5),
])


def menu(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_menu_state")


def stock(ctx, good: int) -> int:
    return int(ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False]))


def disabled(state: dict, name: str):
    return next(b["disabled"] for b in state["buttons"] if b["name"] == name)


def run(ctx) -> dict:
    begin_game(ctx)
    expect = ctx.expect
    ctx.actions.set_silver(1000)
    ctx.mod.command(PREFIX + "liege_menu_close")
    expect.equals("I1 the window opened", ctx.mod.command(PREFIX + "liege_menu_open").get("ok"), True)
    time.sleep(SETTLE_S)
    ctx.mod.command(PREFIX + "liege_contracts_offer_now", ids=OFFER)
    berries0, mushrooms0, hides0, pelts0 = (stock(ctx, g) for g in (BERRIES, MUSHROOMS, HIDES, PELTS))
    ctx.actions.give_item(BERRIES, 25)
    ctx.actions.give_item(MUSHROOMS, 20)
    ctx.actions.give_item(PELTS, 20)
    time.sleep(SETTLE_S + 0.8)
    state = menu(ctx)
    texts = state["texts"]
    expect.equals("I2 the berries card names both goods", (texts.get("ReqLabel0_0"), texts.get("ReqText0_0")), ("Deliver", "40 BERRIES/FUNGI"))
    expect.equals("I3 the hides card names both goods", (texts.get("ReqLabel0_1"), texts.get("ReqText0_1")), ("Deliver", "20 HIDES OR PELTS"))
    pair_storage = stock(ctx, BERRIES) + stock(ctx, MUSHROOMS)
    expect.equals("I4 the storage line adds both goods", texts.get("HaveText0_0") or texts.get("HaveMiss0_0"), f"In storage: {pair_storage} / 40")
    expect.equals("I4b the pair holds at least the 45 that were given", pair_storage >= berries0 + mushrooms0 + 45, True)
    ctx.metric("pair_storage", pair_storage)
    expect.equals("I5 both pair cards can be fulfilled (the pelts pay the hides card)", [not disabled(state, f"FulfilButton0_{c}") for c in (0, 1)], [True, True])
    expect.equals("I6 the shown texts equal the wanted texts", {k: texts.get(k) for k in state["wanted_texts"]}, state["wanted_texts"])
    ctx.screenshot("pair-cards")

    before = {g: stock(ctx, g) for g in (BERRIES, MUSHROOMS)}
    try:
        ctx.mod.command(PREFIX + "liege_menu_press", button="FulfilButton0_0")
    except Exception as error:  # noqa: BLE001 - a refused press is a result, the asserts decide
        ctx.log.info(f"press: {error}")
    ctx.run_until(lambda: menu(ctx)["fulfils"] >= 1, 8, what="the click fulfils the berries card", poll_s=0.5)
    time.sleep(SETTLE_S)
    taken = {g: before[g] - stock(ctx, g) for g in before}
    expect.equals("I7 40 units left the stores, from both goods", sum(taken.values()), 40)
    larger = BERRIES if before[BERRIES] >= before[MUSHROOMS] else MUSHROOMS
    smaller = MUSHROOMS if larger == BERRIES else BERRIES
    expect.equals("I8 the larger stock is taken first", (taken[larger], taken[smaller]), (min(before[larger], 40), 40 - min(before[larger], 40)))
    ctx.metric("taken_berries", taken[BERRIES])
    ctx.metric("taken_mushrooms", taken[MUSHROOMS])
    ctx.screenshot("pair-cards-after")
    ctx.mod.command(PREFIX + "liege_menu_close")
    ctx.run_until(lambda: not menu(ctx)["open"], 8, what="the window closes", poll_s=0.5)
    ctx.metric("start_hides", hides0)
    ctx.metric("start_pelts", pelts0)
    return ctx.result()
