"""Test scenario. It asks for an action that is not possible, to test the clear failure (spec 07)."""

NAME = "selftest-action"
LIMIT_S = 30
HIDDEN = True


def run(ctx) -> dict:
    ctx.actions.save_state("selftest")  # must raise ActionNotPossible. The runner turns it into the verdict fail.
    return ctx.result()
