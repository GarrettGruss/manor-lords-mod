"""A worker with the storehouse role serves the manor store (spec 12, question Q7, criterion M1).

It uses the real OS mouse (action place_building), so it is hidden. Run it alone on a computer that nobody is using:
    .venv\\Scripts\\python.exe harness\\run.py --scenario manor-storage-workers
The game window must be visible.

What is base game and what is mod-defined:
- Base game: the Keep (type 57) can be placed. The worker slots and the role of a building come from its row in the DataTable buildingStats.
  A Storehouse has 3 slots and the role WarehouseWorker (job 45). `Region:assignFamily` assigns a family. A worker carries goods into a store.
- Harness shortcut: the test village cannot finish a Keep (it needs 40 builder units), so `finish_manor_site` writes `Data.constructed`
  and calls `setRegionsManor`.
- Mod-defined: `manor_worker_slot` writes the row of the Keep (slots, job, function, storage limit) in memory. The base game gives the Keep no worker.
"""

NAME = "manor-storage-workers"
DESCRIPTION = ("Place a Keep with the real mouse, finish it with the harness shortcut, give it the worker slots and the role of a Storehouse, "
               "check that no goods arrive without a worker, assign a family, and check that the worker carries goods into the Keep "
               "within a few game days, with no harness put. The assignment must hold.")
COVERS = ["M1"]
# Hidden on purpose: place_building takes over the real mouse and the keyboard focus.
HIDDEN = True
LIMIT_S = 300
KEEP = 57
STOREHOUSE_JOB = 45     # EJobType WarehouseWorker, the role of a Storehouse worker
SLOTS = 3               # the slots of a Storehouse_Lv1
RUBBLE = 15
WOOD, PLANKS, STONE = 16, 17, 27
COUNTED_GOODS = (RUBBLE, WOOD, PLANKS, STONE)   # the worker chooses the good (rubble in one run, planks in another), so the test counts all of them
GIVEN = 100
SPEED = 3
GAME_DAY_SECONDS = 40
SETTLE_DAYS = 2         # builders carry goods to the site for about 2 game days after the click, also after the shortcut finished it (real run, 3 units)
CONTROL_DAYS = 2
WORK_DAYS = 3
MIN_HAULED = 4          # the spike saw 5 to 9 units in 2 to 3 game days with one worker


def region_stock(ctx, good: int) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False])


def keep_goods(ctx) -> dict:
    return {entry["good"]: entry["amount"] for entry in keep_row(ctx)["goods"]}


def keep_row(ctx) -> dict:
    modules = ctx.actions.manor_worker_state()["modules"]
    return next(module for module in modules if module["type"] == KEEP)


def run(ctx) -> dict:
    expect = ctx.expect
    for good in (WOOD, PLANKS, STONE, RUBBLE):
        ctx.actions.give_item(good, GIVEN)

    ctx.actions.place_building(KEEP)
    ctx.actions.finish_manor_site(KEEP)
    start = keep_row(ctx)
    expect.equals("the Keep has no worker slot in the base game", start["max_slots"], 0)
    expect.equals("the Keep has no worker role in the base game", start["job"], 0)

    ctx.actions.manor_worker_slot(STOREHOUSE_JOB, SLOTS)
    slot = keep_row(ctx)
    expect.equals("the Keep has the slots of a Storehouse", slot["max_slots"], SLOTS)
    expect.equals("the Keep slots have the role WarehouseWorker (45)", slot["job"], STOREHOUSE_JOB)
    expect.equals("the Keep counts as a storage building", slot["is_storage"], True)

    ctx.time.run_game_seconds(SETTLE_DAYS * GAME_DAY_SECONDS, speed=SPEED)   # let the builders' last deliveries arrive
    goods_before = keep_goods(ctx)
    region_before = {good: region_stock(ctx, good) for good in COUNTED_GOODS}
    ctx.time.run_game_seconds(CONTROL_DAYS * GAME_DAY_SECONDS, speed=SPEED)
    expect.equals(f"control: with a slot and no worker nothing arrives in {CONTROL_DAYS} game days", keep_row(ctx)["total"], sum(goods_before.values()))

    ctx.actions.manor_assign_worker()
    assigned = keep_row(ctx)
    expect.equals("a family is assigned to the Keep", assigned["assigned"], 1)
    expect.at_least("the assigned family brings people to the Keep", assigned["workers"], 1)

    ctx.time.run_game_seconds(WORK_DAYS * GAME_DAY_SECONDS, speed=SPEED)
    goods_after = keep_goods(ctx)
    hauled = sum(goods_after.values()) - sum(goods_before.values())
    expect.at_least(f"the worker carried goods into the Keep in {WORK_DAYS} game days (units)", hauled, MIN_HAULED)
    expect.equals("the family is still assigned after the days", keep_row(ctx)["assigned"], 1)
    expect.equals("carrying moves goods, the region stock is the same", {good: region_stock(ctx, good) for good in COUNTED_GOODS}, region_before)

    if hauled > 0:  # without a risen good there is nothing to take; the assert above already failed in that case
        risen = max(goods_after, key=lambda good: goods_after[good] - goods_before.get(good, 0))
        ctx.actions.manor_take(risen, 1)
        expect.equals("a carried good can be taken out with the manor store", ctx.actions.manor_stock(risen), goods_after[risen] - 1)

    ctx.metric("manor_goods_hauled", hauled)
    return ctx.result()
