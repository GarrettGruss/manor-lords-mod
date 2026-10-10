"""Set winter and a rich, happy region with actions. Watch 3 game days. Check the date, the region and the telemetry."""

from runlib.timectl import absolute_day

NAME = "winter-region"
DESCRIPTION = "Jump to winter, force Approval and wealth in the player region, run 3 game days, check the date and how the game reacts."
LIMIT_S = 120
DAYS = 3
SPEED = 3
APPROVAL = 80
WEALTH = 200
WINTER = 0
RUNNING_MARGIN_S = 1.0


def _region_sample(sample: dict, name: str) -> dict | None:
    return next((region for region in sample["regions"] if region.get("name") == name), None)


def run(ctx) -> dict:
    expect = ctx.expect
    actions = ctx.actions
    bridge = ctx.bridge
    region_name = bridge.read_property(bridge.player_region_path(), "regionName")
    ctx.log.info(f"player region: {region_name}")

    actions.set_season("winter")
    actions.set_region_value("Approval", APPROVAL)
    actions.set_region_value("regionalWealth", WEALTH)
    start = ctx.read_calendar()

    record = ctx.time.run_game_days(DAYS, speed=SPEED)

    end = ctx.read_calendar()
    expect.changed("absolute day moved by 3", absolute_day(start), absolute_day(end), DAYS, DAYS)
    snapshot = ctx.snapshot()
    expect.equals("season is still winter", snapshot["date"]["season"], WINTER)
    region = _region_sample(snapshot, region_name)
    ctx.log.info(f"region after: {region}")
    # The game keeps the wealth, but it calculates Approval again (measured: 80 fell to 49 within 3 days).
    expect.equals("region wealth is kept", region["wealth"], WEALTH)
    expect.at_most("region Approval left the forced value", region["approval"], APPROVAL - 10)

    # Samples from the paused game before the run can still show the situation from before the actions.
    samples = [s for s in ctx.telemetry.window(record["clock_start"], record["clock_end"]) if s["clock"] > record["clock_start"] + RUNNING_MARGIN_S]
    expect.at_least("telemetry samples while running", len(samples), 2)
    expect.equals("telemetry seasons", sorted({s["date"]["season"] for s in samples}), [WINTER])
    wealth = sorted({_region_sample(s, region_name)["wealth"] for s in samples})
    expect.equals("telemetry wealth values", wealth, [WEALTH])
    return ctx.result()
