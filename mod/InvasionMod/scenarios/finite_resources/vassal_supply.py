"""M10 iteration 02 and change update-vassal-tribute-rich-resources: tribute goods do not reduce the home deposits.

Run it with --new-game (like tribute-payout). It makes one vassal (claim, settle, handover), jumps a season (a new month)
and reads the home stores. The vassal pays 2 goods of 100 units of the rich resources of its region (iron and salt only when they are rich there).
The tribute is not production, so the `mined` count of the home deposits stays 0. It saves nothing.
"""

from _new_game import begin_game

NAME = "finite-resources-vassal-supply"
DESCRIPTION = "A vassal pays 2 rich goods at a month change; the iron, salt and clay deposits of the home region are not reduced by it."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then a season jump."
INFLUENCE = 1000
SEASONS = ["winter", "spring", "summer", "autumn"]


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
    ctx.actions.set_season(SEASONS[(before["season"] + 1) % 4])
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what="the tribute tick")


def run(ctx) -> dict:
    begin_game(ctx)  # a new game waits at the start screen
    ctx.run_until(lambda: tribute(ctx)["last_month"] >= 0, 30, what="the saved month")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    ctx.check("V0 the three home deposits exist (clay, iron, salt)", sorted(deposits(ctx)) == ["clay", "iron", "salt"], deposits(ctx))
    make_vassal(ctx)
    before = tribute(ctx)
    jump_season(ctx)
    after = tribute(ctx)
    payment = after["history"][-1]["payments"][0]
    ctx.log.info(f"TRIBUTE payment {payment}")
    paid = after["paid_total"] - before["paid_total"]
    ctx.check("V1 the vassal paid 2 goods of 100", paid == 200 and len(payment["goods"]) == 2, [paid, payment])
    gains = {good["name"]: after["stock"].get(str(good["id"]), 0) - before["stock"].get(str(good["id"]), 0) for good in payment["goods"]}
    ctx.check("V2 the home stores rose by about the paid goods", sum(gains.values()) >= 0.9 * paid, gains)
    ctx.check("V3 no failed deposit", after["failed_deposits"] == 0, after["failed_deposits"])
    home = deposits(ctx)
    ctx.check("V4 the tribute does not reduce the home deposits", all(home[name]["mined"] == 0 for name in ("iron", "salt", "clay")), home)
    ctx.metric("paid", paid)
    return ctx.result()
