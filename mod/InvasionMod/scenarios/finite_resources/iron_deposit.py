"""M10 iteration 01: a home deposit counts down with the production of the buildings and stops the production when empty.

A real iron mine cannot be placed without the real mouse, so the scenario lends the deposit "iron" to a good that the buildings of the
saved game already produce (the test command picks it): the same counter and the same limit lever apply to any good.
Steps: find a growing good, give the deposit a small size on that good, watch the count fall, see the production limit 0 at the end,
and see that the production of the good stops. It saves nothing. Run it on the default fixture (base).
"""

NAME = "finite-resources-iron"
DESCRIPTION = "The iron deposit counts down with production, sets the production limit to 0 when empty, and the production stops."
LIMIT_S = 300
SPEED = 3
GAME_DAY_SECONDS = 40
TEST_SIZE = 4
MIN_GROWTH = 1          # units that a good must gain in the look-around to be used (the saved game produces slowly)
STOP_DAYS = 3
MAX_LEAK = 2            # a workplace may finish the cycle it has begun


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.finite_resources_state")


def row(ctx) -> dict:
    return state(ctx)["resources"][0]


def advance_until(ctx, condition, max_days: int, what: str) -> None:
    """Let game days pass (the poll of the mod runs in real time) until the condition holds."""
    for _ in range(max_days):
        if condition():
            return
        ctx.time.run_game_seconds(GAME_DAY_SECONDS, speed=SPEED)
        ctx.run_until(lambda: True, 5, what="a poll")
    if not condition():
        raise RuntimeError(f"{what}: not reached in {max_days} game days")


def growing_good(ctx) -> int:
    before = {key: value for key, value in state(ctx)["produced"].items()}
    ctx.time.run_game_seconds(3 * GAME_DAY_SECONDS, speed=SPEED)
    ctx.run_until(lambda: state(ctx)["produced"] != before, 20, what="a new production total")
    after = state(ctx)["produced"]
    gains = {int(good): amount - before.get(good, 0) for good, amount in after.items()}
    good = max(gains, key=gains.get)
    if gains[good] < MIN_GROWTH:
        raise RuntimeError(f"no good grew by {MIN_GROWTH} in 3 game days: {gains}")
    return good


def produced_of(ctx, good: int) -> int:
    return state(ctx)["produced"].get(str(good), 0)


def run(ctx) -> dict:
    ctx.run_until(lambda: row(ctx).get("produced_total") is not None, 30, what="the first poll")
    start = row(ctx)
    ctx.check("D1 the iron deposit starts full (400) with no limit", start["size"] == 400 and start["remaining"] == 400 and start.get("limit") is None, start)

    good = growing_good(ctx)
    ctx.mod.command("InvasionMod.finite_resources_test_set", resource="iron", good=good, size=TEST_SIZE)
    advance_until(ctx, lambda: row(ctx)["mined"] > 0, 8, "the first mined units")
    middle = row(ctx)
    ctx.check("D2 production counts down the stock", middle["remaining"] < TEST_SIZE and middle["remaining"] == TEST_SIZE - middle["mined"], middle)

    advance_until(ctx, lambda: row(ctx)["empty"], 14, "the empty deposit")
    ctx.run_until(lambda: row(ctx).get("limit") == 0, 30, what="the production limit 0")
    empty = row(ctx)
    ctx.check("D3 an empty deposit sets the production limit to 0", empty["empty"] and empty.get("limit") == 0 and empty["remaining"] == 0, empty)

    stopped_at = produced_of(ctx, good)
    ctx.time.run_game_seconds(STOP_DAYS * GAME_DAY_SECONDS, speed=SPEED)
    leak = produced_of(ctx, good) - stopped_at
    ctx.check(f"D4 the production of the good stops (at most {MAX_LEAK} units in {STOP_DAYS} game days)", leak <= MAX_LEAK, [stopped_at, leak])
    ctx.mod.command("InvasionMod.finite_resources_test_clear", resource="iron")
    ctx.check("D5 the limit can be lifted again", row(ctx).get("limit") is None, row(ctx))
    ctx.metric("test_good", good)
    ctx.metric("mined_at_empty", empty["mined"])
    ctx.metric("leak_units", leak)
    return ctx.result()
