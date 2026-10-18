"""M08 iteration 01, T1 to T6: each season change pays goods for each handed-over vassal.

The scenario makes one vassal like M07.02 (claim, settle, handover), then jumps the season with set_season.
Run it with --new-game. Families of the vassal region: 5 after the settle call. Production = 5 x 20 = 100.
It saves nothing.
"""

NAME = "tribute-payout"
DESCRIPTION = "A season change pays 10 to 30 percent of the vassal production into the home stores."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), four season jumps, and 5 game days at speed 2."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]
FISH, TIMBER = "30", "16"


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def next_season(ctx) -> str:
    return SEASONS[(tribute(ctx)["last_season"] + 1) % 4]


def jump_season(ctx) -> dict:
    """Jump to the next season and wait for the tick of the mod. Returns the new state."""
    before = tribute(ctx)
    ctx.actions.set_season(next_season(ctx))
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")
    return tribute(ctx)


def make_vassal(ctx) -> None:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")


def stock_of(state: dict, good: str) -> int:
    return state["stock"].get(good, 0)


def run(ctx) -> dict:
    ctx.run_until(lambda: tribute(ctx)["last_season"] >= 0, 30, what="the saved season")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    first = jump_season(ctx)
    ctx.check("T2 a season change with no vassal pays nothing", first["ticks"] == 1 and first["paid_total"] == 0, first)

    make_vassal(ctx)
    before = tribute(ctx)
    families = vassals(ctx)["vassals"][0]["families"]
    after = jump_season(ctx)
    paid = after["paid_total"] - before["paid_total"]
    expected = round(families * 20 * 0.2)
    ctx.check("T1 one vassal at loyalty 50 pays 20 percent of its production", paid == expected and families == 5, [paid, expected, families])
    gain_fish = stock_of(after, FISH) - stock_of(before, FISH)
    gain_timber = stock_of(after, TIMBER) - stock_of(before, TIMBER)
    ctx.check("T1 the stores rose by the paid goods", gain_fish + gain_timber >= paid and gain_fish >= paid // 2, [gain_fish, gain_timber, paid])
    ctx.check("T5 no failed deposit", after["failed_deposits"] == 0, after)

    ctx.time.run_game_days(2, speed=SPEED)
    later = tribute(ctx)
    ctx.check("T3 one payment for one season change", later["ticks"] == after["ticks"] and later["paid_total"] == after["paid_total"], later)

    for loyalty, share in ((100, 0.3), (0, 0.1)):
        ctx.mod.command("InvasionMod.vassals_set_loyalty", slot=1, value=loyalty)
        start = tribute(ctx)
        done = jump_season(ctx)
        got = done["paid_total"] - start["paid_total"]
        ctx.check(f"T4 loyalty {loyalty} pays {int(share * 100)} percent", got == round(5 * 20 * share), [got, loyalty])
    ctx.metric("paid_total", tribute(ctx)["paid_total"])
    ctx.metric("ticks", tribute(ctx)["ticks"])
    ctx.check("T6 the game still runs", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
