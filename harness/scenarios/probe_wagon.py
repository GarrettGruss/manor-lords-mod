"""Spike scenario (spec 29, part B): can a spawned unit hold a wagon with the native trade wagon call?

It spawns one squad, calls the allow-listed wagon functions on one unit and logs the answers. It takes a screenshot after.
Options: WAGON_TEMPLATE (unit row, default spearMilitia).
"""

from runlib import battle

NAME = "probe-wagon"
DESCRIPTION = "Spike: equipTradeWagon on a spawned unit; logs the wagon object and takes a screenshot."
COVERS: list[str] = []
LIMIT_S = 180
HIDDEN = True


def probe(ctx, squad: int, call: str) -> dict:
    answer = ctx.commands.send("unit_probe", squad=squad, call=call)
    ctx.log.info(f"unit_probe {call}: {answer}")
    return answer


def run(ctx) -> dict:
    template = battle.check_name("WAGON_TEMPLATE", ctx.variant_option("WAGON_TEMPLATE", battle.SPEAR))
    ctx.actions.clear_battle()
    try:
        squad = ctx.actions.spawn_units("player", template)["answer"]["squads"][0]["id"]
        probe(ctx, squad, "isWagonEquipped")
        probe(ctx, squad, "equipTradeWagon")
        equipped = probe(ctx, squad, "isWagonEquipped")
        probe(ctx, squad, "getEquippedWagon")
        ctx.expect.record("the wagon call ran", equipped["call_ok"], equipped["answer"], "call_ok")
        ctx.screenshot("wagon")
    finally:
        ctx.actions.clear_battle()
    return ctx.result()
