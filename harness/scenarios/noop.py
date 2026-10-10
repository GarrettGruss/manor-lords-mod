"""Placeholder. It proves that the game is alive and paused, and that the bridge works."""

NAME = "noop"
LIMIT_S = 30


def run(ctx) -> dict:
    clock = ctx.read_clock()
    ctx.check("clock is stopped", clock["paused"], clock["change"], [0, 0.001])
    result = ctx.result()
    result["clock"] = clock
    return result
