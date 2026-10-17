"""M05 iteration 02, A1: every template planned for a Hussite role exists, spawns as a bandit-side squad, and has a stat profile.

The rule unit_balance is switched off, so the profile is the vanilla one. The scenario records att, def, block, armorPierce and charge
of each template, to choose between candidates. It saves nothing and fights nothing.
"""

import time

NAME = "unit-balance-role-templates"
DESCRIPTION = "Spawn each candidate template as a bandit squad and record its unit count and stat profile."
COVERS = []
LIMIT_S = 180
SETTLE_WAIT_S = 4  # equipment can load after the spawn (spike C1)
CANDIDATES = ["Brigands", "spearMilitia", "militiaFoot", "militiaPole", "mercenary_spearmen", "mercenary_infantry", "brigandPolearms",
              "retinue_tier1", "retinue_tier3", "bowMilitia", "brigandArchers", "Mercenary_Archers", "crossbowMilitia", "mercenary_crossbowmen"]


def profile(ctx, template: str) -> dict:
    rows = [row for row in ctx.actions.unit_stats("bandit")["squads"] if row["template"] == template and row["alive"] > 0]
    return {"alive": rows[0]["alive"], **rows[0]["mean"]} if rows else {}


def run(ctx) -> dict:
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
    known = {row["row"] for row in ctx.actions.datatable_rows("units")}
    ctx.actions.clear_battle()
    try:
        for index, template in enumerate(CANDIDATES):
            ctx.check(f"A1 row {template} exists", template in known, template)
            if template not in known:
                continue
            ctx.actions.spawn_units("bandit", template, count=1, dx=3000 * (index % 5), dy=3000 * (index // 5))
        time.sleep(SETTLE_WAIT_S)
        for template in CANDIDATES:
            stats = profile(ctx, template)
            ctx.log.info(f"ROLE_PROFILE {template} {stats}")
            ctx.check(f"A1 {template} spawned units on the bandit side", stats.get("alive", 0) > 0, stats)
            for key, value in stats.items():
                ctx.metric(f"{template}.{key}", round(value, 2))
    finally:
        ctx.mod.command("InvasionMod.unit_balance_set", enabled=True)
        ctx.actions.clear_battle()
    return ctx.result()
