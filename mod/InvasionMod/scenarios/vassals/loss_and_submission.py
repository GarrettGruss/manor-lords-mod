"""M07 iteration 04, L6 to L8: a lost vassal frees its slot and sends refugees.

The scenario makes one vassal (M07.02). Option (run.py --env): LOSS_REGION (forget or take_by_lord, default forget). With forget the lord keeps the land; with take_by_lord another AI lord is given the region (crashed the game). Run it on the default fixture. It saves nothing.
"""

NAME = "vassals-loss-and-submission"
DESCRIPTION = "The lose command frees the slot and sends a refugee wave."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), 4 game days at speed 2."
INFLUENCE = 1000


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def refugees(ctx) -> dict:
    return ctx.mod.command("InvasionMod.refugees_state")


def row(ctx) -> dict:
    return vassals(ctx)["vassals"][0]


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


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    region = make_vassal(ctx)
    mode = ctx.variant_option("LOSS_REGION", "forget")
    ctx.mod.command("InvasionMod.vassals_set_loss_region", mode=mode)

    last_owner = str(next(r for r in ctx.actions.regions_state()["regions"] if r["region"] == region).get("owner"))
    families_before = refugees(ctx)["numbers"]["families"]
    answer = ctx.mod.command("InvasionMod.vassals_lose", slot=1)
    ctx.check("L6 the lost vassal frees the slot", answer["count"] == 0 and answer["lost"] == 1 and answer["event"]["reason"] == "command", answer)
    wave = refugees(ctx)
    ctx.check("L7 the lost vassal sent a refugee wave", wave["active"] and wave["waves"] == 1 and wave["numbers"]["families"] - families_before == 5, [families_before, wave])
    rows = {r["region"]: r for r in ctx.actions.regions_state()["regions"]}
    owner = str(rows[region].get("owner"))
    if mode == "forget":
        ctx.check("L6 the land stays with its lord (the vassal went independent)", owner == last_owner, [owner, last_owner])
    else:
        ctx.check("L6 another lord owns the land now", owner.startswith("PawnCPP_AI") and owner != last_owner, [owner, last_owner])
    ctx.time.run_game_days(4, speed=SPEED)
    ctx.check("L8 the game runs 4 days after the loss", vassals(ctx)["day"] is not None and vassals(ctx)["count"] == 0, vassals(ctx))
    return ctx.result()
