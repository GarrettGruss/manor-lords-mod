"""Stand-in mod: tiers change size, frequency, variety and targeting over N runs; a warlord returns stronger; the top tier retreats only on leader death (a toy model)."""

import statistics

from raidstandin.client import RaidMod, distinct_units, seed_base_for
from suitelib import stats

NAME = "raid-tiers"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Run seeded two-year raid schedules for each of four tiers (N runs each) and compare size, frequency, unit variety and targeting "
               "with the A/B statistics, report the numbers with ctx.metric for the suite A/B runner, check that an escaped warlord returns "
               "stronger and that the top tier retreats only when the leader dies. Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["D1", "D2", "D3"]

TIERS = (1, 2, 3, 4)
RUNS_PER_TIER = 6
RUN_DAYS = 720
SEEDS_PER_BASE = 10
WARLORD_SEED = 77
WARLORD_BONUS_MIN = 1.4  # two escapes give +50%, and the size is rounded
TOP_TIER = 4
WAIT_DAYS_AT_TOP = 5


def summarize_run(raids):
    sizes = [r["size"] for r in raids]
    return {
        "count": len(raids),
        "mean_size": statistics.fmean(sizes) if sizes else 0.0,
        "variety": [distinct_units(r["composition"]) for r in raids],
        "bait_hits": sum(1 for r in raids if r["bait_hit"]),
    }


def collect(mod, seed_base):
    """The summaries of RUNS_PER_TIER seeded runs for each tier: {tier: [summary]}."""
    return {tier: [summarize_run(mod.auto_run(tier, seed_base * SEEDS_PER_BASE + run, RUN_DAYS)) for run in range(RUNS_PER_TIER)]
            for tier in TIERS}


def column(runs, key):
    return [run[key] for run in runs]


def report_metrics(ctx, runs_by_tier):
    for tier, runs in runs_by_tier.items():
        ctx.metric(f"tier{tier}_mean_size", statistics.fmean(column(runs, "mean_size")))
        ctx.metric(f"tier{tier}_mean_raids", statistics.fmean(column(runs, "count")))


def check_size_and_frequency(ctx, runs_by_tier):
    expect = ctx.expect
    sizes = {tier: column(runs, "mean_size") for tier, runs in runs_by_tier.items()}
    counts = {tier: column(runs, "count") for tier, runs in runs_by_tier.items()}
    expect.equals("D1 every run had raids", min(min(values) for values in counts.values()) >= 1, True)
    medians = [statistics.median(sizes[tier]) for tier in (1, 2, 3)]
    expect.equals("D1 median raid size grows with the tier (1, 2, 3)", medians, sorted(set(medians)))
    for other in (3, TOP_TIER):
        size = stats.compare(sizes[1], sizes[other])
        expect.equals(f"D1 size: tier {other} differs from tier 1", size["verdict"], "different")
        expect.at_least(f"D1 size: tier {other} is bigger than tier 1 (relative)", size["rel_diff"], 0.5)
        count = stats.compare(counts[1], counts[other])
        expect.equals(f"D1 frequency: tier {other} differs from tier 1", count["verdict"], "different")
        expect.at_least(f"D1 frequency: tier {other} has more raids than tier 1 (relative)", count["rel_diff"], 0.3)


def check_variety_and_targeting(ctx, runs_by_tier):
    expect = ctx.expect
    for tier, runs in runs_by_tier.items():
        varieties = {v for run in runs for v in run["variety"]}
        expect.equals(f"D1 variety: tier {tier} raids have {tier} unit types", varieties, {tier})
    low_raids = sum(run["count"] for run in runs_by_tier[1])
    low_hits = sum(run["bait_hits"] for run in runs_by_tier[1])
    expect.at_most("D1 targeting: tier 1 hits the bait stockpile only by chance", low_hits / low_raids, 0.8)
    for tier in (2, 3, TOP_TIER):
        runs = runs_by_tier[tier]
        expect.equals(f"D1 targeting: tier {tier} always hits the nearest high value stockpile",
                      sum(column(runs, "bait_hits")), sum(column(runs, "count")))


def plan_with_seed(mod):
    """Plan a raid with a fixed seed, so the size noise is the same. Return the planned raid."""
    mod("configure", seed=WARLORD_SEED)
    return mod("set_timer", days=2)


def let_leader_escape(mod):
    mod("advance_days", days=2)
    return mod("fill_loot")


def check_warlord(ctx, mod):
    expect = ctx.expect
    mod.start(tier=3)
    base = plan_with_seed(mod)
    mod("cancel_raid")
    expect.equals("D2 a new warlord starts at level 0", base["warlord_level"], 0)
    for level in (1, 2):
        plan_with_seed(mod)
        ended = let_leader_escape(mod)
        expect.equals(f"D2 the leader escapes (retreat {level})", ended["leader_alive"], True)
        expect.equals(f"D2 the warlord level is {level}", mod("settlement")["warlord_level"], level)
    returned = plan_with_seed(mod)
    expect.equals("D2 the returning raid carries the warlord level", returned["warlord_level"], 2)
    expect.at_least("D2 the returning raid is stronger (same seed, ratio)", returned["size"] / base["size"], WARLORD_BONUS_MIN)
    mod("advance_days", days=2)
    ended = mod("kill_leader")
    expect.equals("D2 the leader dies", ended["retreat_reason"], "leader_dead")
    expect.equals("D2 a dead warlord is gone", mod("settlement")["warlord_level"], 0)
    expect.equals("D2 the next raid is as weak as the first", plan_with_seed(mod)["size"], base["size"])


def check_top_tier(ctx, mod):
    expect = ctx.expect
    active = mod.arrive(tier=TOP_TIER)
    expect.equals("D3 the top tier raid has no breaking point", active["breaking_point"], 0)
    for label, force in (("full loot", lambda: mod("fill_loot")), ("timer end", lambda: mod("expire_timer")),
                         ("morale at zero", lambda: mod("damage_morale", amount=active["morale"]))):
        expect.equals(f"D3 {label} does not make the top tier retreat", force()["state"], "active")
    mod("advance_days", days=WAIT_DAYS_AT_TOP)
    expect.equals("D3 the top tier raid stays for days", mod("current_raid")["state"], "active")
    ended = mod("kill_leader")
    expect.equals("D3 the dead leader makes it retreat", (ended["state"], ended["retreat_reason"]), ("ended", "leader_dead"))
    mod.arrive(tier=TOP_TIER - 1)
    expect.equals("D3 a lower tier retreats on full loot", mod("fill_loot")["retreat_reason"], "full_loot")


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    runs_by_tier = collect(mod, seed_base_for(ctx))
    report_metrics(ctx, runs_by_tier)
    check_size_and_frequency(ctx, runs_by_tier)
    check_variety_and_targeting(ctx, runs_by_tier)
    check_warlord(ctx, mod)
    check_top_tier(ctx, mod)
    return ctx.result()
