"""Test scenario. It fails an assertion on purpose, to test the verdict fail."""

NAME = "selftest-fail"
LIMIT_S = 30
HIDDEN = True


def run(ctx) -> dict:
    clock = ctx.read_clock(2.0)
    # The game is paused after boot, so this must be false.
    ctx.check("clock moves while the game is paused (must fail)", not clock["paused"], clock["change"], [0.001, 100])
    return ctx.result()
