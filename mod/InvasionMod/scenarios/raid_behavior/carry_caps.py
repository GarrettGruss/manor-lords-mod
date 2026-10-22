"""Change add-raid-carry-caps: a real Hussite (lord) raid stays under its carry cap and leaves.

Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1). The raid is a small forced raid.
It runs game days until the raid leaves, then checks the plundered goods against carry_cap times the raiders at the start,
the cap in the tracker state and the leave reason. It saves nothing.
"""

NAME = "raid-behavior-carry-caps"
DESCRIPTION = "A Hussite raid plunders at most carry_cap goods per raider and leaves with a known reason."
LIMIT_S = 1200
SPEED = 3
LONG_REASON = "A raid leaves after up to 25 game days. At speed 3 this takes up to 300 s plus the start."
DAY_LIMIT = 40
REASONS = ("loot", "losses", "time")


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.raid_behavior_state")


def tracker(ctx) -> dict:
    raids = state(ctx)["raids"]
    return raids[0] if raids else {}


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
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    raid = tracker(ctx)
    ctx.check("the raid is a Hussite lord raid", raid.get("lord_raid") is True and raid.get("raid_type") == "hussite", raid)
    ctx.run_until(lambda: tracker(ctx)["initial"] > 0, 30, what="the raiders at the start")
    initial = tracker(ctx)["initial"]
    cap = state(ctx)["carry_cap"]

    days = 0
    peak_plundered = 0
    while raid["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
        raid = tracker(ctx)
        peak_plundered = max(peak_plundered, raid["plundered"])
        ctx.log.info(f"day {days}: {raid}")
    ctx.check("the raid left within the day limit", raid["state"] == "left", [raid["state"], days])
    ctx.check("the leave reason is loot, losses or time", raid.get("leave_reason") in REASONS, raid.get("leave_reason"))
    ctx.check("the state shows the cap that was used", cap == 10 and raid.get("carry_cap") in (None, cap), [cap, raid.get("carry_cap")])
    limit = cap * initial
    ctx.check("plundered goods are at most carry_cap times the raiders at the start", raid["plundered"] <= limit, [raid["plundered"], limit])
    ctx.check("the raid plundered something", raid["plundered"] > 0, raid["plundered"])
    if raid.get("leave_reason") == "loot":
        ctx.check("a loot leave happens only when the cap is reached", raid["plundered"] >= limit, [raid["plundered"], limit])
    ctx.metric("days", days)
    ctx.metric("initial", initial)
    ctx.metric("plundered", raid["plundered"])
    ctx.metric("plunder_limit", limit)
    ctx.metric("carry_cap", cap)
    ctx.log.info(f"leave reason: {raid.get('leave_reason')}")
    return ctx.result()
