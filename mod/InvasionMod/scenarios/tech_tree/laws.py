"""M12 iteration 04: a law and a vassal policy change the tribute.

Run it with --new-game (like tribute-payout). It makes one vassal, picks Prosperity, unlocks Fair Courts and Amnesty,
sets the vassal policy light (needs Fair Courts), enacts Trade Pacts (tribute x1.25) and jumps a season.
It saves nothing.
"""

NAME = "tech-tree-laws"
DESCRIPTION = "A vassal policy and a law of the tech tree change the tribute (5 families: 13 with light and Trade Pacts)."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then season jumps."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def make_vassal(ctx) -> None:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")


def jump_season(ctx) -> int:
    """Jump to the next season, wait for the tribute tick, return the goods paid by this tick."""
    before = tribute(ctx)
    ctx.actions.set_season(SEASONS[(before["last_season"] + 1) % 4])
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")
    return tribute(ctx)["paid_total"] - before["paid_total"]


def run(ctx) -> dict:
    ctx.run_until(lambda: tribute(ctx)["last_season"] >= 0, 30, what="the saved season")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    make_vassal(ctx)

    ctx.mod.command("InvasionMod.tech_tree_choose_path", path="prosperity")
    ensure_picks(ctx, 2)
    refused = ctx.mod.refusal("InvasionMod.tech_tree_set_vassal_policy", slot=1, policy="light")
    ctx.check("L1 light is refused before Fair Courts", refused is not None and "fair_courts" in refused, refused)
    ctx.mod.command("InvasionMod.tech_tree_unlock", node="fair_courts")
    ctx.mod.command("InvasionMod.tech_tree_unlock", node="amnesty")
    ctx.mod.command("InvasionMod.tech_tree_set_vassal_policy", slot=1, policy="light")
    heavy = ctx.mod.refusal("InvasionMod.tech_tree_set_vassal_policy", slot=1, policy="heavy")
    ctx.check("L2 heavy is refused on the Prosperity path", heavy is not None and "oppression" in heavy, heavy)

    light_only = jump_season(ctx)
    ctx.check("L3 light alone pays 10 (5 families x 20 x 0.2 x 0.5)", light_only == 10, light_only)

    ctx.mod.command("InvasionMod.tech_tree_enact_law", law="trade_pacts")
    with_pacts = jump_season(ctx)
    ctx.check("L4 Trade Pacts raise the tribute by 25 percent (12 to 14)", 12 <= with_pacts <= 14, with_pacts)
    ctx.mod.command("InvasionMod.tech_tree_repeal_law", law="trade_pacts")
    repealed = jump_season(ctx)
    ctx.check("L6 after the repeal the tribute is 10 again", repealed == 10, repealed)
    ctx.metric("tribute_light", light_only)
    ctx.metric("tribute_light_pacts", with_pacts)
    return ctx.result()


def ensure_picks(ctx, wanted: int) -> None:
    """Wait for the start pick, then add picks (a test command) until `wanted` picks are earned."""
    ctx.run_until(lambda: ctx.mod.command("InvasionMod." + "tech_tree_state")["picks_earned"] >= 1, 30, what="the start pick")
    missing = wanted - ctx.mod.command("InvasionMod." + "tech_tree_state")["picks_earned"]
    if missing > 0:
        ctx.mod.command("InvasionMod." + "tech_tree_test_grant_picks", count=missing)
