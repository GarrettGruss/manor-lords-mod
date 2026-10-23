"""Change add-vassal-sack-wipe: a sack of a vassal that ends without a wipe.

The scenario adopts the AI-lord region Goldhof (Hochweg, internal name; option VASSAL_REGION) as a vassal (command `vassals_adopt`). `vassals_sack` starts the sack: the mod removes all logs and planks of the
region and collapses 80 percent of the buildings. The option `hold` keeps the sack from wiping; when the ruins are there, `vassals_end_sack` ends it.
The mod gives 50 logs and 100 planks and orders the rebuild of every ruin. The scenario watches the ruins become construction sites
and the sites get built. It saves nothing.
Environment (run.py --env): REBUILD_DAYS (game days to watch after the order, default 15).
"""

NAME = "vassals-sack-end"
DESCRIPTION = "A sack that ends without a wipe removes the wood, gives 50 logs and 100 planks and orders the rebuild of every ruin."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "Claim, settle and handover (about 100 s), 10 game days of growth, then up to 15 game days of rebuild at speed 3."
GROWTH_DAYS = 1
STEP_DAYS = 5


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def census(ctx, region: str) -> dict:
    return ctx.mod.command("InvasionMod.vassals_region_census", region=region)


def make_vassal(ctx) -> str:
    """Adopt a region that an AI lord already owns (owner, 2026-10-22: a vassal is a region of an AI lord). Default Goldhof (Hochweg)."""
    region = ctx.variant_option("VASSAL_REGION", "Goldhof")
    answer = ctx.mod.command("InvasionMod.vassals_adopt", region=region)
    ctx.log.info(f"adopted {region}: slot {answer['adopted_slot']}")
    return region


def run(ctx) -> dict:
    rebuild_days = int(ctx.variant_option("REBUILD_DAYS", "15"))
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    region = make_vassal(ctx)
    ctx.time.run_game_days(GROWTH_DAYS, speed=SPEED)
    before = census(ctx, region)
    ctx.metric("buildings_before_sack", before["total"])

    started = ctx.mod.command("InvasionMod.vassals_sack", slot=1, hold=True)["sack"]
    needed = -(-before["total"] * 4 // 5)
    ctx.run_until(lambda: census(ctx, region)["rubble"] >= needed, 60, what="the collapses of the sack")
    ctx.log.info(f"sack started: {started}")
    ctx.check("E1 the sack start removed the wood (both goods reported)", set(started.get("wood_removed", {})) == {"logs", "planks"}, started)
    ended = ctx.mod.command("InvasionMod.vassals_end_sack", slot=1)
    state = ended
    ctx.check("E2 the village is not wiped", state["lost"] == 0 and state["count"] == 1, state)
    result = ended["ended"]
    ctx.log.info(f"sack ended: {result}")
    ctx.check("E3 the region got 50 logs and 100 planks", result["given"] == {"logs": 50, "planks": 100}, result["given"])
    ctx.check("E4 the rebuild order failed for no building", result["rebuild"]["failed"] == 0, result["rebuild"])
    now = census(ctx, region)
    ctx.metric("rubble_after_end", now["rubble"])
    ctx.metric("built_after_end", now["built"])
    ctx.check("E5 every ruin was ordered (rubble left is only the skipped ones)", now["rubble"] <= result["rebuild"]["skipped"], [now, result["rebuild"]])
    ctx.check("E6 the ordered ruins are construction sites, not finished buildings", now["built"] < now["standing"] or result["rebuild"]["ordered"] == 0, now)

    for day in range(STEP_DAYS, rebuild_days + 1, STEP_DAYS):
        ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        later = census(ctx, region)
        ctx.metric(f"built_day{day}", later["built"])
        ctx.metric(f"rubble_day{day}", later["rubble"])
        ctx.log.info(f"rebuild day {day}: {later}")
    final = census(ctx, region)
    ctx.check("E7 more buildings are built than right after the order", final["built"] > now["built"], [now, final])
    ctx.check("E8 the game runs on", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
