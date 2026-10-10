"""Stand-in mod: outposts, raid reveal, lost outposts, tribute and intel leaks, and evacuation (a toy model)."""

NAME = "standin-outposts"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Found two outposts, check the raid reveal inside and outside the border, lose one outpost, "
               "leave one unprotected for game days, then evacuate. Needs the mods InvasionStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["O1", "O2", "O3", "O4", "S4"]

PREFIX = "InvasionStandIn."
PROTECTED_REGION = 2
UNPROTECTED_REGION = 3
HOME_REGION = 1
WAIT_DAYS = 4  # the toy rule needs 3 unprotected days
SPEED = 3
TELEMETRY_WAIT_S = 20


def command(ctx, name, **args):
    return ctx.mod.command(PREFIX + name, **args)


def metric_is(ctx, label, name, expected):
    """A metric is read from the mod now. The wait covers the toy days that pass at game speed."""
    ctx.expect.eventually(label, lambda: ctx.mod.metric(PREFIX + name, None) == expected, TELEMETRY_WAIT_S)


def check_commands_are_listed(ctx):
    names = {item["name"] for item in ctx.mod.commands("InvasionStandIn")}
    wanted = {PREFIX + name for name in ("found_outpost", "lose_outpost", "reveal", "evacuate", "outpost")}
    ctx.expect.equals("stand-in commands are registered", sorted(wanted - names), [])


def found_outposts(ctx):
    command(ctx, "reset")
    protected = command(ctx, "found_outpost", region_id=PROTECTED_REGION, protected=True)
    unprotected = command(ctx, "found_outpost", region_id=UNPROTECTED_REGION, protected=False)
    metric_is(ctx, "metric outposts_alive after founding", "outposts_alive", 2)
    metric_is(ctx, "metric trade_value after founding", "trade_value", protected["trade_value"] + unprotected["trade_value"])
    return protected, unprotected


def check_raid_reveal(ctx, outpost):
    inside = command(ctx, "reveal", region_id=PROTECTED_REGION, distance=outpost["scouting_range"] - 1)
    outside = command(ctx, "reveal", region_id=PROTECTED_REGION, distance=outpost["scouting_range"] + 1)
    ctx.expect.equals("O1 raid inside the border is seen", inside["sees"], True)
    ctx.expect.equals("O1 raid outside the border is not seen", outside["sees"], False)
    target = command(ctx, "raid_target")
    ctx.expect.equals("O2 raiders hit the outpost first", [target["target"], target["region_id"]], ["outpost", PROTECTED_REGION])


def check_lost_outpost(ctx, protected, unprotected):
    lost = command(ctx, "lose_outpost", region_id=PROTECTED_REGION)
    ctx.expect.equals("O3 lost outpost is not alive", lost["alive"], False)
    ctx.expect.equals("O3 lost outpost has no trade value", lost["trade_value"], 0)
    metric_is(ctx, "O3 metric trade_value drops", "trade_value", unprotected["trade_value"])
    ctx.expect.at_most("O3 trade value fell", unprotected["trade_value"], protected["trade_value"] + unprotected["trade_value"] - 1)
    blind = command(ctx, "reveal", region_id=PROTECTED_REGION, distance=0)
    ctx.expect.equals("O3 lost outpost is blind even at distance 0", blind["sees"], False)


def check_unprotected_outpost(ctx):
    before = command(ctx, "outpost", region_id=UNPROTECTED_REGION)
    ctx.expect.equals("O4 flags are off at the start", [before["tribute_to_invader"], before["leaks_intel"]], [False, False])
    record = ctx.time.run_game_days(WAIT_DAYS, speed=SPEED)
    ctx.expect.at_least("O4 game days passed", record["days_end"] - record["days_start"], WAIT_DAYS)
    after = command(ctx, "outpost", region_id=UNPROTECTED_REGION)
    ctx.expect.equals("O4 unprotected outpost pays tribute", after["tribute_to_invader"], True)
    ctx.expect.equals("O4 unprotected outpost leaks intel", after["leaks_intel"], True)
    metric_is(ctx, "O4 metric leaked", "leaked", 1)


def check_evacuation(ctx):
    home_before = command(ctx, "region_stock", region_id=HOME_REGION)
    fallback_before = command(ctx, "region_stock", region_id=UNPROTECTED_REGION)
    answer = command(ctx, "evacuate", from_region=HOME_REGION, to_region=UNPROTECTED_REGION, families=5, grain=50)
    ctx.expect.equals("S4 home lost 5 families", home_before["families"] - answer["from"]["families"], 5)
    ctx.expect.equals("S4 home lost 50 grain", home_before["grain"] - answer["from"]["grain"], 50)
    ctx.expect.equals("S4 fallback got 5 families", answer["to"]["families"] - fallback_before["families"], 5)
    ctx.expect.equals("S4 fallback got 50 grain", answer["to"]["grain"] - fallback_before["grain"], 50)
    ctx.expect.equals("S4 stock read back at home", command(ctx, "region_stock", region_id=HOME_REGION), answer["from"])
    ctx.expect.equals("S4 stock read back at the fallback", command(ctx, "region_stock", region_id=UNPROTECTED_REGION), answer["to"])
    refusal = ctx.mod.refusal(PREFIX + "evacuate", from_region=HOME_REGION, to_region=PROTECTED_REGION, families=1, grain=0)
    ctx.expect.equals("S4 evacuation to a lost outpost is refused", refusal is not None, True)


def run(ctx) -> dict:
    check_commands_are_listed(ctx)
    protected, unprotected = found_outposts(ctx)
    check_raid_reveal(ctx, protected)
    check_lost_outpost(ctx, protected, unprotected)
    check_unprotected_outpost(ctx)
    check_evacuation(ctx)
    return ctx.result()
