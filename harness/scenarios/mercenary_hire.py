"""Hire a mercenary company: the cost is paid and the units are there, by template and count (spec 10, spike P5, criterion P5)."""

from runlib import battle

NAME = "mercenary-hire"
DESCRIPTION = "hire_mercenaries takes the silver cost of the cheapest offered company and adds its squads (units by template) at once."
COVERS = ["P5"]
LIMIT_S = 150

SILVER_BUFFER = 40
MAX_COST = 400          # the offers seen cost 50 to 110
MIN_SQUAD_UNITS = 12    # a squad has 18 to 60 units; far below that means the spawn failed
HOLD_GAME_SECONDS = 10


def cheapest(offers: list[dict]) -> dict:
    return min(offers, key=lambda offer: offer["cost"])


def check_offers(ctx) -> dict | None:
    expect = ctx.expect
    listed = ctx.actions.mercenary_offers()
    expect.at_least("companies on offer", len(listed["offers"]), 1)
    if not listed["offers"]:
        return None
    for offer in listed["offers"]:
        expect.in_range(f"cost of {offer['name']}", offer["cost"], 1, MAX_COST)
        expect.at_least(f"units of {offer['name']}", len(offer["units"]), 1)
    return cheapest(listed["offers"])


def check_refused_without_silver(ctx, offer: dict) -> None:
    ctx.actions.set_silver(offer["cost"] - 1)
    try:
        ctx.actions.hire_mercenaries(offer["name"])
        ctx.expect.record("hire without enough silver is refused", False, "accepted", "refused")
    except battle.BattleError as error:
        ctx.expect.record("hire without enough silver is refused", True, str(error)[:70], "BattleError")
    ctx.expect.equals("nothing was hired", ctx.actions.mercenary_offers()["hired"] or 0, 0)
    ctx.expect.equals("no units yet", battle.alive(ctx.actions.battle_state(), "player"), 0)


def check_company_present(ctx, offer: dict, answer: dict) -> None:
    expect = ctx.expect
    state = ctx.actions.battle_state()
    expect.equals("squads equal the units of the company", len(state["squads"]), len(offer["units"]))
    expect.equals("squad templates", sorted(squad["template"] for squad in state["squads"]), sorted(offer["units"]))
    for squad in state["squads"]:
        expect.at_least(f"units in squad {squad['id']} ({squad['template']})", squad["alive"], MIN_SQUAD_UNITS)
    expect.equals("living player units equal the answer", battle.alive(state, "player"), answer["units"])
    census = ctx.actions.units_census()
    expect.at_least("the census counts the player units", census["by_side"].get("player", 0), answer["units"])
    expect.equals("the offer left the list", offer["name"] in battle.offer_names(ctx.actions.mercenary_offers()["offers"]), False)


def run(ctx) -> dict:
    expect = ctx.expect
    offer = check_offers(ctx)
    if offer is None:
        return ctx.result()
    ctx.log.info(f"hiring {offer['name']}: cost {offer['cost']}, units {offer['units']}")
    check_refused_without_silver(ctx, offer)

    ctx.actions.set_silver(offer["cost"] + SILVER_BUFFER)
    record = ctx.actions.hire_mercenaries(offer["name"])
    answer = record["answer"]
    expect.in_range("silver paid", answer["silver_before"] - answer["silver_after"], offer["cost"], offer["cost"])
    expect.equals("silver left", answer["silver_after"], SILVER_BUFFER)
    expect.equals("hired companies", answer["hired_after"], (answer["hired_before"] or 0) + 1)
    check_company_present(ctx, offer, answer)

    ctx.time.run_game_seconds(HOLD_GAME_SECONDS, speed=3)
    held = battle.alive(ctx.actions.battle_state(), "player")
    expect.at_least("units still there after a few game seconds", held, int(answer["units"] * 0.9))
    ctx.metric("mercenary_units", answer["units"])
    ctx.metric("mercenary_cost", offer["cost"])
    ctx.actions.clear_battle()
    return ctx.result()
