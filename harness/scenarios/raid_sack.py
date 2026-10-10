"""Stand-in mod: the run continues after one sack, and repeated sacks inside the window are fatal (a toy model)."""

from raidstandin.client import RaidMod

NAME = "raid-sack"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Sack the settlement once and check that the run continues, sack it again inside the window and check the game over state, "
               "and sack it twice with the window between them. Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["S2", "S3"]

WINDOW_DAYS = 360
INSIDE_DAYS = 100
WAIT_AFTER_SACK_DAYS = 10
RAID_TIMER_DAYS = 3


def check_first_sack_is_survivable(ctx, mod):
    expect = ctx.expect
    mod.start()
    before = mod("settlement")
    after = mod("sack")
    expect.equals("S2 one sack is counted", after["sacks_in_window"], 1)
    expect.equals("S2 no game over after one sack", after["game_over"], False)
    expect.equals("S2 the sack took food", after["food"] < before["food"], True)
    day = mod("clock")["day"]
    expect.equals("S2 the clock goes on", mod("advance_days", days=WAIT_AFTER_SACK_DAYS)["day"], day + WAIT_AFTER_SACK_DAYS)
    mod("set_timer", days=RAID_TIMER_DAYS)
    mod("advance_days", days=RAID_TIMER_DAYS)
    expect.equals("S2 the raid director still works after a sack", mod("current_raid")["state"], "active")
    expect.equals("S2 the metric game_over is false", mod.metric("game_over"), False)


def check_second_sack_in_window_is_fatal(ctx, mod):
    expect = ctx.expect
    mod.start()
    mod("sack")
    mod("advance_days", days=INSIDE_DAYS)
    after = mod("sack")
    expect.equals("S3 two sacks inside the window are counted", after["sacks_in_window"], 2)
    expect.equals("S3 the second sack is fatal", after["game_over"], True)
    expect.equals("S3 the metric game_over is true", mod.metric("game_over"), True)
    expect.equals("S3 the metric sacks_in_window is 2", mod.metric("sacks_in_window"), 2)
    mod("advance_days", days=WAIT_AFTER_SACK_DAYS)
    expect.equals("S3 the game over state stays", mod("settlement")["game_over"], True)
    expect.equals("S3 a further sack is refused", mod.refusal("sack") is not None, True)


def check_sacks_far_apart_are_forgiven(ctx, mod):
    expect = ctx.expect
    mod.start()
    mod("sack")
    mod("advance_days", days=WINDOW_DAYS)
    after = mod("sack")
    expect.equals("S3 the old sack left the window", after["sacks_in_window"], 1)
    expect.equals("S3 both sacks are in the history", after["sacks_total"], 2)
    expect.equals("S3 sacks a window apart are not fatal", after["game_over"], False)


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    check_first_sack_is_survivable(ctx, mod)
    check_second_sack_in_window_is_fatal(ctx, mod)
    check_sacks_far_apart_are_forgiven(ctx, mod)
    return ctx.result()
