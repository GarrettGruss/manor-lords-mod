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
               "check that no goods arrive without a worker, assign a family, and check that the worker carries rubble into the Keep "
               "within a few game days, with no harness put. The assignment must hold.")
COVERS = ["M1"]
# Hidden on purpose: place_building takes over the real mouse and the keyboard focus.
HIDDEN = True
LIMIT_S = 300
KEEP = 57
STOREHOUSE_JOB = 45     # EJobType WarehouseWorker, the role of a Storehouse worker
SLOTS = 3               # the slots of a Storehouse_Lv1
RUBBLE = 15             # a good that the base game workers carry into stores (wood, planks and stone stayed in the crate in the spike)
WOOD, PLANKS, STONE = 16, 17, 27
GIVEN = 100
SPEED = 3
GAME_DAY_SECONDS = 40
CONTROL_DAYS = 2
WORK_DAYS = 3
MIN_HAULED = 3          # the spike saw about 5 units per 2 game days with one worker


def region_stock(ctx, good: int) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False])


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

    rubble_before = ctx.actions.manor_stock(RUBBLE)
    region_before = region_stock(ctx, RUBBLE)
    ctx.time.run_game_seconds(CONTROL_DAYS * GAME_DAY_SECONDS, speed=SPEED)
    expect.equals(f"control: with a slot and no worker nothing arrives in {CONTROL_DAYS} game days", ctx.actions.manor_stock(RUBBLE), rubble_before)

    ctx.actions.manor_assign_worker()
    assigned = keep_row(ctx)
    expect.equals("a family is assigned to the Keep", assigned["assigned"], 1)
    expect.at_least("the assigned family brings people to the Keep", assigned["workers"], 1)

    ctx.time.run_game_seconds(WORK_DAYS * GAME_DAY_SECONDS, speed=SPEED)
    hauled = ctx.actions.manor_stock(RUBBLE) - rubble_before
    expect.at_least(f"the worker carried rubble into the Keep in {WORK_DAYS} game days (units)", hauled, MIN_HAULED)
    expect.equals("the family is still assigned after the days", keep_row(ctx)["assigned"], 1)
    expect.equals("carrying moves goods, the region stock is the same", region_stock(ctx, RUBBLE), region_before)

    if hauled > 0:  # a zero take is refused; the assert above already failed in that case
        ctx.actions.manor_take(RUBBLE, hauled)
        expect.equals("the carried goods can be taken out with the manor store", ctx.actions.manor_stock(RUBBLE), rubble_before)

    ctx.metric("manor_rubble_hauled", hauled)
    return ctx.result()
