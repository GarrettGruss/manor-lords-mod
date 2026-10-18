"""M06 iteration 02, B2 to B4 and B6: the player accepts the terms of a lord raid and the raid leaves without a sack.

Options (run.py --env): INVASION_DIFFICULTY (1 to 3, default 1), TERMS_KIND (payment or vassalage, default payment). It saves nothing.
"""

NAME = "sack-and-terms-pay-terms"
DESCRIPTION = "Accepting terms (payment or vassalage) makes a role raid leave with reason terms; no sack."
LIMIT_S = 300
SPEED = 3
DAY_LIMIT = 6
PAYMENT_BASE = 100
START_SILVER = 1000


def tracker(ctx) -> dict:
    raids = ctx.mod.command("InvasionMod.raid_behavior_state")["raids"]
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
    kind = ctx.variant_option("TERMS_KIND", "payment")
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    ctx.mod.command("InvasionMod.invasion_set_size", size="small")
    ctx.actions.set_silver(START_SILVER)
    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: bool(tracker(ctx)), 30, what="the raid record")
    if ctx.mod.command("InvasionMod.terms_state")["state"] != 1:
        ctx.mod.command("InvasionMod.terms_offer")
    offer = ctx.mod.command("InvasionMod.terms_state")["offer"]
    ctx.check("B1 the payment is 100 x difficulty", offer["payment"] == PAYMENT_BASE * difficulty, offer)

    before = ctx.mod.command("InvasionMod.terms_state")
    answer = ctx.mod.command("InvasionMod.terms_accept", kind=kind)
    paid = before["silver"] - answer["silver_after"]
    expected = offer["payment"] if kind == "payment" else 0
    ctx.check("B2 the silver paid is exact", paid == expected, [before["silver"], answer["silver_after"], expected])
    days = 0
    while tracker(ctx)["state"] == "active" and days < DAY_LIMIT:
        run_day(ctx)
        days += 1
    raid = tracker(ctx)
    ctx.check("B2 the raid left with reason terms", raid["state"] == "left" and raid.get("leave_reason") == "terms", [raid["state"], raid.get("leave_reason"), days])
    sack = ctx.mod.command("InvasionMod.sack_state")
    ctx.check("B2 no sack", sack["sack_count"] == 0, sack["sack_count"])
    terms = ctx.mod.command("InvasionMod.terms_state")
    if kind == "vassalage":
        ctx.check("B4 vassal state with a tribute day", terms["state"] == 3 and terms["next_tribute_day"] > terms["day"], terms)
    else:
        ctx.check("B2 paid state", terms["state"] == 2 and terms["paid_total"] == expected, terms)
    population = ctx.mod.command("InvasionMod.raid_behavior_state")["population"]
    ctx.check("B6 the village still has people", population is not None and population > 0, population)
    ctx.metric("days_to_leave", days)
    ctx.metric("silver_paid", paid)
    return ctx.result()
