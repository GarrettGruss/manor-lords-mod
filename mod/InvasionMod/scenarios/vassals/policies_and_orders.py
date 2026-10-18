"""M07 iteration 03, P1 to P6: mod-owned policies change loyalty at each season change and scale the tribute; a gift raises loyalty.

The scenario makes one vassal (M07.02) and jumps seasons with set_season. Run it with --new-game. It saves nothing.
"""

NAME = "vassals-policies-and-orders"
DESCRIPTION = "Policy light/fair/heavy: loyalty change per season and tribute factor; the gift order costs silver and adds loyalty."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then season jumps and one game day at speed 2."
INFLUENCE = 1000
START_SILVER = 500
SEASONS = ["winter", "spring", "summer", "autumn"]


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def row(ctx) -> dict:
    return vassals(ctx)["vassals"][0]


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


def jump_season(ctx) -> dict:
    """Jump to the next season and wait for both ticks (tribute and loyalty). Returns the tribute state."""
    before = tribute(ctx)
    ctx.actions.set_season(SEASONS[(before["last_season"] + 1) % 4])
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")
    ctx.time.run_game_seconds(6, speed=1)  # the loyalty tick has its own poll
    return tribute(ctx)


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    ctx.actions.set_silver(START_SILVER)
    make_vassal(ctx)
    ctx.run_until(lambda: vassals(ctx).get("day") is not None, 10, what="the state")
    ctx.check("P1 the default policy is fair", row(ctx)["policy"] == "fair", row(ctx))

    jump_season(ctx)
    ctx.check("P2 fair keeps the loyalty at a season change", row(ctx)["loyalty"] == 50, row(ctx))

    for policy, loyalty_after, factor in (("heavy", 45, 1.5), ("light", 48, 0.5)):
        ctx.mod.command("InvasionMod.vassals_set_policy", slot=1, policy=policy)
        jump_season(ctx)
        current = row(ctx)
        payment = tribute(ctx)["history"][-1]["payments"][0]
        ctx.check(f"P3 {policy} changes the loyalty once", current["loyalty"] == loyalty_after, current)
        want = (0.10 + 0.20 * payment["loyalty"] / 100) * factor
        ctx.check(f"P4 {policy} scales the tribute share by {factor}", payment["policy"] == policy and abs(payment["share"] - want) < 1e-6, payment)

    before_loyalty = row(ctx)["loyalty"]
    gift = ctx.mod.command("InvasionMod.vassals_order_gift", slot=1)
    ctx.check("P5 a gift costs 50 silver and adds 10 loyalty", gift["cost"] == 50 and gift["loyalty"] == before_loyalty + 10, gift)

    refused = False
    try:
        ctx.mod.command("InvasionMod.vassals_set_policy", slot=1, policy="harsh")
    except Exception as error:  # ModCommandError: an unknown policy is refused
        refused = "unknown policy" in str(error)
    ctx.check("P6 an unknown policy is refused", refused)
    ctx.time.run_game_days(1, speed=SPEED)
    ctx.check("P6 the game runs", vassals(ctx)["day"] is not None)
    return ctx.result()
