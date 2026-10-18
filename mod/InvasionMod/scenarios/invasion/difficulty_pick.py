"""M02 iteration 04, D1 to D4: the player picks the difficulty at the start. It scales the raid plan, the relief army and the Public Order debuff.

Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 2). It saves nothing.
"""

NAME = "invasion-difficulty-pick"
LIMIT_S = 200
RELIEF = {1: 15, 2: 8, 3: 0}


def run(ctx) -> dict:
    pick = int(ctx.variant_option("INVASION_DIFFICULTY", "2"))
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    before = ctx.mod.command("InvasionMod.invasion_difficulty_state")
    ctx.check("D1 before a pick the difficulty is not chosen", before["chosen"] is False, before)
    after = ctx.mod.command("InvasionMod.invasion_pick_difficulty", value=pick)
    ctx.check("D2 the pick is stored", after["difficulty"] == pick and after["chosen"] is True, after)
    refused = ctx.mod.refusal("InvasionMod.invasion_pick_difficulty", value=1)
    ctx.check("D2 a second pick is refused", refused is not None, refused)
    ctx.check("D3 relief squads", after["relief_squads"] == RELIEF[pick], after["relief_squads"])
    ctx.check("D3 waves equal the difficulty", after["waves"] == pick, after["waves"])
    plan = ctx.mod.command("InvasionMod.invasion_state")
    ctx.check("D3 planned squads are a multiple of the difficulty", plan["squads"] % pick == 0 and 1 <= plan["squads"] // pick <= 3, plan["squads"])
    bandits = ctx.mod.command("InvasionMod.bandits_state")
    ctx.check("D4 the bandits feature reads the picked difficulty", bandits["difficulty"] == pick, bandits.get("difficulty"))
    ctx.metric("difficulty", pick)
    return ctx.result()
