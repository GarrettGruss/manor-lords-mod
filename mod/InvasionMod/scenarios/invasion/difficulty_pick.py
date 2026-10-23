"""M02 iteration 04, D1 to D4, and update-raid-difficulty-levels (#404): the test pick sets the three levels together; each level can then be set alone.
The levels scale the raid plan (yearly, vassal), the waves and the relief army (great) and the Public Order debuff.

Option (run.py --env): INVASION_DIFFICULTY (1 to 3, default 2). It saves nothing.
"""

NAME = "invasion-difficulty-pick"
LIMIT_S = 200
RELIEF = {1: 15, 2: 8, 3: 0}


def run(ctx) -> dict:
    pick = int(ctx.variant_option("INVASION_DIFFICULTY", "2"))
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    before = ctx.mod.command("InvasionMod.invasion_difficulty_state")
    ctx.check("D1 before a pick the difficulty is not chosen", before["chosen"] is False, before)
    after = ctx.mod.command("InvasionMod.invasion_pick_difficulty", value=pick)
    ctx.check("D2 the pick is stored", (after["yearly"], after["great"], after["vassal"]) == (pick, pick, pick) and after["chosen"] is True, after)
    refused = ctx.mod.refusal("InvasionMod.invasion_pick_difficulty", value=1)
    ctx.check("D2 a second pick is refused", refused is not None, refused)
    ctx.check("D3 relief squads", after["relief_squads"] == RELIEF[pick], after["relief_squads"])
    ctx.check("D3 waves equal the difficulty", after["waves"] == pick, after["waves"])
    plan = ctx.mod.command("InvasionMod.invasion_state")
    ctx.check("D3 planned squads are a multiple of the difficulty", plan["squads"] % pick == 0 and 1 <= plan["squads"] // pick <= 3, plan["squads"])
    bandits = ctx.mod.command("InvasionMod.bandits_state")
    ctx.check("D4 the bandits feature reads the picked difficulty", bandits["difficulty"] == pick, bandits.get("difficulty"))
    # D5: one level at a time. Yearly 1, great 3, vassal 0: the plan and the great raid follow their own level.
    ctx.mod.command("InvasionMod.invasion_set_level", kind="yearly", value=1)
    ctx.mod.command("InvasionMod.invasion_set_level", kind="great", value=3)
    ctx.mod.command("InvasionMod.invasion_set_level", kind="vassal", value=0)
    mixed = ctx.mod.command("InvasionMod.invasion_difficulty_state")
    plan = ctx.mod.command("InvasionMod.invasion_state")
    ctx.check("D5 the levels are yearly 1, great 3, vassal 0", (mixed["yearly"], mixed["great"], mixed["vassal"]) == (1, 3, 0), mixed)
    ctx.check("D5 the yearly raid has the squads of level 1 (1 to 3 squads)", 1 <= plan["squads"] <= 3, plan["squads"])
    ctx.check("D5 the great raid has 3 waves and no relief army", (mixed["waves"], mixed["relief_squads"]) == (3, 0), mixed)
    ctx.check("D5 no subjugation raid at vassal level 0", ctx.mod.refusal("InvasionMod.invasion_plan_now", kind="subjugation") is not None)
    ctx.check("D5 a level of 4 is refused", ctx.mod.refusal("InvasionMod.invasion_set_level", kind="yearly", value=4) is not None)
    ctx.metric("difficulty", pick)
    return ctx.result()
