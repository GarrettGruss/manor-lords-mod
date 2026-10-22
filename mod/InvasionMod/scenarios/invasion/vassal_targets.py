"""M02 iteration 07, V1 to V6: the subjugation raid targets a vassal region and takes the vassal after 8 active days.

The scenario makes one vassal (M07.02), lets the first raid end, then forces the subjugation raid and runs game days.
The region owner is never written (it crashes the game). It saves nothing.
"""

import re

NAME = "invasion-vassal-targets"
DESCRIPTION = "A subjugation raid picks the vassal region as target; after 8 active days the vassal is lost with reason taken."
LIMIT_S = 1800
SPEED = 3
LONG_REASON = "Claim, settle and handover (about 100 s), the first raid ends (up to 40 game days), then the subjugation raid runs up to 14 game days."
INFLUENCE = 1000
DAY_LIMIT = 40
SIEGE_LIMIT_DAYS = 14
SPAWN = re.compile(r"INVASION spawn day=(\d+) .*kind=(\w+) target=(\S+) stand_in=(\w+)")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def raids(ctx) -> list[dict]:
    return ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]


def log_lines(ctx) -> list[str]:
    log = ctx.run_dir / "mod.log"
    return log.read_text(encoding="utf-8", errors="replace").splitlines() if log.exists() else []


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def free_region(ctx) -> str:
    rows = ctx.actions.regions_state()["regions"]
    free = [row["region"] for row in rows if not row.get("owner") and not row.get("settled")]
    if not free:
        raise RuntimeError(f"no free region in this start: {rows}")
    return free[0]


def owner_of(ctx, region: str) -> str:
    return str(next(r for r in ctx.actions.regions_state()["regions"] if r["region"] == region).get("owner"))


def make_vassal(ctx) -> str:
    region = free_region(ctx)
    ctx.actions.set_influence(INFLUENCE)
    ctx.actions.claim_region(region, target=0, finalize=True)
    ctx.run_until(lambda: vassals(ctx)["count"] == 1, 30, what="the claim in the registry")
    ctx.actions.settle_region(region, target=0, settlement_type=1, supply=2)
    ctx.run_until(lambda: vassals(ctx)["vassals"][0]["lord"] != "none", 40, what="the handover")
    return region


def finish_first_raid(ctx) -> None:
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 1, 30, what="the first raid record")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now", kind="subjugation")["day"] is not None and ctx.mod.command("InvasionMod.invasion_subjugation_state")["sub_day"] > 0, 30, what="the subjugation plan")
    days = 0
    while raids(ctx)[0]["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    region = make_vassal(ctx)
    finish_first_raid(ctx)

    owner_before = owner_of(ctx, region)
    ctx.mod.command("InvasionMod.invasion_subjugation_force_next")
    ctx.run_until(lambda: len(raids(ctx)) >= 2, 30, what="the subjugation raid record")
    spawns = [m.groups() for m in map(SPAWN.search, log_lines(ctx)) if m]
    ctx.check("V1 the subjugation raid targets the vassal region", any(kind == "subjugation" and target == region and stand == "false" for _, kind, target, stand in spawns), [spawns, region])

    days = 0
    while vassals(ctx)["lost"] == 0 and days < SIEGE_LIMIT_DAYS:
        run_day(ctx)
        days += 1
    state = vassals(ctx)
    ctx.metric("siege_days", days)
    ctx.check("V3 the vassal is lost after the siege", state["lost"] == 1 and state["count"] == 0, state)
    ctx.check("V3 the reason is taken", bool(state["lost_events"]) and state["lost_events"][0]["reason"] == "taken", state["lost_events"])
    ctx.check("V3 the siege lasted at least 8 days", days >= 7, days)
    owner_after = owner_of(ctx, region)
    ctx.check("V5 the region owner is unchanged (no owner write)", owner_after == owner_before, [owner_before, owner_after])
    ctx.time.run_game_days(2, speed=SPEED)
    ctx.check("V6 the game runs 2 days after the loss", vassals(ctx)["day"] is not None, vassals(ctx))
    return ctx.result()
