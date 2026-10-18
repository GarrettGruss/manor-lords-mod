"""M08 iteration 02, P1 to P6: a raid on a vassal region changes the loyalty of the vassal.

The scenario makes one vassal (M07.02). It feeds the raid results through the test command `tribute_test_raid_result`,
because a raid does not target a vassal region yet. It saves nothing.
"""

NAME = "tribute-protection-and-loyalty"
DESCRIPTION = "An undefended raid on a vassal region lowers loyalty, a defended one raises it; low loyalty makes the vassal submit."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), one season jump, 3 game days at speed 2."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def loyalty(ctx) -> int:
    return vassals(ctx)["vassals"][0]["loyalty"]


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def make_vassal(ctx) -> str:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")
    return region


def raid_result(ctx, region: str, state: str, leave_reason: str | None = None) -> dict:
    args = {"region": region, "state": state}
    if leave_reason:
        args["leave_reason"] = leave_reason
    return ctx.mod.command("InvasionMod.tribute_test_raid_result", **args)


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    home = vassals(ctx)["home_region"]
    region = make_vassal(ctx)
    start = loyalty(ctx)

    raid_result(ctx, region, "left", "loot")
    ctx.check("P1 an undefended raid lowers loyalty by 15", loyalty(ctx) == start - 15, [start, loyalty(ctx)])
    before = loyalty(ctx)
    raid_result(ctx, region, "destroyed")
    ctx.check("P2 a defended raid raises loyalty by 5", loyalty(ctx) == before + 5, [before, loyalty(ctx)])
    before = loyalty(ctx)
    answer = raid_result(ctx, home, "left", "loot")
    ctx.check("P3 a raid on the home region changes no loyalty", answer["event"] is False and loyalty(ctx) == before, answer)

    for _ in range(4):
        raid_result(ctx, region, "left", "time")
    ctx.check("P5 loyalty is clamped at 0", loyalty(ctx) == 0, loyalty(ctx))
    ctx.check("P4 the counts are kept", tribute(ctx)["protection_failed"] == 5 and tribute(ctx)["protection_defended"] == 1, tribute(ctx))

    state = tribute(ctx)
    ctx.actions.set_season(SEASONS[(state["last_season"] + 1) % 4])
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["submitted"], 30, what="the submission")
    ctx.check("P4 the vassal at loyalty 0 submits at the season change", vassals(ctx)["submissions"] == 1, vassals(ctx))
    ctx.time.run_game_days(3, speed=SPEED)
    ctx.check("P6 the game runs 3 days after the submission", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
