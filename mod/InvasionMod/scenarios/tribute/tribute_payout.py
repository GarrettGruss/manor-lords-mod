"""M08 iteration 01 and change update-vassal-tribute-rich-resources: each month change pays goods for each handed-over vassal.

The scenario makes one vassal like M07.02 (claim, settle, handover), then jumps the season with set_season (a season jump is also a month change).
The vassal pays 2 goods of 100 units (policy fair). Which goods depends on the rich resources of the claimed region; flax fills up.
Run it with --new-game. It saves nothing.
"""

NAME = "tribute-payout"
DESCRIPTION = "A month change pays 100 units of each of 2 rich goods of the vassal region into the home stores."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), two season jumps, and 2 game days at speed 2."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]
BASE = 100


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


def jump_season(ctx) -> dict:
    """Jump to the next season (a new month) and wait for the tick of the mod. Returns the new state."""
    before = tribute(ctx)
    ctx.actions.set_season(SEASONS[(before["season"] + 1) % 4])
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
    ctx.run_until(lambda: tribute(ctx)["last_month"] >= 0, 30, what="the saved month")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    first = jump_season(ctx)
    ctx.check("T2 a month change with no vassal pays nothing", first["ticks"] == 1 and first["paid_total"] == 0, first)

    make_vassal(ctx)
    before = tribute(ctx)
    after = jump_season(ctx)
    paid = after["paid_total"] - before["paid_total"]
    payment = after["history"][-1]["payments"][0]
    ctx.log.info(f"TRIBUTE payment {payment}")
    ctx.check("T1 one fair vassal pays 2 goods of 100", paid == 2 * BASE and len(payment["goods"]) == 2 and payment["amount"] == BASE, [paid, payment])
    gains = {good["name"] + str(index): stock_of(after, str(good["id"])) - stock_of(before, str(good["id"])) for index, good in enumerate(payment["goods"])}
    ctx.check("T1 the stores rose by about the paid goods", sum(gains.values()) >= 0.9 * paid, gains)
    ctx.check("T5 no failed deposit", after["failed_deposits"] == 0, after)

    ctx.time.run_game_days(2, speed=SPEED)
    later = tribute(ctx)
    ctx.check("T3 one payment for one month change", later["ticks"] == after["ticks"] and later["paid_total"] == after["paid_total"], later)

    ctx.metric("paid_total", tribute(ctx)["paid_total"])
    ctx.metric("ticks", tribute(ctx)["ticks"])
    ctx.check("T6 the game still runs", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
