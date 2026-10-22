"""Change add-raid-storage-tiers: the mod steal never takes goods from the manor store (tier 2), also with goods in tier 1 stores.

Option (run.py --env): RAID=baron (default) or RAID=game. INVASION_DIFFICULTY (1 to 3, default 1).
The scenario puts 100 rough stone (a good the village does not use) in the manor. RAID=baron forces a small baron (lord) raid and checks
that the manor stone is unchanged and that the mod took goods from tier 1. RAID=game starts a game raid (spawnRaiders) and checks that
the mod tracker has no raid and no steal; the manor stone is only recorded, because the game may rob it (owner decision 2026-10-20).
It saves nothing.
"""

NAME = "raid-behavior-storage-tiers"
DESCRIPTION = "The mod steal of a baron raid leaves the manor store alone; a game raid has no mod steal."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "A raid needs up to 30 game days. At speed 3 this takes up to 300 s plus the start."
DAY_LIMIT = 30
GOOD = 27  # rough stone: the village does not use it
PUT = 100


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    actions = ctx.actions
    mode = ctx.variant_option("RAID", "baron")
    ctx.check("the village has a built region manor", actions.manor_state()["region_has_manor"] is True)
    actions.manor_put(GOOD, PUT)
    ctx.check("the manor holds the stone", actions.manor_stock(GOOD) == PUT, actions.manor_stock(GOOD))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=int(ctx.variant_option("INVASION_DIFFICULTY", "1")))
    days, manor_min = 0, PUT
    if mode == "game":
        actions.spawn_raid(squads=2)
    else:
        ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
        ctx.mod.command("InvasionMod.invasion_set_size", size="small")
        ctx.mod.command("InvasionMod.invasion_force_next")
        ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    while days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        manor_min = min(manor_min, actions.manor_stock(GOOD))
        if mode == "baron" and tracker(ctx).get("state") != "active":
            break
        if mode == "game" and days >= 8 and actions.units_census().get("by_state", {}).get("alive", 1) == 0:
            break
    raid = tracker(ctx)
    ctx.metric("days", days)
    ctx.metric("manor_min_stock", manor_min)
    ctx.metric("stolen", raid.get("stolen", 0))
    if mode == "game":
        ctx.check("a game raid has no tracker record, so no mod steal", raid == {}, raid)
    else:
        ctx.check("the manor stone is unchanged at every day", manor_min == PUT and actions.manor_stock(GOOD) == PUT, manor_min)
        ctx.check("the mod took goods from tier 1 stores", raid.get("stolen", 0) > 0, raid)
    return ctx.result()
