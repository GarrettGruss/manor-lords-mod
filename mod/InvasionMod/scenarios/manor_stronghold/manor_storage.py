"""M13 iteration 01: the manor holds more goods after a tech tree upgrade.

Run it on the fixture manor-bailey (a built manor house, no mouse needed):
    uv run python harness\run.py --scenario manor-stronghold-storage --fixture manor-bailey --slot auto
Steps: read the capacity (200), fill the manor to the limit, see that one more unit is refused, unlock Fair Courts and Amnesty
(Prosperity), see the capacity 400, put 150 more, take some out, wait 2 game days. It saves nothing.
"""

NAME = "manor-stronghold-storage"
DESCRIPTION = "A tech tree node raises the capacity of the manor store from 200 to 400 units; put and take follow the region stock."
LIMIT_S = 300
SPEED = 3
GAME_DAY_SECONDS = 40
STONE = 27
BASE_CAPACITY = 200
UPGRADED_CAPACITY = 400


def manor(ctx) -> dict:
    return ctx.mod.command("InvasionMod.manor_state")


def module(ctx) -> dict:
    built = [row for row in manor(ctx)["modules"] if row["built"]]
    ctx.check("S0 the fixture has a built manor module", len(built) >= 1, manor(ctx))
    return built[0]


def region_stock(ctx, good: int) -> int:
    return ctx.bridge.call_function(ctx.bridge.player_region_path(), "getStockOfGood", [good, False, False])


def unlock_storage_upgrade(ctx) -> None:
    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="prosperity")
    ctx.actions.set_settlement_level(2)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.tech_tree_state")["slots"] >= 2, 20, what="2 node slots")
    for node in ("fair_courts", "amnesty"):
        ctx.mod.command("InvasionMod.tech_tree_unlock", node=node)
    ctx.run_until(lambda: manor(ctx)["capacity"] == UPGRADED_CAPACITY, 20, what="the capacity 400")


def run(ctx) -> dict:
    ctx.actions.give_item(STONE, 600)
    start = manor(ctx)
    ctx.check("S1 the base capacity is 200", start["capacity"] == BASE_CAPACITY, start)
    held = module(ctx)["total"]
    room = BASE_CAPACITY - held
    ctx.mod.command("InvasionMod.manor_put", good=STONE, amount=room)
    reason = ctx.mod.refusal("InvasionMod.manor_put", good=STONE, amount=1)
    ctx.check("S1 one more unit is refused at the base capacity", reason is not None and "200" in reason, reason)

    unlock_storage_upgrade(ctx)
    ctx.check("S2 the capacity is 400 after the node", manor(ctx)["capacity"] == UPGRADED_CAPACITY, manor(ctx))
    stock_before = region_stock(ctx, STONE)
    ctx.mod.command("InvasionMod.manor_put", good=STONE, amount=150)
    ctx.check("S2 150 more units fit", module(ctx)["total"] == BASE_CAPACITY + 150, module(ctx))
    ctx.check("S3 the region stock rose by 150", region_stock(ctx, STONE) - stock_before == 150, region_stock(ctx, STONE))
    over = ctx.mod.refusal("InvasionMod.manor_put", good=STONE, amount=UPGRADED_CAPACITY)
    ctx.check("S2 a put over 400 is refused", over is not None, over)

    ctx.mod.command("InvasionMod.manor_take", good=STONE, amount=50)
    kept = module(ctx)["total"]
    ctx.check("S3 a take of 50 lowers the manor total", kept == BASE_CAPACITY + 100, kept)
    ctx.time.run_game_seconds(2 * GAME_DAY_SECONDS, speed=SPEED)
    ctx.check("S4 the goods stay after 2 game days", module(ctx)["total"] == kept, module(ctx))
    ctx.metric("capacity_after", manor(ctx)["capacity"])
    ctx.metric("manor_total", kept)
    return ctx.result()
