"""Change update-tech-tree-yearly-picks: Disarm the Peasantry moves home weapons to the storehouse.

Fixture: the default `base-corpse-pit` (it has homes and a storehouse). The fixture homes already hold spears and shields (militia gear), and the game moves some of them by itself, so the checks use ranges and
the tick counters of the state command. The scenario puts 3 spears (133) and 2 large shields (271) into the first home with a test command,
checks that no tick runs without the law, enacts the law, runs game days until the homes hold none, and checks that the store gained what the
ticks moved. After the repeal, no tick runs.
The rebellion that the empty homes block belongs to the change update-banditry-rebellion-raid and is not checked here.
It saves nothing.
"""

NAME = "tech-tree-disarm"
DESCRIPTION = "With Disarm the Peasantry in force, the weapons of the homes go to the storehouse at the next tick; after the repeal they stay."
LIMIT_S = 900
SPEED = 3
LONG_REASON = "The home tick runs once for each game day; the check needs a few game days."
DAY_LIMIT = 4
SPEAR, LARGE_SHIELD = 133, 271
PREFIX = "InvasionMod."


def goods(ctx, good: int) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_test_home_goods", good=good)


def state(ctx) -> dict:
    return ctx.mod.command(PREFIX + "tech_tree_state")


def run_day(ctx) -> None:
    ctx.popups()
    ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    ctx.run_until(lambda: ctx.mod.command(PREFIX + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    ctx.check("D1 Armory Census is unlocked", "armory_census" in ctx.mod.command(PREFIX + "tech_tree_unlock", node="armory_census")["unlocked"])
    base = {good: goods(ctx, good) for good in (SPEAR, LARGE_SHIELD)}
    ctx.check("D2 the fixture has homes and a store", base[SPEAR]["home_count"] >= 1 and base[SPEAR]["store"] is not None, base)
    ctx.mod.command(PREFIX + "tech_tree_test_fill_home", good=SPEAR, amount=3)
    ctx.mod.command(PREFIX + "tech_tree_test_fill_home", good=LARGE_SHIELD, amount=2)
    filled = {good: goods(ctx, good) for good in (SPEAR, LARGE_SHIELD)}
    ctx.check("D3 the home holds the new weapons", filled[SPEAR]["homes"] == base[SPEAR]["homes"] + 3 and filled[LARGE_SHIELD]["homes"] == base[LARGE_SHIELD]["homes"] + 2, filled)

    run_day(ctx)
    ctx.check("D4 no tick runs and the store gains nothing without the law",
              state(ctx)["disarm_ticks"] == 0 and goods(ctx, SPEAR)["store"] == base[SPEAR]["store"] and goods(ctx, SPEAR)["homes"] > 0,
              [state(ctx)["disarm_ticks"], goods(ctx, SPEAR)])

    enacted = ctx.mod.command(PREFIX + "tech_tree_enact_law", law="disarm_the_peasantry")
    ctx.check("D5 the law is in force", "disarm_the_peasantry" in enacted["laws"], enacted)
    for _ in range(DAY_LIMIT):
        if goods(ctx, SPEAR)["homes"] == 0 and goods(ctx, LARGE_SHIELD)["homes"] == 0:
            break
        run_day(ctx)
    after = {good: goods(ctx, good) for good in (SPEAR, LARGE_SHIELD)}
    ctx.metric("homes_spears_after", after[SPEAR]["homes"])
    ctx.check("D6 the homes hold no spear and no large shield", after[SPEAR]["homes"] == 0 and after[LARGE_SHIELD]["homes"] == 0, after)
    gain = sum(after[good]["store"] - filled[good]["store"] for good in (SPEAR, LARGE_SHIELD))
    moved, stored = state(ctx)["disarm_moved"], state(ctx)["disarm_stored"]
    ctx.metric("store_gain", gain)
    ctx.metric("moved_by_ticks", moved)
    # The tick reads the store before and after its add, so `stored` is exact at the tick. The game moves some weapons out of the
    # store later (militia gear), so the later reading is only a range.
    ctx.check("D7 the store kept every weapon that the ticks moved", moved >= 5 and stored == moved, [moved, stored])
    ctx.check("D7b the store still holds most of them at the end", gain >= moved * 0.7, [gain, moved])
    ctx.check("D8 the law lowers approval by 3", ctx.mod.command(PREFIX + "tech_tree_state")["totals"]["approval_bonus"] == -3)

    ctx.mod.command(PREFIX + "tech_tree_repeal_law", law="disarm_the_peasantry")
    ticks = state(ctx)["disarm_ticks"]
    ctx.mod.command(PREFIX + "tech_tree_test_fill_home", good=SPEAR, amount=2)
    run_day(ctx)
    run_day(ctx)
    ctx.check("D9 after the repeal no tick runs", state(ctx)["disarm_ticks"] == ticks, [ticks, state(ctx)["disarm_ticks"]])
    return ctx.result()
