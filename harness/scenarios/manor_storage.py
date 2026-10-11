"""Goods are kept in the manor: put in, read back, take out, read after game days (spec 12, criterion M1).

It uses the real OS mouse (action place_building), so it is hidden. Run it alone on a computer that nobody is using:
    .venv\\Scripts\\python.exe harness\\run.py --scenario manor-storage
The game window must be visible.

What is base game and what is mod-defined:
- Base game: the Keep (type 57) can be placed, the building has an `Inventory`, and goods added to it count in the region stock.
- Harness shortcut: the test village cannot finish a Keep (it needs 40 builder units), so `finish_manor_site` writes `Data.constructed`
  and calls `setRegionsManor`.
- Mod-defined: the put and take commands and the capacity of 200 units. The base game does not use the Keep as a store.
"""

NAME = "manor-storage"
DESCRIPTION = ("Place a Keep (the manor) with the real mouse, finish it with the harness shortcut, then put goods in, read the stock back "
               "from the module and the region, take some out, and read again after two game days. A put over the capacity and a take of "
               "more than it holds are refused. The store is mod-defined on top of the building inventory.")
COVERS = ["M1"]
# Hidden on purpose: place_building takes over the real mouse and the keyboard focus.
HIDDEN = True
LIMIT_S = 240
KEEP = 57
ROUGH_STONE = 27          # not a good that a Keep needs, so the builders do not move it
WOOD, PLANKS, RUBBLE = 16, 17, 15   # the Keep costs 10 wood, 15 planks and 10 rubble (read from the build preview)
GIVEN = 100
PUT = 20
TAKE = 5
TOO_MUCH = 500
SPEED = 3
GAME_DAY_SECONDS = 40
DAYS = 2


def region_stock(ctx, good: int) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False])


def refused(ctx, name: str, call) -> None:
    from runlib.commands import CommandRefused
    try:
        call()
    except CommandRefused as error:
        ctx.expect.record(name, True, error.reason[:60], "refused")
        return
    ctx.expect.record(name, False, "accepted", "refused")


def run(ctx) -> dict:
    expect = ctx.expect
    for good in (WOOD, PLANKS, RUBBLE, ROUGH_STONE):
        ctx.actions.give_item(good, GIVEN)

    ctx.actions.place_building(KEEP)
    sites = [module for module in ctx.actions.manor_state()["modules"] if module["type"] == KEEP]
    expect.equals("the Keep site stands", len(sites), 1)
    expect.equals("the Keep site is not built yet", sites[0]["built"] if sites else None, False)

    ctx.actions.finish_manor_site(KEEP)
    state = ctx.actions.manor_state()
    expect.equals("the region has a manor", state["region_has_manor"], True)
    expect.equals("one manor module is built", [module["built"] for module in state["modules"]], [True])

    stone_before = region_stock(ctx, ROUGH_STONE)
    expect.equals("the manor holds no stone at the start", ctx.actions.manor_stock(ROUGH_STONE), 0)

    ctx.actions.manor_put(ROUGH_STONE, PUT)
    expect.equals("put: the manor holds the stone", ctx.actions.manor_stock(ROUGH_STONE), PUT)
    expect.equals("put: the region stock rose by the same amount", region_stock(ctx, ROUGH_STONE), stone_before + PUT)

    ctx.actions.manor_take(ROUGH_STONE, TAKE)
    kept = PUT - TAKE
    expect.equals("take: the manor holds the rest", ctx.actions.manor_stock(ROUGH_STONE), kept)
    expect.equals("take: the region stock fell by the same amount", region_stock(ctx, ROUGH_STONE), stone_before + kept)

    refused(ctx, "a put over the capacity is refused", lambda: ctx.actions.manor_put(ROUGH_STONE, TOO_MUCH))
    refused(ctx, "a take of more than the manor holds is refused", lambda: ctx.actions.manor_take(ROUGH_STONE, kept + 1))
    expect.equals("the refusals changed nothing", ctx.actions.manor_stock(ROUGH_STONE), kept)

    ctx.time.run_game_seconds(DAYS * GAME_DAY_SECONDS, speed=SPEED)
    expect.equals(f"after {DAYS} game days the manor still holds the stone", ctx.actions.manor_stock(ROUGH_STONE), kept)
    expect.equals("after the days the region stock is the same", region_stock(ctx, ROUGH_STONE), stone_before + kept)

    ctx.metric("manor_stone_kept", kept)
    return ctx.result()
