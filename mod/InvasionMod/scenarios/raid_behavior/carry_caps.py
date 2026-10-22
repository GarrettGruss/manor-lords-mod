"""Changes add-raid-carry-caps and fix-native-plunder-test: a real Hussite (lord) raid stays under its carry cap, and the
tracker counts its living raiders like the game unit census.

Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The raid is a small forced raid.
A Hussite raid runs under the baron AI and may end `left` or `destroyed`; there is no day limit besides DAY_LIMIT.
At every sample the tracker count of living raiders must equal the census count. It runs game days until the raid ends, then checks the plundered goods against carry_cap times the raiders at the start,
the cap in the tracker state and the leave reason. It saves nothing.
"""

import time

NAME = "raid-behavior-carry-caps"
DESCRIPTION = "A Hussite raid plunders at most carry_cap goods per raider and leaves with a known reason."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "A raid leaves after up to 25 game days. At speed 3 this takes up to 300 s plus the start."
DAY_LIMIT = 40
REASONS = ("loot", "losses", "time")
SIDES = ("bandit", "ai")
# The census counts a unit by its squad. Other units of the same side (relief, vassals) must not count, so the scenario
# counts only the squads that the spawn made.
SETTLE_S = 2.0  # the tracker looks once a second; a unit can die between the two reads


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_state")


def tracker(ctx) -> dict:
    raids = state(ctx)["raids"]
    return raids[0] if raids else {}


def squad_sizes(ctx) -> dict:
    """Census squad id -> number of living units, for the squads of the sides that a raid can have."""
    census = ctx.actions.units_census()
    return {row["id"]: row["size"] for row in census["squads"] if row["side"] in SIDES}


def run_day(ctx) -> None:
    ctx.popups()
    try:
        ctx.time.run_game_days(1, speed=SPEED)
    except Exception as error:  # TimeControlError: the clock did not move
        ctx.log.info(f"day failed ({error}); closing pop-ups and trying again")
        ctx.popups()
        ctx.time.run_game_days(1, speed=SPEED)


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    known = set(squad_sizes(ctx))
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    raid = tracker(ctx)
    ctx.check("the raid is a Hussite lord raid", raid.get("lord_raid") is True and raid.get("raid_type") == "hussite", raid)
    ctx.run_until(lambda: tracker(ctx)["initial"] > 0, 30, what="the raiders at the start")
    initial = tracker(ctx)["initial"]
    cap = state(ctx)["carry_cap"]
    raid_squads = {key for key in squad_sizes(ctx) if key not in known}  # the squads that the spawn made

    def census_living() -> int:
        sizes = squad_sizes(ctx)
        return sum(sizes.get(key, 0) for key in raid_squads)

    ctx.check("the census counts the raiders of the start", census_living() == initial, [sorted(raid_squads), census_living(), initial])
    mismatches = []

    days = 0
    peak_plundered = 0
    while raid["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        raid = tracker(ctx)
        peak_plundered = max(peak_plundered, raid["plundered"])
        if census_living() != raid["living"]:
            time.sleep(SETTLE_S)
            raid = tracker(ctx)
        if census_living() != raid["living"]:
            mismatches.append([days, raid["living"], census_living()])
        ctx.log.info(f"day {days}: {raid}")
    ctx.check("the tracker living count equals the census count at every sample", not mismatches, mismatches)
    ctx.check("the raid ended left or destroyed within the day limit", raid["state"] in ("left", "destroyed"), [raid["state"], days])
    if raid["state"] == "left":
        ctx.check("a raid that left has a leave reason (loot, losses or time) or ended by its raiders walking off",
                  raid.get("leave_reason") in REASONS or raid["departures"] > 0, [raid.get("leave_reason"), raid["departures"]])
    ctx.check("the state shows the cap that was used", cap == 10 and raid.get("carry_cap") in (None, cap), [cap, raid.get("carry_cap")])
    limit = cap * initial
    ctx.check("plundered goods are at most carry_cap times the raiders at the start", raid["plundered"] <= limit, [raid["plundered"], limit])
    if raid.get("leave_reason") == "loot":
        ctx.check("a loot leave happens only when the cap is reached", raid["plundered"] >= limit, [raid["plundered"], limit])
    ctx.metric("days", days)
    ctx.metric("initial", initial)
    ctx.metric("plundered", raid["plundered"])
    ctx.metric("plunder_limit", limit)
    ctx.metric("carry_cap", cap)
    ctx.metric("census_mismatches", len(mismatches))
    ctx.log.info(f"leave reason: {raid.get('leave_reason')}")
    return ctx.result()
