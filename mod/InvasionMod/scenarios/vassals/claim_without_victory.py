"""M07 iteration 01, V1 to V6: the goal is Endless, a claim does not end the game, the claim is a vassal slot.

Run it with --new-game for V3 (the Growth default of a new game ends the game on a claim without the mod).
On a fixture the claim still works, and V3 only shows that the status stays 0. It saves nothing.
"""

NAME = "vassals-claim-without-victory"
DESCRIPTION = "The mod holds goals = Endless; a claimed region is registered as a vassal slot; no victory."
LIMIT_S = 400
SPEED = 2
LONG_REASON = "10 game days at speed 2 after the claim, plus the wait for the claim and the goal checks."
INFLUENCE = 1000


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def check_goal_is_held(ctx) -> None:
    ctx.run_until(lambda: state(ctx)["goal"] == 2, 15, what="the goal Endless")
    ctx.check("V1 the goal is Endless (2)", state(ctx)["goal"] == 2, state(ctx))
    writes = state(ctx)["goal_writes"]
    ctx.mod.command("InvasionMod.vassals_set_goal", goal=3)
    ctx.run_until(lambda: state(ctx)["goal_writes"] > writes, 15, what="the mod to write the goal back")
    after = state(ctx)
    game_goal = ctx.actions.game_setup_state()
    ctx.check("V2 the mod wrote the goal back to Endless", after["goal"] == 2 and game_goal["goals"] == 2, [after["goal"], game_goal])


def check_claim(ctx) -> str:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    answer = ctx.mod.command("InvasionMod.vassals_claim", region=region)
    ctx.time.run_game_seconds(6, speed=1)
    after = state(ctx)
    setup = ctx.actions.game_setup_state()
    row = next(r for r in ctx.actions.regions_state()["regions"] if r["region"] == region)
    ctx.check("V3 the claim did not end the game (victory status 0)", setup["victory_status"] == 0, setup)
    ctx.check("V3 the player owns the region", bool(row.get("owner")), row)
    vassal = after["vassals"][0] if after["vassals"] else {}
    ctx.check("V4 the claim is slot 1 with the start loyalty", after["count"] == 1 and vassal.get("region") == region
              and vassal.get("loyalty") == 50 and answer["claimed_slot"] == 1, after)
    return region


def check_loyalty_clamp(ctx) -> None:
    high = ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=150)["vassals"][0]["loyalty"]
    low = ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=-5)["vassals"][0]["loyalty"]
    ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=50)
    ctx.check("V5 loyalty is clamped to 0..100", (high, low) == (100, 0), [high, low])


def run(ctx) -> dict:
    ctx.run_until(lambda: state(ctx).get("day") is not None, 30, what="the mod state")
    check_goal_is_held(ctx)
    check_claim(ctx)
    check_loyalty_clamp(ctx)
    before = state(ctx)["day"]
    ctx.time.run_game_days(10, speed=SPEED)
    final = state(ctx)
    ctx.check("V6 the game runs 10 days after the claim", final["day"] >= before + 10 and final["goal"] == 2, [before, final["day"]])
    ctx.metric("goal_writes", final["goal_writes"])
    ctx.metric("vassals", final["count"])
    return ctx.result()
