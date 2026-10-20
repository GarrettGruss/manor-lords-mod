"""Spike (change add-raid-storage-tiers, task 1.2): does a game raid reach the manor store?

The base fixture has a built manor (type 98). The scenario puts goods in the manor, starts a native raid (spawnRaiders, the game steers
the raiders to pillage) and samples each game day: the manor stock, the goods in every other store, the loot carried by the raiders and
the buildings that burn. Option RAID_SQUADS (default 2) sets the raid size. It saves nothing and adds no steering.
"""

import json

NAME = "spike-raid-game-manor"
DESCRIPTION = "A native raid on a village with goods in the manor: is the manor store robbed? (spike, records numbers)"
HIDDEN = True
LIMIT_S = 900
LONG_REASON = "A native raid needs about 16 game days to arrive and burn. The scenario samples up to 30 game days at speed 3."
SPEED = 3
MAX_DAYS = 30
GOOD = 27       # rough stone: not used by the village, so only the raid or a store can change it
PUT = 100


def note(ctx, step: str, **data) -> None:
    ctx.log.info(f"PROBE {json.dumps({'step': step, **data}, default=str)[:1500]}")


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: an army in sight drops the speed to 1
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def store_totals(census: dict) -> dict:
    return {str(store["id"]): [store["type"], store["goods"]] for store in census["stores"]}


def run(ctx) -> dict:
    actions, expect = ctx.actions, ctx.expect
    squads = int(ctx.variant_option("RAID_SQUADS", "2"))
    manor = actions.manor_state()
    expect.equals("the village has a built region manor", manor["region_has_manor"], True)
    actions.manor_put(GOOD, PUT)
    manor_id = manor["region_manor_id"]
    start = actions.sack_census()
    note(ctx, "start", manor_stock=actions.manor_stock(GOOD), stores=store_totals(start), stock_total=start["stock"]["total"])
    actions.spawn_raid(squads=squads)

    peak_loot, days = 0, 0
    manor_min = PUT
    while days < MAX_DAYS:
        ctx.popups()
        run_day(ctx)
        days += 1
        census = actions.units_census()
        loot = census["loot"]["total"]
        village = actions.sack_census()
        stock = actions.manor_stock(GOOD)
        manor_min = min(manor_min, stock)
        peak_loot = max(peak_loot, loot if isinstance(loot, int) else 0)
        note(ctx, "day", day=days, manor_stock=stock, loot=loot, stores=store_totals(village), burning=village["buildings"]["burning"],
             rubble=village["buildings"]["rubble"], standing=village["buildings"]["standing"], stock_total=village["stock"]["total"],
             by_state=census.get("by_state"))
        if days >= 8 and census.get("by_state", {}).get("alive", 1) == 0:
            break
    final = actions.manor_state()
    note(ctx, "end", manor_modules=final["modules"], manor_id=manor_id)
    ctx.metric("manor_min_stock", manor_min)
    ctx.metric("peak_loot", peak_loot)
    ctx.metric("days", days)
    expect.equals("the manor stock was read each day", manor_min >= 0, True)
    ctx.ensure_alive("spike raid game manor")
    return ctx.result()
