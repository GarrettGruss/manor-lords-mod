"""M13 iteration 02: a tech tree node raises the retinue limit of the manor from 12 to 24.

Run it on the fixture manor-bailey (a built manor house, no mouse needed):
    uv run python harness\run.py --scenario manor-stronghold-retinue --fixture manor-bailey --slot auto
Steps: hire retinue men up to the base limit (12), see that hiring stops, unlock Militia Rights (Prosperity), see the limit 24,
hire more men and count the men bound to the manor (the native hire still stops at 12: see the iteration file). It saves nothing.
"""

NAME = "manor-stronghold-retinue"
DESCRIPTION = "A tech tree node raises the retinue limit and the hire gate of the manor from 12 to 24; the native hire stays at 12 (known)."
LIMIT_S = 300
SPEED = 2
BASE_LIMIT = 12
UPGRADED_LIMIT = 24
SILVER = 100000
MAX_HIRES = 40


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.retinue_state")


def hire_until_stuck(ctx) -> dict:
    current = state(ctx)
    stuck = 0
    for _ in range(MAX_HIRES):
        before = current["bound"]
        current = ctx.mod.command("InvasionMod.retinue_hire")
        ctx.time.run_game_seconds(1, speed=SPEED)
        current = state(ctx)
        stuck = stuck + 1 if current["bound"] == before else 0
        if stuck >= 3:
            break
    return current


def unlock_militia_rights(ctx) -> None:
    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="prosperity")
    ctx.actions.set_settlement_level(3)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.tech_tree_state")["slots"] >= 3, 20, what="3 node slots")
    for node in ("fair_courts", "amnesty", "militia_rights"):
        ctx.mod.command("InvasionMod.tech_tree_unlock", node=node)
    ctx.run_until(lambda: state(ctx)["bonus"] == UPGRADED_LIMIT - BASE_LIMIT, 20, what="the retinue bonus 12")


def run(ctx) -> dict:
    ctx.actions.set_silver(SILVER)
    start = state(ctx)
    ctx.check("R1 the base limit is 12", start["limit"] == BASE_LIMIT and start["bonus"] == 0, start)
    full = hire_until_stuck(ctx)
    ctx.check("R1 hiring stops at the base limit", full["bound"] == BASE_LIMIT and full["can_hire"] is False, full)

    unlock_militia_rights(ctx)
    upgraded = state(ctx)
    ctx.check("R2 the limit is 24 after the node", upgraded["limit"] == UPGRADED_LIMIT, upgraded)
    ctx.check("R2 the hire gate is open below the new limit", upgraded["can_hire"] is True, upgraded)
    after = hire_until_stuck(ctx)
    # Finding (run 20261018-094006-4a4f): the native hire refuses above the native limit, also when the script limit and the gate say 24.
    # The check below records the fact. If a game update lets the hires pass, this check fails and the design can use it.
    ctx.check("R3 the native hire stays at the native limit (known)", after["bound"] == BASE_LIMIT, after)
    ctx.metric("bound_base", full["bound"])
    ctx.metric("bound_upgraded", after["bound"])
    return ctx.result()
