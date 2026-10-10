"""Stand-in mod: raid timing follows the season rules over three simulated years, and winter pauses fighting (a toy model)."""

from raidstandin.client import ALLOWED_SEASONS, RaidMod, season_of, seed_base_for

NAME = "raid-seasons"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Set the toy day with a command, check the season borders, simulate three years of raids and compare each raid day "
               "with the season rules, then check that winter pauses an active raid and strains the food. "
               "Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["T5", "P6"]

YEARS = 3
YEAR_DAYS = 360
MIN_RAIDS = 5
SEASON_BORDERS = (0, 89, 90, 179, 180, 269, 270, 359, 360, 1079)
WINTER_DAY = 275
PAUSED_DAYS = 20
FOOD_DAYS = 10


def check_season_borders(ctx, mod):
    for day in SEASON_BORDERS:
        got = mod("set_day", day=day)["season"]
        ctx.expect.equals(f"T5 the mod names the season of day {day}", got, season_of(day))


def check_schedule_over_years(ctx, mod, seed_base):
    expect = ctx.expect
    mod("reset")
    mod("configure", tier=2, seed=seed_base, auto=True)
    mod("set_day", day=0)
    mod("advance_days", days=YEARS * YEAR_DAYS)
    raids = mod("raid_log", count=100)["raids"]
    expect.at_least("T5 raids happened in three years", len(raids), MIN_RAIDS)
    wrong = [r["id"] for r in raids if season_of(r["arrival_day"]) not in ALLOWED_SEASONS[r["faction"]]]
    expect.equals("T5 every raid day follows its season rule", wrong, [])
    expect.equals("T5 no raid arrives in winter", [r["id"] for r in raids if season_of(r["arrival_day"]) == "winter"], [])
    expect.equals("T5 the raids arrive on the planned days", [r["id"] for r in raids if r["arrival_day"] != r["planned_day"]], [])
    expect.equals("T5 both factions raid", {r["faction"] for r in raids}, set(ALLOWED_SEASONS))
    years = {r["arrival_day"] // YEAR_DAYS for r in raids}
    expect.equals("T5 every year has a raid", years, set(range(YEARS)))


def check_winter_pauses_fighting(ctx, mod):
    expect = ctx.expect
    mod.start(tier=2, seed=3)
    mod("set_day", day=WINTER_DAY)
    mod("set_timer", days=2, faction="norse")
    mod("advance_days", days=2)
    mod("advance_days", days=PAUSED_DAYS)
    raid = mod("current_raid")
    expect.equals("P6 the raid is still on the field in winter", raid["state"], "active")
    expect.equals("P6 winter pauses fighting: no loot", raid.get("loot"), 0)
    expect.equals("P6 winter pauses fighting: no morale loss", raid.get("morale"), 100)
    expect.equals("P6 the paused days are counted", raid.get("paused_days"), PAUSED_DAYS)
    mod("set_day", day=0)
    mod("advance_days", days=1)
    expect.at_least("P6 spring ends the pause: the raid loots again", mod("current_raid").get("loot"), 1)


def check_winter_strains_food(ctx, mod):
    expect = ctx.expect
    mod("reset")
    mod("set_day", day=100)
    summer = mod("settlement")
    mod("set_day", day=WINTER_DAY)
    winter = mod("settlement")
    expect.at_least("P6 farms give food in summer", summer["food_income"], 1)
    expect.equals("P6 farms give no food in winter", winter["food_income"], 0)
    expect.at_least("P6 the town eats more in winter", winter["food_use"] - summer["food_use"], 1)
    mod("advance_days", days=FOOD_DAYS)
    after = mod("settlement")
    expect.equals("P6 the food falls by the winter use", winter["food"] - after["food"], winter["food_use"] * FOOD_DAYS)
    expect.equals("P6 the metric food shows it", mod.metric("food"), after["food"])


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    seed_base = seed_base_for(ctx)
    check_season_borders(ctx, mod)
    check_schedule_over_years(ctx, mod, seed_base)
    check_winter_pauses_fighting(ctx, mod)
    check_winter_strains_food(ctx, mod)
    return ctx.result()
