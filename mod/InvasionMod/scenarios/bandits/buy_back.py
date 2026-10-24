"""M04 iteration 03, C1 to C7 and C9: the player pays silver and the converted families come back.

The conversion is forced (bandits_leave_now). The buy-back uses the native settle letter through the named command.
C6 (no free home slot) cannot be made in the real game without building changes, so it is covered by the fake game tests.
It saves nothing.
"""

from runlib.units import side_count

NAME = "bandits-buy-back"
LIMIT_S = 600
SPEED = 2
LONG_REASON = "Several waits of 40 to 60 game seconds and 5 game days at speed 2, plus the start."
PRICE_PER_FAMILY = 10


def state(ctx) -> dict:
    return ctx.mod.command("InvasionMod.bandits_state")


def bandits(ctx) -> int:
    return side_count(ctx.actions.units_census(), "bandit")


def unchanged(before: dict, after: dict) -> bool:
    keys = ("silver", "families", "outstanding_families", "free_slots")
    return all(before[key] == after[key] for key in keys)


def check_refusals(ctx) -> None:
    before = state(ctx)
    answer = ctx.mod.command("InvasionMod.bandits_buy_back")
    ctx.check("C7 refused with nothing outstanding", answer["accepted"] is False and "no families" in answer["reason"], answer)
    ctx.check("C7 nothing changed", unchanged(before, state(ctx)), [before, state(ctx)])

    ctx.mod.command("InvasionMod.bandits_leave_now", count=2)
    ctx.run_until(lambda: state(ctx)["outstanding_families"] == 2, 20, what="the conversion")
    ctx.time.run_game_seconds(10, speed=SPEED)
    ctx.actions.set_silver(5)
    poor = state(ctx)
    units = bandits(ctx)
    answer = ctx.mod.command("InvasionMod.bandits_buy_back")
    ctx.check("C5 refused when silver is short", answer["accepted"] is False and "silver" in answer["reason"], answer)
    ctx.check("C5 silver, families and outstanding families did not change", unchanged(poor, state(ctx)), [poor, state(ctx)])
    ctx.check("C5 bandit units did not change", bandits(ctx) == units, [units, bandits(ctx)])


def run(ctx) -> dict:
    check_refusals(ctx)
    ctx.actions.set_silver(100)
    before = state(ctx)
    units_before = bandits(ctx)
    ctx.check("setup: 2 families outstanding and a free home", before["outstanding_families"] == 2 and before["free_slots"] >= 1, before)
    expected = min(before["outstanding_families"], before["free_slots"])
    price = expected * PRICE_PER_FAMILY

    answer = ctx.mod.command("InvasionMod.bandits_buy_back")
    ctx.check("the buy-back is accepted at the price rule", answer["accepted"] is True and answer["price"] == price, answer)
    ctx.time.run_game_seconds(40, speed=SPEED)
    for _ in range(8):  # the mod waits in game time; a failed deal ends after 120 game seconds
        if not state(ctx)["buy_back_pending"]:
            break
        ctx.time.run_game_seconds(30, speed=SPEED)
    ctx.run_until(lambda: not state(ctx)["buy_back_pending"], 30, what="the buy-back result")
    ctx.time.run_game_seconds(30, speed=SPEED)
    after = state(ctx)
    gain = after["families"] - before["families"]
    ctx.check("C3 bandit units went down", bandits(ctx) < units_before, [units_before, bandits(ctx)])
    ctx.check("C3 no bandit units are left", bandits(ctx) == 0, bandits(ctx))
    ctx.check("the mod recorded the result", len(after["buy_backs"]) == 1 and after["buy_backs"][0]["family_gain"] == gain, after["buy_backs"])
    # The game brings families back only some of the time (spike S1: 12 of 15 first letters). Both outcomes must be consistent.
    worked = gain >= 1
    if worked:
        ctx.check("C1 silver went down by exactly the price", before["silver"] - after["silver"] == price, [before["silver"], after["silver"], price])
        ctx.check("C2 families came back (1 to the free slots)", gain <= before["free_slots"], [before["families"], after["families"], before["free_slots"]])
        ctx.check("C4 outstanding families went down by the families returned",
                  after["outstanding_families"] == before["outstanding_families"] - expected, after)
    else:
        ctx.check("C10 a failed deal gives the silver back", after["silver"] == before["silver"], [before["silver"], after["silver"]])
        ctx.check("C10 a failed deal keeps the families outstanding", after["outstanding_families"] == before["outstanding_families"], after)
        ctx.check("C10 the result says what was refunded", after["buy_backs"][0]["refunded"] == price, after["buy_backs"])
    ctx.metric("deal_worked", 1 if worked else 0)

    ctx.time.run_game_days(5, speed=SPEED)
    final = state(ctx)
    ctx.check("C9 the game runs 5 days after the buy-back", final["day"] >= after["day"] + 5, [after["day"], final["day"]])
    ctx.metric("price", price)
    ctx.metric("family_gain", gain)
    ctx.metric("silver_paid", before["silver"] - after["silver"])
    ctx.metric("free_slots_before", before["free_slots"])
    return ctx.result()
