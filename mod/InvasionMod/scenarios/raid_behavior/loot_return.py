"""M03 iteration 01: the loot of killed raiders goes back to the nearest store.

Loot is written on every bandit unit, so on the 18 raiders (set_unit_loot). The tracker must see it. The raiders are then killed.
The stock of the village must rise by the loot, the tracker must count 18 deaths and the returned goods. It saves nothing.
"""

from runlib import sack
from runlib.units import side_count

NAME = "raid-behavior-loot-return"
LIMIT_S = 240
LOOT_EACH = 4
RAIDERS = 18  # the raiders of one squad. The scenario cannot pick them out, so it loads and kills every bandit unit.



def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    bandits = side_count(ctx.actions.units_census(), "bandit")
    ctx.actions.set_unit_loot(side="bandit", count=bandits, amount=LOOT_EACH)
    ctx.run_until(lambda: tracker(ctx)["loot"] >= RAIDERS * LOOT_EACH, 30, what="the tracker to see the loot")
    stock_before = sack.stock_total(ctx.actions.sack_census())
    killed = ctx.actions.kill_units(side="bandit", count=bandits, with_loot=True)
    ctx.run_until(lambda: tracker(ctx)["deaths"] >= RAIDERS, 30, what="the tracker to see the deaths")
    raid = tracker(ctx)
    stock_after = sack.stock_total(ctx.actions.sack_census())
    ctx.check("the tracker counts the deaths", raid["deaths"] == RAIDERS, raid["deaths"])
    ctx.check("the returned goods equal the carried loot", raid["returned"] == RAIDERS * LOOT_EACH, raid["returned"])
    ctx.check("nothing was lost", raid["lost"] == 0, raid["lost"])
    ctx.check("the village stock rose by the returned goods", stock_after - stock_before == RAIDERS * LOOT_EACH, [stock_before, stock_after])
    ctx.check("no raider is alive", raid["living"] == 0 and raid["state"] == "destroyed", [raid["living"], raid["state"]])
    return ctx.result()
