"""Stand-in mod: tribute offers of each kind and their effects over game days (a toy model)."""

NAME = "standin-tribute"
DESCRIPTION = ("Stand-in mod: a toy model that proves the harness method, not the real mod. "
               "Offer and accept a payment, hostages and vassalage, then run game days and check the yearly tribute. "
               "Needs the mods InvasionStandIn and HarnessActions.")
LIMIT_S = 120
COVERS = ["S5"]

PREFIX = "InvasionStandIn."
PAYMENT = 100
HOSTAGES = 4
YEARLY = 50
YEAR_DAYS = 2  # a short toy year, so a few game days hold two ticks
WAIT_DAYS = 5
SPEED = 3
TELEMETRY_WAIT_S = 20


def command(ctx, name, **args):
    return ctx.mod.command(PREFIX + name, **args)


def check_payment(ctx, start):
    expect = ctx.expect
    offered = command(ctx, "offer_tribute", kind="payment", amount=PAYMENT)
    expect.equals("S5 the offer is pending", offered["pending"], "payment")
    expect.equals("S5 a second offer is refused", ctx.mod.refusal(PREFIX + "offer_tribute", kind="hostages", amount=1) is not None, True)
    accepted = command(ctx, "accept_tribute")
    expect.equals("S5 the payment left the treasury", start["treasury"] - accepted["treasury"], PAYMENT)
    expect.equals("S5 the payment is counted", accepted["paid_total"] - start["paid_total"], PAYMENT)
    expect.eventually("S5 metric tribute_paid shows the payment",
                      lambda: ctx.mod.metric(PREFIX + "tribute_paid", None) == accepted["paid_total"], TELEMETRY_WAIT_S)
    return accepted


def check_unaffordable_payment(ctx):
    command(ctx, "offer_tribute", kind="payment", amount=100000)
    ctx.expect.equals("S5 a payment above the treasury is refused", ctx.mod.refusal(PREFIX + "accept_tribute") is not None, True)
    rejected = command(ctx, "reject_tribute")
    ctx.expect.equals("S5 a rejected offer is gone", rejected["pending"], "none")


def check_hostages(ctx, before):
    command(ctx, "offer_tribute", kind="hostages", amount=HOSTAGES)
    accepted = command(ctx, "accept_tribute")
    ctx.expect.equals("S5 hostages are given", accepted["hostages_given"] - before["hostages_given"], HOSTAGES)
    ctx.expect.equals("S5 hostages cost no silver", accepted["treasury"], before["treasury"])
    return accepted


def check_vassalage(ctx, before):
    expect = ctx.expect
    command(ctx, "offer_tribute", kind="vassal", amount=YEARLY)
    accepted = command(ctx, "accept_tribute")
    expect.equals("S5 the town is a vassal", accepted["vassal"], True)
    expect.equals("S5 nothing is paid on the day of the oath", accepted["paid_total"], before["paid_total"])
    record = ctx.time.run_game_days(WAIT_DAYS, speed=SPEED)
    passed = record["days_end"] - record["days_start"]
    expect.at_least("S5 game days passed", passed, WAIT_DAYS)
    after = command(ctx, "tribute")
    # The run may pass a little more than WAIT_DAYS, so the expected number of ticks comes from the days that passed.
    expect.equals("S5 yearly tribute was paid once for each toy year", after["years_paid"], passed // YEAR_DAYS)
    expect.equals("S5 the treasury fell by the tribute", before["treasury"] - after["treasury"], after["years_paid"] * YEARLY)
    expect.eventually("S5 metric tribute_paid shows the yearly tribute",
                      lambda: ctx.mod.metric(PREFIX + "tribute_paid", None) == after["paid_total"], TELEMETRY_WAIT_S)


def run(ctx) -> dict:
    command(ctx, "reset")
    command(ctx, "set_year_days", days=YEAR_DAYS)
    start = command(ctx, "tribute")
    after_payment = check_payment(ctx, start)
    check_unaffordable_payment(ctx)
    after_hostages = check_hostages(ctx, after_payment)
    check_vassalage(ctx, after_hostages)
    return ctx.result()
