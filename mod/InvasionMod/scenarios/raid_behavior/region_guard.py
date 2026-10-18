"""M03.02 follow-up: the guard gives a region back when the raid lord wins it.

The scenario forces the win with a test command (the lord becomes the region owner, as a won challenge does) and checks
that the player owns the region again. It saves nothing.
"""

NAME = "raid-behavior-region-guard"
DESCRIPTION = "A region that the raid lord took goes back to the player."
LIMIT_S = 300
SPEED = 3
LOOK_SECONDS = 30


def player_owns(ctx, region_name: str) -> bool:
    for row in ctx.actions.regions_state().get("regions", []):
        if row.get("region") == region_name:
            return "MyPawn" in (row.get("owner") or "")
    return False


def lord_raid_record(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
    return raids[0] if raids else {}


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=1)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(lord_raid_record(ctx)), 30, what="the raid record")
    ctx.check("the raid is a lord raid", lord_raid_record(ctx).get("lord_raid") is True, lord_raid_record(ctx))

    taken = ctx.mod.command("InvasionMod.raid_behavior_test_take_region")
    region = taken["region"]
    ctx.time.run_game_seconds(LOOK_SECONDS, speed=SPEED)
    # The guard acts within one look (about 5 s), so a read of the owner right after the command may see the player already.
    # The log line proves that the lord had the region.
    log = (ctx.run_dir / "mod.log").read_text(encoding="utf-8", errors="replace")
    ctx.check("the guard saw the lord as owner and gave the region back", f"region {region} was taken by the lord, given back=true" in log, region)
    ctx.check("the region is the player's again", player_owns(ctx, region), region)
    population = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.check("the village still has people", population is not None and population > 0, population)
    return ctx.result()
