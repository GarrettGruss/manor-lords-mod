"""M10 iteration 02: a vassal pays iron and salt at each season change (the permanent supply), and the home deposits do not count it.

Run it with --new-game (like tribute-payout). It makes one vassal (claim, settle, handover), jumps a season and reads the home stores.
Families of the vassal region: 5. Loyalty 50 gives a share of 20 percent: iron 5 x 10 x 0.2 = 10, salt 5 x 6 x 0.2 = 6. It saves nothing.
"""

NAME = "finite-resources-vassal-supply"
DESCRIPTION = "A vassal pays 10 iron and 6 salt at a season change; the iron deposit of the home region is not reduced by it."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then a season jump."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]
IRON, SALT = "14", "145"


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def deposits(ctx) -> dict:
    return {item["name"]: item for item in ctx.mod.command("InvasionMod.finite_resources_state")["resources"]}


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def make_vassal(ctx) -> None:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")


def jump_season(ctx) -> None:
    before = tribute(ctx)
    ctx.actions.set_season(SEASONS[(before["last_season"] + 1) % 4])
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")


def run(ctx) -> dict:
    ctx.run_until(lambda: tribute(ctx)["last_season"] >= 0, 30, what="the saved season")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    ctx.check("V0 the three home deposits exist (clay, iron, salt)", sorted(deposits(ctx)) == ["clay", "iron", "salt"], deposits(ctx))
    make_vassal(ctx)
    ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=50)
    before = tribute(ctx)
    jump_season(ctx)
    after = tribute(ctx)
    iron = after["stock"].get(IRON, 0) - before["stock"].get(IRON, 0)
    salt = after["stock"].get(SALT, 0) - before["stock"].get(SALT, 0)
    ctx.check("V1 the vassal paid 10 iron and 6 salt", after["finite_paid"].get("iron") == 10 and after["finite_paid"].get("salt") == 6, after["finite_paid"])
    ctx.check("V2 the home stores rose by the paid iron and salt", iron >= 10 and salt >= 6, [iron, salt])
    ctx.check("V3 no failed deposit", after["failed_deposits"] == 0, after["failed_deposits"])
    home = deposits(ctx)
    ctx.check("V4 the tribute does not reduce the home deposits", home["iron"]["mined"] == 0 and home["salt"]["mined"] == 0, home)
    ctx.metric("iron_gain", iron)
    ctx.metric("salt_gain", salt)
    return ctx.result()
