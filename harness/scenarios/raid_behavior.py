"""Stand-in mod: each raid has one objective and one breaking point, forced retreat triggers work, and bait is chosen as target (a toy model)."""

from raidstandin.client import OBJECTIVES, RETREAT_REASONS, RaidMod, seed_base_for

NAME = "raid-behavior"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Read the per-raid state log, force each retreat trigger (full loot, morale break, timer end, leader dead) and watch the "
               "state change, and place a bait stockpile to see that raiders choose it. Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["R1", "R4", "R6"]

LOG_TIER = 3
LOG_DAYS = 720
MIN_LOGGED_RAIDS = 4
RETREAT_TIER = 3
BAIT_ID = 5
BAIT_DISTANCE = 3
BAIT_STOCK = 500
SPENT_BAIT_STOCK = 99
HIGH_VALUE_ID = 2  # the nearest stockpile with at least 100 stock in the start state


def check_one_objective_and_one_breaking_point(ctx, mod, seed_base):
    expect = ctx.expect
    raids = mod.auto_run(LOG_TIER, seed_base, LOG_DAYS)
    expect.at_least("R1 the state log holds raids", len(raids), MIN_LOGGED_RAIDS)
    bad_objective = [r["id"] for r in raids if r["objective"] != OBJECTIVES[r["faction"]]]
    expect.equals("R1 each raid has exactly one objective of its faction", bad_objective, [])
    bad_point = [r["id"] for r in raids if isinstance(r["breaking_point"], bool) or not isinstance(r["breaking_point"], (int, float))]
    expect.equals("R1 each raid has one numeric breaking point", bad_point, [])
    expect.equals("R1 each logged raid has ended with a known reason",
                  [r["id"] for r in raids if r["state"] != "ended" or r["retreat_reason"] not in RETREAT_REASONS], [])
    expect.equals("R1 each raid has its own id", len({r["id"] for r in raids}), len(raids))


def check_trigger(ctx, mod, label, force, reason):
    expect = ctx.expect
    active = mod.arrive(tier=RETREAT_TIER)
    expect.equals(f"R4 {label}: the raid is active before the trigger", (active["state"], active["retreat_reason"]), ("active", ""))
    result = force(active)
    expect.equals(f"R4 {label}: the raid retreats", result["state"], "ended")
    expect.equals(f"R4 {label}: the reason is {reason}", result["retreat_reason"], reason)
    expect.equals(f"R4 {label}: no raid is active afterwards", mod("current_raid")["state"], "none")
    expect.equals(f"R4 {label}: the metric raid_active is false", mod.metric("raid_active"), False)


def check_retreat_triggers(ctx, mod):
    check_trigger(ctx, mod, "full loot", lambda raid: mod("fill_loot"), "full_loot")
    check_trigger(ctx, mod, "morale break", lambda raid: mod("damage_morale", amount=raid["morale"] - raid["breaking_point"]), "morale_break")
    check_trigger(ctx, mod, "timer end", lambda raid: mod("expire_timer"), "timer_end")
    check_trigger(ctx, mod, "leader dead", lambda raid: mod("kill_leader"), "leader_dead")


def check_no_retreat_just_above_the_breaking_point(ctx, mod):
    active = mod.arrive(tier=RETREAT_TIER)
    near = mod("damage_morale", amount=active["morale"] - active["breaking_point"] - 1)
    ctx.expect.equals("R4 one point above the breaking point the raid stays", near["state"], "active")
    mod("kill_leader")


def next_raid_target(mod):
    mod("set_timer", days=2, faction="cuman")
    mod("advance_days", days=2)
    raid = mod("current_raid")
    mod("expire_timer")
    return raid


def check_bait(ctx, mod):
    expect = ctx.expect
    mod.start(tier=2)
    mod("set_day", day=100)
    before = mod("stockpiles")
    expect.equals("R6 the nearest high value stockpile is known", before["nearest_high_value"], HIGH_VALUE_ID)
    expect.equals("R6 raiders choose the nearest high value stockpile", next_raid_target(mod)["target"], HIGH_VALUE_ID)
    placed = mod("set_stockpile", id=BAIT_ID, distance=BAIT_DISTANCE, stock=BAIT_STOCK)
    expect.equals("R6 the bait becomes the nearest high value stockpile", placed["nearest_high_value"], BAIT_ID)
    baited = next_raid_target(mod)
    expect.equals("R6 raiders go for the bait", (baited["target"], baited["bait_hit"]), (BAIT_ID, True))
    mod("set_stockpile", id=BAIT_ID, distance=BAIT_DISTANCE, stock=SPENT_BAIT_STOCK)
    expect.equals("R6 a spent bait (stock under 100) is ignored", next_raid_target(mod)["target"], HIGH_VALUE_ID)
    expect.at_least("R6 the metric bait_hits counts them", mod.metric("bait_hits"), 3)


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    check_one_objective_and_one_breaking_point(ctx, mod, seed_base_for(ctx))
    check_retreat_triggers(ctx, mod)
    check_no_retreat_just_above_the_breaking_point(ctx, mod)
    check_bait(ctx, mod)
    return ctx.result()
