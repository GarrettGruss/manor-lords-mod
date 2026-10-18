"""M06 iteration 03, F1 to F6: the player pays to make a fortified vassal the fallback capital.

The scenario makes one vassal (M07.02), waits for it to grow, then calls fallback_move. Run it with --new-game.
A lord that does not build (stalled, M07.02) never reaches the fortified size; then the scenario lowers the limit for the test
and says so in the log. Option (run.py --env): FALLBACK_TAKE_BACK (clear or write, default write). It saves nothing.
"""

NAME = "sack-and-terms-fallback-capital"
DESCRIPTION = "Pay silver: a vassal region returns to the player, grain moves, settlers arrive, the slot is the capital."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Claim, settle, handover (about 100 s) and up to 12 game days of growth at speed 2, then 5 more days."
INFLUENCE = 1000
START_SILVER = 1000
GROWTH_DAYS = 12
FORTIFIED = 8


def fallback(ctx) -> dict:
    return ctx.mod.command("InvasionMod.fallback_state")


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
    ctx.actions.set_silver(START_SILVER)
    ctx.mod.command("InvasionMod.fallback_set_take_back", mode=ctx.variant_option("FALLBACK_TAKE_BACK", "write"))
    region = make_vassal(ctx)
    wait_for_growth(ctx, region)

    refused_early = False
    try:
        ctx.mod.command("InvasionMod.fallback_move", slot=2)
    except Exception as error:  # ModCommandError: the mod refuses an empty slot
        refused_early = "no handed-over vassal" in str(error)
    ctx.check("F5 an empty slot is refused", refused_early)

    families_before = region_row(ctx, region).get("families") or 0
    silver_before = fallback(ctx)["silver"]
    answer = ctx.mod.command("InvasionMod.fallback_move", slot=1)
    last = answer["last"]
    owner = region_row(ctx, region)
    ctx.check("F1 the region is the player region again", "MyPawn" in str(owner.get("owner")), owner)
    ctx.check("F2 the silver was paid (150 x difficulty)", silver_before - answer["silver"] == last["cost"] and last["cost"] == 150 * 1, [silver_before, answer])
    ctx.check("F3 grain left the home stores and arrived", last["grain_taken"] > 0 and last["grain_deposited"] == last["grain_taken"], last)
    ctx.check("F4 settlers arrived (5 families a call)", (owner.get("families") or 0) - families_before == 5 * last["settle_calls"] and last["settle_calls"] == 1, [families_before, owner])
    state = vassals(ctx)
    ctx.check("F4 the slot is the capital and has no lord", state["vassals"][0]["capital"] and state["vassals"][0]["lord"] == "none", state)
    try:
        ctx.mod.command("InvasionMod.fallback_move", slot=1)
        again = True
    except Exception:  # ModCommandError: a second capital is refused
        again = False
    ctx.check("F5 a second capital is refused", not again)

    ctx.time.run_game_days(5, speed=SPEED)
    later = vassals(ctx)
    ctx.check("F6 the capital stays the player region (no new handover) after 5 days", later["vassals"][0]["capital"] and later["vassals"][0]["lord"] == "none"
              and "MyPawn" in str(region_row(ctx, region).get("owner")), later)
    ctx.metric("capital_buildings", region_row(ctx, region).get("buildings") or 0)
    return ctx.result()
