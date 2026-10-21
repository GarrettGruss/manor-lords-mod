"""add-liege-influence: the command liege_send_tribute takes silver and raises influence in the real game.

Run with --new-game. It saves nothing.
"""

from runlib.modstate import ModCommandError

NAME = "liege-send-tribute"
DESCRIPTION = "Send 200 silver as tribute by command: silver falls by 200, influence rises by 20. A tribute above the silver is refused."
LIMIT_S = 240
PREFIX = "InvasionMod."
SILVER = 1000
AMOUNT = 200


def liege(ctx) -> dict:
    return ctx.mod.command(PREFIX + "liege_state")


def run(ctx) -> dict:
    ctx.actions.set_silver(SILVER)
    before = liege(ctx)
    ctx.log.info(f"before {before}")
    ctx.mod.command(PREFIX + "liege_send_tribute", amount=AMOUNT)
    after = liege(ctx)
    ctx.log.info(f"after {after}")
    ctx.metric("silver_taken", before["silver"] - after["silver"])
    ctx.metric("influence_gained", after["influence"] - before["influence"])
    ctx.check("the tribute took 200 silver", before["silver"] - after["silver"] == AMOUNT, (before["silver"], after["silver"]))
    ctx.check("10 silver gave 1 influence", abs(after["influence"] - before["influence"] - AMOUNT * 0.1) < 0.01, after["influence"])
    refused = False
    try:
        ctx.mod.command(PREFIX + "liege_send_tribute", amount=int(after["silver"]) + 1000)
    except ModCommandError:
        refused = True
    final = liege(ctx)
    ctx.check("a tribute above the silver is refused", refused, final)
    ctx.check("the refused tribute changed nothing", final["silver"] == after["silver"] and final["influence"] == after["influence"], final)
    return ctx.result()
