"""Change update-banditry-rebellion-raid: probe how consumeGoodNoCheck behaves on a home with weapons.

It stocks the homes, then takes the weapon goods of one armed home and writes the inventory before and after into the notes.
Run: uv run python harness/run.py --scenario bandits-take-goods-probe --fixture playtest-noai --max-runs 1000
It changes goods of one home only. It saves nothing and never fails on a game answer.
"""

NAME = "bandits-take-goods-probe"
DESCRIPTION = "Probe: take the weapons of one home with consumeGoodNoCheck and read the inventory."
LIMIT_S = 180
HIDDEN = True


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.bandits_stock_homes", good=133, amount=2, homes=3)
    ctx.mod.command("InvasionMod.bandits_stock_homes", good=271, amount=1, homes=3)
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    ctx.notes.append(f"homes before: {[h['inventory'] for h in homes['homes']]}")
    for index in (1, 2):
        answer = ctx.mod.command("InvasionMod.bandits_test_take_goods", index=index)
        ctx.notes.append(f"take {index}: {answer}")
        ctx.log.info(f"TAKE {index} {answer}")
    ctx.time.run_game_seconds(40, speed=1)
    homes = ctx.mod.command("InvasionMod.bandits_homes")
    ctx.notes.append(f"homes after one game day: {[h['inventory'] for h in homes['homes']]}")
    ctx.check("the probe ran", True, "")
    return ctx.result()
