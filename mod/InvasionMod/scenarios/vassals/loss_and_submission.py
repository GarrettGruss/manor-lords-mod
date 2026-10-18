"""M07 iteration 04, L1 to L8: a vassal with low loyalty submits (tribute stops, the lord goes to war) and returns; a lost vassal sends refugees.

The scenario makes one vassal (M07.02). Option (run.py --env): LOSS_REGION (forget or take_by_lord, default forget). With forget the lord keeps the land; with take_by_lord another AI lord is given the region (crashed the game). Run it on the default fixture (base). It saves nothing.
"""

NAME = "vassals-loss-and-submission"
DESCRIPTION = "Submission at loyalty 10 or less, return at 40 or more; the lose command frees the slot and sends a refugee wave."
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), two season jumps, 4 game days at speed 2."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


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


def jump_season(ctx) -> dict:
    before = tribute(ctx)
    ctx.actions.set_season(SEASONS[(before["last_season"] + 1) % 4])
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")
    return tribute(ctx)


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    region = make_vassal(ctx)
    mode = ctx.variant_option("LOSS_REGION", "forget")
    ctx.mod.command("InvasionMod.vassals_set_loss_region", mode=mode)

    ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=5)
    ctx.mod.command("InvasionMod.vassals_submission_tick_now")
    ctx.run_until(lambda: any(w and w.get("enemy_of_player") for w in (vassals(ctx).get("wars") or {}).values()), 20, what="the war of the submitted lord")
    state = vassals(ctx)
    ctx.check("L1 a vassal at loyalty 5 submits", row(ctx)["submitted"] and state["submissions"] == 1, state)
    ctx.check("L2 the lord of a submitted vassal is at war with the player (the mod does not make peace)", state["wars"]["1"]["enemy_of_player"], state["wars"])

    before = tribute(ctx)
    after = jump_season(ctx)
    ctx.check("L3 a submitted vassal pays no tribute", after["paid_total"] == before["paid_total"], [before["paid_total"], after["paid_total"]])

    ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=45)
    ctx.mod.command("InvasionMod.vassals_submission_tick_now")
    ctx.check("L4 at loyalty 45 the vassal returns", not row(ctx)["submitted"], row(ctx))
    ctx.run_until(lambda: not any(w and w.get("enemy_of_player") for w in (vassals(ctx).get("wars") or {}).values()), 30, what="peace with the returned lord")
    ctx.check("L5 the lord is at peace again", True)

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
