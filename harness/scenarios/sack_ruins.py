"""Burn buildings and read the ruins (spec 10, spike S6, criterion R8: the state half)."""

from runlib import sack

NAME = "sack-ruins"
DESCRIPTION = "sack_buildings with fire: the buildings burn, then they are rubble, stay in the list, and their goods are gone."
COVERS = []  # R8 is NOT tagged: this scenario proves only the ruin state. The coverage tool counts a tagged, passing scenario as verified, and the rebuild cost cannot be read (criteria.json spike_note)
LIMIT_S = 150

BURN_COUNT = 2
BURN_TIMEOUT_GAME_S = 150   # a fire lasted about 50 game seconds in the probe
SPEED = 3
RUBBLE_BUILDING_TYPE = 75   # EBuildingType::Rubble


def player_region(ctx) -> str:
    return ctx.bridge.player_region_path()


def run(ctx) -> dict:
    expect, bridge = ctx.expect, ctx.bridge
    region = player_region(ctx)
    start = ctx.actions.sack_census()
    expect.at_least("start: standing buildings", sack.standing(start), BURN_COUNT + 1)
    expect.equals("start: nothing burns", sack.burning(start), 0)
    expect.equals("start: no fire flag", bridge.read_property(region, "bAnyBuildingOnFire"), False)

    record = ctx.actions.sack_buildings(count=BURN_COUNT, method="fire")
    expect.equals("action read-back", record["ok"], True)
    lit = ctx.actions.sack_census()
    expect.equals("buildings on fire right after", sack.burning(lit), BURN_COUNT)
    expect.equals("the region reports a fire", bridge.read_property(region, "bAnyBuildingOnFire"), True)

    ctx.time.set_speed(SPEED)
    ctx.run_until(lambda: sack.burning(ctx.actions.sack_census()) == 0, BURN_TIMEOUT_GAME_S, clock="game",
                  what="the fires to burn out", poll_s=2.0, stall_s=30.0, on_stall=ctx.popups)
    ctx.time.pause()

    ruined = ctx.actions.sack_census()
    expect.equals("no fire left", sack.burning(ruined), 0)
    expect.equals("burned buildings are rubble", sack.rubble(ruined), BURN_COUNT)
    expect.equals("ruins stay in the list", ruined["buildings"]["total"], start["buildings"]["total"])
    expect.equals("the region reports no fire", bridge.read_property(region, "bAnyBuildingOnFire"), False)
    expect.equals("game count of rubble buildings (type 75)", bridge.call_function(region, "getBuildingCount", [RUBBLE_BUILDING_TYPE, False]),
                  BURN_COUNT)
    burned_store_goods = sum(entry["goods"] for entry in ruined["stores"] if entry["type"] == RUBBLE_BUILDING_TYPE)
    expect.equals("a fire destroys the goods inside: ruins hold no goods", burned_store_goods, 0)
    emptied = [entry["id"] for entry in start["stores"] if entry["id"] not in {item["id"] for item in ruined["stores"]}]
    ctx.notes.append(f"stores that held goods and burned: {emptied}; stock {sack.stock_total(start)} -> {sack.stock_total(ruined)}")
    return ctx.result()
