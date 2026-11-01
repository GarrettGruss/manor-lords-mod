"""Change update-vassal-tribute-rich-resources: each game month a vassal pays the rich resources of its region.

The scenario adopts two AI-lord regions of the test map as vassals (command `vassals_adopt`): Krumme Leite (internal name immenreuth,
rich stone and salt) and Hochweg (internal name Goldhof, rich mushrooms and flax as the stand-in for rich soil).
Then `set_day` jumps to a new month three times, with the policy `fair`, `heavy` and `light`. The amount of each good is
base 100 x policy factor: 100, 150 and 50. It also reads the month field of the calendar at each jump (task 1.1, notes/month-clock.md).
It saves nothing and calls no save function. Run it on the default fixture or with --new-game.
Environment (run.py --env): REGIONS (internal names, default immenreuth,Goldhof).
"""

NAME = "tribute-rich"
DESCRIPTION = "Vassals pay 100 of each rich good of their region at a month change; heavy pays 150 and light 50."
LIMIT_S = 400
SPEED = 2
LONG_REASON = "Two adoptions and three month jumps; the poll of the tribute runs every 2 real seconds."
# Day of the year in three different months (Jan 15, Feb 15, Mar 15 in a 365-day year).
JUMP_DAYS = [15, 46, 74]
EXPECTED = {
    "immenreuth": {"rich": ["salt", "stone"], "goods": ["stone", "salt"]},
    "Goldhof": {"rich": ["mushrooms"], "goods": ["mushrooms", "flax"]},
}
BASE = 100


def tribute(ctx) -> dict:
    return ctx.mod.command("InvasionMod.tribute_state")


def vassals(ctx) -> dict:
    return ctx.mod.command("InvasionMod.vassals_state")


def jump(ctx, day: int) -> dict:
    """Jump to a day of the year and wait for the tribute tick. Returns the tick."""
    before = tribute(ctx)
    ctx.actions.set_day(day)
    ctx.run_until(lambda: tribute(ctx)["ticks"] > before["ticks"], 30, what=f"the tribute tick for day {day}")
    after = tribute(ctx)
    ctx.log.info(f"TRIBUTE_RICH day {day}: month {before['month']} to {after['month']}, ticks {before['ticks']} to {after['ticks']}")
    return {"before": before, "after": after, "tick": after["history"][-1]}


def by_region(tick: dict) -> dict:
    return {payment["region"]: payment for payment in tick["payments"]}


def check_amounts(ctx, label: str, step: dict, factor: float) -> None:
    expected = round(BASE * factor)
    payments = by_region(step["tick"])
    for region, want in EXPECTED.items():
        payment = payments.get(region)
        got = [(good["name"], good["paid"]) for good in payment["goods"]] if payment else None
        ctx.check(f"{label} {region} paid {want['goods']} at {expected} each", got == [(name, expected) for name in want["goods"]], got)
        gain = {name: step["after"]["stock"].get(str(good["id"]), 0) - step["before"]["stock"].get(str(good["id"]), 0)
                for good in (payment["goods"] if payment else []) for name in [good["name"]]}
        ctx.check(f"{label} {region} stock rose by about the paid amounts", all(value >= expected * 0.9 for value in gain.values()), gain)


def run(ctx) -> dict:
    regions = ctx.variant_option("REGIONS", "immenreuth,Goldhof").split(",")
    ctx.run_until(lambda: vassals(ctx)["home_region"] != "none", 30, what="the home region")
    slots = {}
    for region in regions:
        answer = ctx.mod.command("InvasionMod.vassals_adopt", region=region)
        slots[region] = answer["adopted_slot"]
        ctx.log.info(f"adopted {region}: slot {answer['adopted_slot']}")
    ctx.run_until(lambda: tribute(ctx)["last_month"] >= 0, 30, what="the saved month")
    ctx.check("T0 the tribute reads a month of the calendar", tribute(ctx)["month"] == tribute(ctx)["last_month"], tribute(ctx))

    fair = jump(ctx, JUMP_DAYS[0])
    months = [fair["before"]["month"], fair["after"]["month"]]
    ctx.check("T1 the month field changed and the tick ran once", fair["after"]["ticks"] == fair["before"]["ticks"] + 1 and months[0] != months[1], months)
    payments = by_region(fair["tick"])
    for region, want in EXPECTED.items():
        ctx.check(f"T2 {region} has the rich goods {want['rich']}", sorted((payments.get(region) or {}).get("rich", ["missing"])) == want["rich"], payments.get(region))
    check_amounts(ctx, "T3 fair", fair, 1.0)

    for region, slot in slots.items():
        ctx.mod.command("InvasionMod.vassals_set_policy", slot=slot, policy="heavy")
    heavy = jump(ctx, JUMP_DAYS[1])
    months.append(heavy["after"]["month"])
    check_amounts(ctx, "T4 heavy", heavy, 1.5)

    for region, slot in slots.items():
        ctx.mod.command("InvasionMod.vassals_set_policy", slot=slot, policy="light")
    light = jump(ctx, JUMP_DAYS[2])
    months.append(light["after"]["month"])
    check_amounts(ctx, "T5 light", light, 0.5)

    ctx.check("T6 three different months were seen", len(set(months)) >= 3, months)
    final = tribute(ctx)
    ctx.check("T7 no failed deposit", final["failed_deposits"] == 0, final["failed_deposits"])
    ctx.check("T8 the game still runs", vassals(ctx)["day"] is not None, final["day"])
    ctx.metric("distinct_months_seen", len(set(months)))
    ctx.metric("paid_total", final["paid_total"])
    return ctx.result()
