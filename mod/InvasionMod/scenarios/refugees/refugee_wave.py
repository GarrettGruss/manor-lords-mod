"""M09 iteration 01, R1 to R7: a lost vassal sends a wave of refugee families to the home region.

The scenario makes one vassal like M07.02, then calls refugees_vassal_lost. Run it on the default fixture (base: 10 families, approval about 71, free homes). On a new game all 5 start families are homeless and approval stays 50, so R4 cannot show a fall. It saves nothing.
"""

NAME = "refugees-wave"
DESCRIPTION = "A lost vassal sends 30 percent of its families as refugees; homeless families lower approval."
LIMIT_S = 500
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), then 4 game days at speed 2."
INFLUENCE = 1000
WATCH_DAYS = 4


def refugees(ctx) -> dict:
    return ctx.mod.command("InvasionMod.refugees_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


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


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    make_vassal(ctx)
    before = refugees(ctx)["numbers"]
    answer = refugees(ctx)
    ctx.check("no wave before the vassal is lost", not answer["active"] and answer["waves"] == 0, answer)

    wave = ctx.mod.command("InvasionMod.refugees_vassal_lost", slot=1, share=30)
    after = wave["numbers"]
    ctx.check("R1 the wave added 5 families to the home region", after["families"] - before["families"] == 5 and wave["last_wave"]["calls"] == 1, [before, after, wave["last_wave"]])
    ctx.check("R2 the wave is active and remembers the homeless base", wave["active"] and wave["base_homeless"] == before["homeless"], wave)
    homeless_rise = after["homeless"] - before["homeless"]
    ctx.metric("homeless_rise", homeless_rise)
    ctx.check("R3 some refugee families are homeless (tent camp)", homeless_rise >= 1, [before, after])

    again = ctx.mod
    try:
        again.command("InvasionMod.refugees_vassal_lost", slot=1, share=30)
        refused = False
    except Exception as error:  # ModCommandError: the mod refuses a second wave
        refused = "active" in str(error)
    ctx.check("R5 a second wave is refused while one is active", refused)

    low = after["approval"]
    ctx.time.run_game_days(WATCH_DAYS, speed=SPEED)
    now = refugees(ctx)["numbers"]
    low = min(low, now["approval"])
    ctx.metric("approval_before", before["approval"])
    ctx.metric("approval_low", low)
    if homeless_rise >= 1 and now["homeless"] > before["homeless"]:
        ctx.check("R4 approval fell while the refugees stayed homeless", before["approval"] - low >= 3, [before["approval"], low, now])
    ctx.check("R7 the game ran 4 days after the wave", refugees(ctx)["day"] is not None, refugees(ctx))
    return ctx.result()
