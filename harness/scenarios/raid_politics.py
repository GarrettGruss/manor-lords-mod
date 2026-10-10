"""Stand-in mod: laws and pacts have costs and benefits, fear and hope follow the threat, and the war economy shifts workers (a toy model)."""

from raidstandin.client import RaidMod

NAME = "raid-politics"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Enact laws and a pact and check silver, defense and raid size, read the morale meter against the toy clock while a raid is "
               "announced and after it, and toggle the war economy to see workers, defense and food change. "
               "Needs the mods RaidStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["P1", "P2", "P4"]

CONSCRIPTION_COST = 100
CONSCRIPTION_DEFENSE = 20
CONSCRIPTION_FOOD = 3
TITHE_SILVER_PER_DAY = 5
TITHE_DAYS = 10
PACT_SEED = 9
PACT_RATIO_RANGE = (0.35, 0.65)
MORALE_STEPS = 6
STEP_DAYS = 2
WAR_SHIFT = 10
RAID_TIMER_DAYS = 20
RAID_ARRIVAL_REST_DAYS = RAID_TIMER_DAYS - MORALE_STEPS * STEP_DAYS
REPEL_HOPE = 10


def check_conscription(ctx, mod):
    expect = ctx.expect
    mod.start()
    before = mod("settlement")
    after = mod("enact", law="conscription")
    expect.equals("P1 conscription costs silver", before["silver"] - after["silver"], CONSCRIPTION_COST)
    expect.equals("P1 conscription adds defense", after["defense"] - before["defense"], CONSCRIPTION_DEFENSE)
    expect.equals("P1 conscription costs food each day", after["food_use"] - before["food_use"], CONSCRIPTION_FOOD)
    expect.equals("P1 the metric defense follows", mod.metric("defense"), after["defense"])
    expect.equals("P1 a law cannot be enacted twice", mod.refusal("enact", law="conscription") is not None, True)
    expect.equals("P1 a repeal removes the benefit", mod("repeal", law="conscription")["defense"], before["defense"])


def morale_after_one_day(mod, with_law):
    mod.arrive(tier=2)
    if with_law:
        mod("enact", law="conscription")
    mod("advance_days", days=1)
    return mod("current_raid")["morale"]


def check_defense_hurts_raiders(ctx, mod):
    plain = morale_after_one_day(mod, with_law=False)
    drilled = morale_after_one_day(mod, with_law=True)
    ctx.expect.at_least("P1 more defense drains more raider morale", plain - drilled, 1)


def check_tithe(ctx, mod):
    expect = ctx.expect
    mod.start()
    before = mod("settlement")
    mod("enact", law="tithe")
    mod("advance_days", days=TITHE_DAYS)
    after = mod("settlement")
    expect.equals("P1 the tithe gives silver each day", after["silver"] - before["silver"], TITHE_SILVER_PER_DAY * TITHE_DAYS)
    expect.equals("P1 the metric silver follows", mod.metric("silver"), after["silver"])


def planned_size(mod, with_pact, faction):
    mod.start(tier=3, seed=PACT_SEED)
    if with_pact:
        mod("enact", law="cuman_pact")
    return mod("set_timer", days=3, faction=faction)["size"]


def check_pact(ctx, mod):
    expect = ctx.expect
    open_size, pact_size = planned_size(mod, False, "cuman"), planned_size(mod, True, "cuman")
    expect.in_range("P1 the cuman pact cuts cuman raid size (ratio)", pact_size / open_size, *PACT_RATIO_RANGE)
    expect.equals("P1 the cuman pact leaves norse raids alone", planned_size(mod, True, "norse"), planned_size(mod, False, "norse"))
    mod.start()
    for _ in range(2):  # a repeal gives no refund, so the silver runs out
        mod("enact", law="cuman_pact")
        mod("repeal", law="cuman_pact")
    expect.equals("P1 a law the town cannot pay is refused", mod.refusal("enact", law="cuman_pact") is not None, True)


def read_morale_series(mod, steps):
    series = [mod.metric("town_morale")]
    for _ in range(steps):
        mod("advance_days", days=STEP_DAYS)
        series.append(mod.metric("town_morale"))
    return series


def check_morale_follows_threat(ctx, mod):
    expect = ctx.expect
    mod.start(tier=4, announce_days=30)  # a top tier raid stays, so the threat lasts
    mod("advance_days", days=STEP_DAYS)
    calm = read_morale_series(mod, MORALE_STEPS)
    expect.equals("P2 hope grows while no raid is announced", calm, sorted(calm))
    mod("set_timer", days=RAID_TIMER_DAYS)
    fear = read_morale_series(mod, MORALE_STEPS)
    expect.equals("P2 fear grows while a raid is announced", fear, sorted(fear, reverse=True))
    expect.at_least("P2 the morale fell with the threat", fear[0] - fear[-1], MORALE_STEPS * STEP_DAYS)
    mod("advance_days", days=RAID_ARRIVAL_REST_DAYS)
    expect.equals("P2 the raid has arrived", mod.metric("raid_active"), True)
    before_repel = mod.metric("town_morale")
    mod("kill_leader")
    expect.equals("P2 repelling the raid gives hope", mod.metric("town_morale") - before_repel, REPEL_HOPE)
    hope = read_morale_series(mod, MORALE_STEPS)
    expect.equals("P2 hope returns after the threat", hope, sorted(hope))
    window = ctx.mod.metrics_window(["RaidStandIn.town_morale"])
    expect.at_least("P2 the harness kept the morale reads against the clock", len(window), 3 * (MORALE_STEPS + 1))


def check_war_economy(ctx, mod):
    expect = ctx.expect
    mod.start()
    before = mod("settlement")
    on = mod("set_war_economy", on=True)
    expect.equals("P4 farmers move to the military", (before["workers"]["farming"] - on["workers"]["farming"],
                                                      on["workers"]["military"] - before["workers"]["military"]), (WAR_SHIFT, WAR_SHIFT))
    expect.equals("P4 the number of workers stays", sum(on["workers"].values()), sum(before["workers"].values()))
    expect.equals("P4 the metric workers_farming follows", mod.metric("workers_farming"), on["workers"]["farming"])
    expect.at_least("P4 the war economy adds defense", on["defense"] - before["defense"], 1)
    expect.at_least("P4 the war economy lowers the food income", before["food_income"] - on["food_income"], 1)
    expect.equals("P4 the toggle cannot be set twice", mod.refusal("set_war_economy", on=True) is not None, True)
    expect.equals("P4 switching off restores the workers", mod("set_war_economy", on=False)["workers"], before["workers"])


def run(ctx) -> dict:
    mod = RaidMod(ctx)
    check_conscription(ctx, mod)
    check_defense_hurts_raiders(ctx, mod)
    check_tithe(ctx, mod)
    check_pact(ctx, mod)
    check_morale_follows_threat(ctx, mod)
    check_war_economy(ctx, mod)
    return ctx.result()
