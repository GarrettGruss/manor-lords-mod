"""Refugee waves (spec 15, issue #51): the mod RefugeeWaves sends a wave, the player houses it, a second wave turns into a raid.

Needs the mod RefugeeWaves (the real mod, not a stand-in) and fixture `base`. It proves the feature criteria of spec 15:
  "a named command starts a wave without the mouse; +N homeless families" (phase 1),
  "approval falls while the wave is homeless, and the wave ends when the player builds homes" (phase 1),
  "the rebellion starts when the timer ends" (phase 2).
COVERS stays empty: the criteria ids of spec 10 do not include the criteria of spec 15.
"""

from runlib import plotgeom

NAME = "refugee-wave"
DESCRIPTION = ("Phase 1: force a wave (RefugeeWaves.start_wave), check families, homeless and approval, build 5 burgage plots without "
               "the mouse, the wave ends housed. Phase 2: a second wave, a short timer, half of the homeless families turn into a raid.")
LIMIT_S = 900
LONG_REASON = "Phase 1 waits for a plot build (about 12 game days); phase 2 waits for the timer. Speed 3 is 8x."
COVERS = []
SPEED = 3
TIMBER = 16
TIMBER_AMOUNT = 60
PLOT_COUNT = 5
BUILD_DAYS_LIMIT = 24
PHASE2_TIMER_DAYS = 3
PHASE2_DAYS_LIMIT = 8
PREFIX = "RefugeeWaves."


def region_numbers(ctx) -> dict:
    return ctx.actions.housing_state()["region"]


def mod_check(ctx) -> dict:
    return ctx.mod.command(PREFIX + "check")


def place_plots(ctx) -> None:
    actions = ctx.actions
    spots = actions.tent_find_spot()
    spot, centre = spots["spots"][0], spots["centre"]
    plots = plotgeom.make_plots(spot["x"], spot["y"], spot["z"], spot["x"] - centre["x"], spot["y"] - centre["y"], PLOT_COUNT)
    actions.give_item(TIMBER, TIMBER_AMOUNT)
    actions.open_burgage_tool()
    actions.plot_field_place(plots)
    actions.commit_plots()


def phase_one(ctx) -> None:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "configure", chance_percent=0, homeless_days_limit=1000, approval_floor=0, adopt_on_start=False)
    ctx.time.run_game_days(1, speed=SPEED)
    before = region_numbers(ctx)
    mod_check(ctx)
    expect.equals("P1 no wave before the command", ctx.mod.metric(PREFIX + "wave_active"), False)

    answer = ctx.mod.command(PREFIX + "start_wave", calls=1)
    after = region_numbers(ctx)
    expect.in_range("P1 families rose by one call", after["families"] - before["families"], 3, 6)
    expect.in_range("P1 homeless families appeared", after["homeless"] - before["homeless"], 1, 5)
    expect.equals("P1 wave is active", ctx.mod.metric(PREFIX + "wave_active"), True)
    ctx.log.info(f"P1 wave: {answer} before={before} after={after}")

    low = after["approval"]
    for _ in range(4):
        ctx.time.run_game_days(1, speed=SPEED)
        low = min(low, region_numbers(ctx)["approval"])
        mod_check(ctx)
    expect.at_least("P1 approval fell while homeless", before["approval"] - low, 3)
    expect.equals("P1 wave still active while homeless", ctx.mod.metric(PREFIX + "wave_active"), True)

    place_plots(ctx)
    for _ in range(BUILD_DAYS_LIMIT):
        ctx.time.run_game_days(1, speed=SPEED)
        if mod_check(ctx)["active"] is False:
            break
    final = region_numbers(ctx)
    expect.equals("P1 wave ended housed", ctx.mod.metric(PREFIX + "last_outcome"), "housed")
    expect.equals("P1 no homeless left", final["homeless"], before["homeless"])
    expect.at_least("P1 approval recovered after housing", final["approval"], low + 2)
    expect.equals("P1 no rebellion", ctx.mod.metric(PREFIX + "rebellions"), 0)


def phase_two(ctx) -> None:
    expect = ctx.expect
    ctx.mod.command(PREFIX + "configure", homeless_days_limit=PHASE2_TIMER_DAYS)
    ctx.mod.command(PREFIX + "start_wave", calls=1)
    start = region_numbers(ctx)
    homeless_wave = start["homeless"]
    expect.at_least("P2 second wave made homeless families", homeless_wave, 1)
    for _ in range(PHASE2_DAYS_LIMIT):
        ctx.time.run_game_days(1, speed=SPEED)
        if mod_check(ctx)["active"] is False:
            break
    outcome = ctx.mod.metric(PREFIX + "last_outcome")
    ctx.log.info(f"P2 outcome {outcome}, wave homeless {homeless_wave}")
    expect.equals("P2 the timer ended in a rebellion", outcome, "rebelled")
    expect.equals("P2 one rebellion counted", ctx.mod.metric(PREFIX + "rebellions"), 1)
    after = region_numbers(ctx)
    expect.in_range("P2 about half of the wave families left", start["families"] - after["families"],
                    max(1, homeless_wave // 2 - 1), homeless_wave // 2 + 2)
    expect.at_least("P2 bandit units appeared", ctx.actions.bandit_state()["bandit_units"], 1)


def run(ctx) -> dict:
    phase_one(ctx)
    phase_two(ctx)
    return ctx.result()
