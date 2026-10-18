"""M07 iteration 02, H1 to H6: the player claims and settles a region; the mod hands it to a friendly AI lord.

The lord may build (4 to 14 buildings seen) or stall (no build seen when the region starts with 5 buildings). The mod flags a stall after 10 game days. The lord starts a war on its own; the mod declares peace. The scenario watches 20 game days in steps of 5.
Options (run.py --env): VASSAL_SUPPLY (0 to 2, default 2: the supply given to the settle call), VASSAL_KEEP_PEACE (1 or 0, default 1: the mod declares peace when the lord is at war with the player). It saves nothing.
"""

NAME = "vassals-settled-vassal"
DESCRIPTION = "A settled region is handed to an AI lord that builds and stays at peace with the player."
LIMIT_S = 700
SPEED = 2
STEP_DAYS = 5
WATCH_DAYS = 20
LONG_REASON = "20 game days at speed 2 (about 13 s per day) plus the claim, the settle and the handover."
INFLUENCE = 1000
MIN_NEW = 3  # config growth_min_buildings


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def region_row(ctx, name: str) -> dict:
    return next(row for row in ctx.actions.regions_state()["regions"] if row["region"] == name)


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def home_row(ctx) -> dict:
    return region_row(ctx, state(ctx)["home_region"])


LOG_LINES = 40
LORD_NAME = "Aldric"
seen_lines: dict = {"construction": set(), "general": set()}


def collect_lord_lines(ctx) -> None:
    """The AI logs keep only the newest lines of all lords, so the lines of the vassal lord are collected at every step."""
    logs = ctx.actions.lords_state(log=LOG_LINES)["logs"]
    for key, name in (("construction", "debugLog_AI_construction"), ("general", "debugLog_AI_general")):
        seen_lines[key].update(line for line in logs.get(name, []) if line.startswith(LORD_NAME))


def wars(current: dict) -> list:
    return [lord for lord in (current.get("wars") or {}).values() if lord and (lord["enemy_of_player"] or "at_war" in lord["tags"])]


def run(ctx) -> dict:
    supply = int(ctx.variant_option("VASSAL_SUPPLY", "2"))
    keep_peace = ctx.variant_option("VASSAL_KEEP_PEACE", "1") == "1"
    ctx.mod.command("InvasionMod.vassals_set_keep_peace", value=keep_peace)
    ctx.run_until(lambda: state(ctx)["home_region"] != "none", 30, what="the home region")
    home_before = home_row(ctx)
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: state(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.check("the claimed region is a slot without a lord yet", state(ctx)["vassals"][0]["lord"] == "none", state(ctx))
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=supply)
    ctx.run_until(lambda: state(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")
    handed = state(ctx)
    owner = region_row(ctx, region)
    ctx.check("H1 the lord owns the region", handed["vassals"][0]["lord"] == "Aldric" and bool(owner.get("owner")) and "AI" in str(owner["owner"]), [handed["vassals"], owner])
    start_buildings = owner.get("buildings") or 0
    war_seen = False
    history = []
    for step in range(STEP_DAYS, WATCH_DAYS + 1, STEP_DAYS):
        ctx.time.run_game_days(STEP_DAYS, speed=SPEED)
        current = state(ctx)
        row = region_row(ctx, region)
        war_seen = war_seen or bool(wars(current))
        collect_lord_lines(ctx)
        history.append({"day": step, "buildings": row.get("buildings"), "families": row.get("families"), "wars": current.get("wars")})
        ctx.log.info(f"VASSAL step {history[-1]}")
        ctx.metric(f"buildings_day{step}", row.get("buildings") or 0)
    final = region_row(ctx, region)
    for key, lines in seen_lines.items():
        ctx.log.info(f"VASSAL lord lines {key}: {sorted(lines)[:30]}")
    ctx.metric("build_lines", len([line for line in seen_lines["construction"] if "AI_build" in line and "lacks" not in line]))
    ctx.metric("buildings_start", start_buildings)
    ctx.metric("buildings_end", final.get("buildings") or 0)
    grew = (final.get("buildings") or 0) >= start_buildings + MIN_NEW
    flagged = state(ctx)["vassals"][0]["stalled"]
    ctx.metric("grew", int(grew))
    ctx.check("H2 the stall flag matches what happened (a lord that did not build is flagged, one that built is not)", flagged == (not grew), [start_buildings, final.get("buildings"), flagged, history])
    ctx.metric("war_seen", int(war_seen))
    ctx.metric("peace_calls", sum((state(ctx).get("peace_calls") or {}).values()))
    if keep_peace:
        ctx.check("H3 with keep_peace the lord is not at war at any 5 day look", not war_seen, history)
    else:
        ctx.log.info(f"H3 observation only: war seen = {war_seen}")
    home_after = home_row(ctx)
    ctx.check("H4 the home region stays the player region", home_after["owner"] == home_before["owner"]
              and (home_after.get("families") or 0) >= 0.9 * (home_before.get("families") or 0), [home_before, home_after])
    ctx.check("H6 the registry still holds the vassal", state(ctx)["count"] == 1, state(ctx))
    return ctx.result()
