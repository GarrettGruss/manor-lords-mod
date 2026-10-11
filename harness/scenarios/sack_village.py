"""Take a share of the village away: buildings, goods and people (spec 10, spike S6, criterion S1)."""

from runlib import sack
from runlib.commands import CommandRefused

NAME = "sack-village"
DESCRIPTION = "sack_village removes a percent of the buildings (rubble), the goods and the families. Counts before and after stay in range."
COVERS = ["S1"]
LIMIT_S = 120

BUILDINGS_PCT = 50
STOCK_PCT = 50
PEOPLE_PCT = 40
MIN_BUILDINGS = 3   # the base fixture has 4
MIN_STOCK = 30      # the base fixture has about 79 items
MIN_FAMILIES = 4    # the base fixture has 5
STOCK_TOLERANCE = 5.0  # points: each good is rounded on its own


def unit_points(total: int) -> float:
    """One whole building or family, in percent of the total. Counts are whole, so a share is only this exact."""
    return 100.0 / total


def check_baseline(ctx, census: dict) -> None:
    ctx.expect.at_least("start: standing buildings", sack.standing(census), MIN_BUILDINGS)
    ctx.expect.equals("start: no rubble", sack.rubble(census), 0)
    ctx.expect.at_least("start: stock items", sack.stock_total(census), MIN_STOCK)
    ctx.expect.at_least("start: families", sack.families(census), MIN_FAMILIES)


def check_zero_sack_changes_nothing(ctx, before: dict) -> None:
    ctx.actions.sack_village(0, 0, 0)
    after = ctx.actions.sack_census()
    ctx.expect.equals("0 percent: buildings unchanged", after["buildings"], before["buildings"])
    ctx.expect.equals("0 percent: stock unchanged", sack.stock_total(after), sack.stock_total(before))
    ctx.expect.equals("0 percent: people unchanged", after["people"], before["people"])


def check_inputs_are_refused(ctx) -> None:
    for name, value in (("buildings_pct", 101), ("stock_pct", -1), ("people_pct", 1000)):
        try:
            ctx.actions.sack_village(**{"buildings_pct": 0, "stock_pct": 0, "people_pct": 0, name: value})
            ctx.expect.record(f"refused: {name}={value}", False, "accepted", "refused by Python")
        except sack.SackError as error:
            ctx.expect.record(f"refused: {name}={value}", True, str(error)[:50], "SackError")
    try:
        ctx.commands.send("sack_village", buildings_pct=101, stock_pct=0, people_pct=0)
        ctx.expect.record("mod refuses 101 percent", False, "accepted", "refused by the mod")
    except CommandRefused as error:
        ctx.expect.record("mod refuses 101 percent", True, error.reason[:50], "CommandRefused")


def check_shares(ctx, before: dict, after: dict) -> None:
    expect = ctx.expect
    lost_buildings = sack.removed_share(sack.standing(before), sack.standing(after))
    expect.in_range("buildings lost (percent)", lost_buildings, BUILDINGS_PCT - unit_points(sack.standing(before)) / 2,
                    BUILDINGS_PCT + unit_points(sack.standing(before)) / 2)
    expect.equals("buildings kept in the list as rubble", after["buildings"]["total"], before["buildings"]["total"])
    expect.equals("rubble count", sack.rubble(after), sack.share(sack.standing(before), BUILDINGS_PCT))
    lost_stock = sack.removed_share(sack.stock_total(before), sack.stock_total(after))
    expect.in_range("stock lost (percent)", lost_stock, STOCK_PCT - STOCK_TOLERANCE, STOCK_PCT + STOCK_TOLERANCE)
    lost_families = sack.removed_share(sack.families(before), sack.families(after))
    half_family = unit_points(sack.families(before)) / 2
    expect.in_range("families lost (percent)", lost_families, PEOPLE_PCT - half_family, PEOPLE_PCT + half_family)
    expect.at_most("people left", sack.population(after), sack.population(before) - 1)


def run(ctx) -> dict:
    expect = ctx.expect
    start = ctx.actions.sack_census()
    check_baseline(ctx, start)
    check_inputs_are_refused(ctx)
    check_zero_sack_changes_nothing(ctx, start)

    answer = ctx.actions.sack_village(BUILDINGS_PCT, STOCK_PCT, PEOPLE_PCT)
    after = ctx.actions.sack_census()
    expect.equals("the answer matches a new census", answer["after"]["buildings"], after["buildings"])
    check_shares(ctx, start, after)

    ctx.time.run_game_days(1, speed=3)
    later = ctx.actions.sack_census()
    expect.equals("one day later: rubble stays", sack.rubble(later), sack.rubble(after))
    expect.at_most("one day later: families do not come back", sack.families(later), sack.families(after))
    expect.equals("the game still runs", ctx.bridge.read_property("first:BP_MLGameInstance_C", "currentGameVictoryStatus"), 0)
    return ctx.result()
