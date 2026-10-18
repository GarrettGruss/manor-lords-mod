"""M06 iteration 04, R1 and R5: after a fallback capital move, a sack hits the home region and not the capital.

The scenario makes one vassal (M07.02), lets it grow, moves the capital (M06.03), then calls sack_now. Run it with --new-game.
A lord that does not build never reaches the fortified size; then the scenario lowers the limit for the test. It saves nothing.
"""

NAME = "sack-and-terms-sack-region"
DESCRIPTION = "After the capital moved, a sack takes buildings and families from the home region only."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Claim, settle, handover (about 100 s) and up to 12 game days of growth at speed 2, then one sack."
INFLUENCE = 1000
START_SILVER = 1000
GROWTH_DAYS = 12
FORTIFIED = 8


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def region_row(ctx, name: str) -> dict:
    return next(row for row in ctx.actions.regions_state()["regions"] if row["region"] == name)


def make_vassal(ctx) -> str:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")
    return region


def wait_for_growth(ctx, region: str) -> None:
    for _ in range(GROWTH_DAYS):
        if (region_row(ctx, region).get("buildings") or 0) >= FORTIFIED:
            return
        ctx.time.run_game_days(1, speed=SPEED)
    ctx.log.info("the vassal did not grow; the fortified limit is lowered for this test")
    ctx.mod.command("InvasionMod.fallback_set_min_buildings", value=1)


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    home = vassals(ctx)["home_region"]
    ctx.actions.set_silver(START_SILVER)
    ctx.mod.command("InvasionMod.sack_set_fatal", enabled=False)
    capital = make_vassal(ctx)
    wait_for_growth(ctx, capital)
    ctx.mod.command("InvasionMod.fallback_move", slot=1)
    ctx.check("the capital is a player region", "MyPawn" in str(region_row(ctx, capital).get("owner")), region_row(ctx, capital))

    home_before, capital_before = region_row(ctx, home), region_row(ctx, capital)
    result = ctx.mod.command("InvasionMod.sack_now", difficulty=3)
    home_after, capital_after = region_row(ctx, home), region_row(ctx, capital)
    ctx.check("R1 the sack names the home region", result["region"] == home, [result["region"], home])
    ctx.check("R1 the home region lost families", (home_after["families"] or 0) < (home_before["families"] or 0), [home_before["families"], home_after["families"]])
    ctx.check("R1 the capital lost no family", (capital_after["families"] or 0) == (capital_before["families"] or 0), [capital_before["families"], capital_after["families"]])
    ctx.metric("home_families_lost", (home_before["families"] or 0) - (home_after["families"] or 0))
    ctx.time.run_game_days(2, speed=SPEED)
    ctx.check("R5 the game runs 2 days after the sack", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
