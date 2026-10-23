"""M06 iteration 04, R1 and R5: a manual sack hits the home region and never a vassal region.

The scenario makes one vassal (M07.02), lets it settle, then calls sack_now. The vassal region belongs to its lord, so it must lose nothing.
Run it with --new-game. It saves nothing.
"""

NAME = "sack-and-terms-sack-region"
DESCRIPTION = "A manual sack takes buildings and families from the home region only, not from a vassal region."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then one sack and 2 game days at speed 2."
INFLUENCE = 1000


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


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    home = vassals(ctx)["home_region"]
    ctx.mod.command("InvasionMod.sack_set_fatal", enabled=False)
    vassal = make_vassal(ctx)

    home_before, vassal_before = region_row(ctx, home), region_row(ctx, vassal)
    result = ctx.mod.command("InvasionMod.sack_now", difficulty=3)
    home_after, vassal_after = region_row(ctx, home), region_row(ctx, vassal)
    ctx.check("R1 the sack names the home region", result["region"] == home, [result["region"], home])
    ctx.check("R1 the home region lost families", (home_after["families"] or 0) < (home_before["families"] or 0), [home_before["families"], home_after["families"]])
    ctx.check("R1 the vassal region lost no family", (vassal_after["families"] or 0) == (vassal_before["families"] or 0), [vassal_before["families"], vassal_after["families"]])
    ctx.metric("home_families_lost", (home_before["families"] or 0) - (home_after["families"] or 0))
    ctx.time.run_game_days(2, speed=SPEED)
    ctx.check("R5 the game runs 2 days after the sack", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
