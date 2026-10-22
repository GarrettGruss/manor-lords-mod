"""M09 iteration 02, H1 to H6: housed refugees end the wave; unhoused refugees turn into bandits at the timeout.

Phase 1: a wave, 5 burgage plots without the mouse, the wave ends housed.
Phase 2: a second wave with a 3 game day timeout; the unhoused families leave as bandits.
Run it with `--fixture base` (it relies on the exact families and homes of that save). It saves nothing.
"""

from runlib import plotgeom
from runlib.units import side_count

NAME = "refugees-housing-and-timeout"
DESCRIPTION = "A refugee wave ends housed after the player builds homes; a second wave turns into bandits at the timeout."
LIMIT_S = 900
SPEED = 2
LONG_REASON = "Claim, settle and handover (about 100 s), a plot build of about 12 game days and a timer phase at speed 2 (speed 3 crashed the game in run 20261018-081339-1665)."
INFLUENCE = 1000
TIMBER = 16
TIMBER_AMOUNT = 60
PLOT_COUNT = 5
BUILD_DAYS_LIMIT = 24
PHASE2_TIMEOUT_DAYS = 3
PHASE2_DAYS_LIMIT = 8


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


def place_plots(ctx) -> None:
    actions = ctx.actions
    spots = actions.tent_find_spot()
    spot, centre = spots["spots"][0], spots["centre"]
    plots = plotgeom.make_plots(spot["x"], spot["y"], spot["z"], spot["x"] - centre["x"], spot["y"] - centre["y"], PLOT_COUNT)
    actions.give_item(TIMBER, TIMBER_AMOUNT)
    actions.open_burgage_tool()
    actions.plot_field_place(plots)
    actions.commit_plots()


def run_days_until_done(ctx, limit: int) -> int:
    days = 0
    while refugees(ctx)["active"] and days < limit:
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)
        days += 1
    return days


def phase_one(ctx) -> None:
    before = refugees(ctx)["numbers"]
    wave = ctx.mod.command("InvasionMod.refugees_vassal_lost", slot=1, share=30)
    ctx.check("H1 the wave is active with homeless families", wave["active"] and wave["numbers"]["homeless"] > before["homeless"], wave)
    low = wave["numbers"]["approval"]
    ctx.time.run_game_days(2, speed=SPEED)
    ctx.check("H2 the wave is still active while the refugees are homeless", refugees(ctx)["active"], refugees(ctx))
    low = min(low, refugees(ctx)["numbers"]["approval"])
    place_plots(ctx)
    days = run_days_until_done(ctx, BUILD_DAYS_LIMIT)
    final = refugees(ctx)
    ctx.check("H3 the wave ended housed", final["last_outcome"] == "housed" and final["housed"] == 1 and not final["active"], [days, final])
    ctx.check("H3 no homeless wave families are left", final["numbers"]["homeless"] <= before["homeless"], [before, final["numbers"]])
    ctx.check("H3 no family turned to bandits", final["rebelled"] == 0 and final["bandit_families"] == 0, final)
    ctx.metric("days_to_house", days)
    ctx.metric("approval_low", low)
    ctx.metric("approval_after", final["numbers"]["approval"])


def phase_two(ctx) -> None:
    ctx.mod.command("InvasionMod.refugees_set_timeout", days=PHASE2_TIMEOUT_DAYS)
    before = refugees(ctx)["numbers"]
    bandits_before = side_count(ctx.actions.units_census(), "bandit")
    wave = ctx.mod.command("InvasionMod.refugees_vassal_lost", slot=1, share=30)
    unhoused = wave["numbers"]["homeless"] - wave["base_homeless"]
    ctx.check("H4 the second wave has unhoused families", unhoused >= 1, wave)
    days = run_days_until_done(ctx, PHASE2_DAYS_LIMIT)
    final = refugees(ctx)
    ctx.check("H5 the timer turned the unhoused families into bandits", final["last_outcome"] == "rebelled" and final["rebelled"] == 1, [days, final])
    ctx.check("H5 the converted families match the unhoused ones", 1 <= final["bandit_families"] <= unhoused, [unhoused, final])
    ctx.run_until(lambda: side_count(ctx.actions.units_census(), "bandit") > bandits_before, 20, what="the bandit squad")
    ctx.check("H5 bandit units appeared", side_count(ctx.actions.units_census(), "bandit") > bandits_before)
    ctx.check("H5 the home region lost the families", refugees(ctx)["numbers"]["families"] < wave["numbers"]["families"], [before, wave["numbers"], refugees(ctx)["numbers"]])


def run(ctx) -> dict:
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    make_vassal(ctx)
    phase_one(ctx)
    phase_two(ctx)
    ctx.check("H6 the game still runs", refugees(ctx)["day"] is not None)
    return ctx.result()
