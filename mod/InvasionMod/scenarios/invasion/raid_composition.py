"""M05 iteration 02, A3 to A5: a forced large raid spawns the planned Hussite composition.

Option INVASION_DIFFICULTY (1 to 3, default 1). The scenario forces a large raid and spawns it at once (invasion_force_next).
The mod reports the squads it made (id, template) with the mean stats of their living units. The scenario matches each squad to
a template by its stats (profiles from the probe `unit-balance-role-templates`) and compares with the plan.
The rule unit_balance is off while the stats are read, so the profiles are the vanilla ones. It saves nothing.
"""

import time
from collections import Counter

NAME = "invasion-raid-composition"
DESCRIPTION = "A forced large raid spawns the planned composition (templates, units, ranged share)."
COVERS = []
LIMIT_S = 240
SIZE_MULTIPLIER = 3  # large
SETTLE_S = 2
SIZE_FIT = 0.9  # a squad may lose a few units before the first read
# Mean stats of a vanilla squad (run 20261017-221800-9e31): att, def, armorPierce, units.
PROFILES = {
    "Brigands": (2.389, 2.778, 0.0, 18), "spearMilitia": (4.031, 6.688, 0.0, 32), "militiaFoot": (5.0, 4.875, 0.0, 32),
    "mercenary_infantry": (5.0, 5.944, 0.0, 36), "retinue_tier3": (6.917, 63.5, 0.944, 36), "brigandPolearms": (5.0, 4.0, 2.0, 36),
    "bowMilitia": (3.063, 2.0, 0.0, 32), "brigandArchers": (3.0, 4.0, 0.0, 36),
    "crossbowMilitia": (3.063, 2.0, 0.0, 32), "mercenary_crossbowmen": (3.056, 2.611, 0.0, 36),
}
RANGED = {"bowMilitia", "brigandArchers", "crossbowMilitia", "mercenary_crossbowmen"}
# Templates with the same profile cannot be told apart by stats. They share one label.
SAME_PROFILE = {"crossbowMilitia": "bowMilitia"}


def label(template: str) -> str:
    return SAME_PROFILE.get(template, template)


def match(squad: dict) -> str:
    """The template whose unit count fits the squad and whose profile is nearest, or 'unknown'.

    The mean stats of a squad vary a little between spawns (random gear), so the unit count picks the candidates first.
    """
    mean = squad["mean"]
    candidates = {name: profile for name, profile in PROFILES.items() if profile[3] * SIZE_FIT <= squad["alive"] <= profile[3]}
    if not candidates:
        return "unknown"
    gap = lambda profile: abs(mean["att"] - profile[0]) + abs(mean["def"] - profile[1]) + abs(mean["armorPierce"] - profile[2])
    return label(min(candidates, key=lambda name: gap(candidates[name])))


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_plan_now")["raid_day"] > 0, 30, what="the raid plan")
    plan = ctx.mod.command("InvasionMod.invasion_set_size", size="large")
    planned = plan["composition"].split("-")
    ctx.log.info(f"COMPOSITION plan difficulty={difficulty} {plan['composition']} raiders={plan['raiders']}")
    ctx.check("A6 squads = multiplier x difficulty", plan["squads"] == SIZE_MULTIPLIER * difficulty, plan["squads"])
    ctx.check("A2 one template for each squad", len(planned) == plan["squads"], planned)
    ctx.check("A1 every planned template has a profile", all(name in PROFILES for name in planned), planned)

    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raids_spawned"] == 1, 30, what="the raid spawn")
    time.sleep(SETTLE_S)  # one read only: many reads of all units can crash the game (M03 notes)
    squads = ctx.mod.command("InvasionMod.invasion_raid_squads")["squads"]
    ctx.log.info(f"COMPOSITION squads {squads}")
    ctx.check("A3 the mod made one squad for each planned template", [row["template"] for row in squads] == planned, squads)
    observed = Counter(match(row) for row in squads)
    expected = Counter(label(name) for name in planned)
    ctx.check("A3 the stats of the spawned squads match the planned templates", observed == expected, [dict(observed), dict(expected)])

    units = sum(row["alive"] for row in squads)
    planned_units = sum(PROFILES[name][3] for name in planned)
    ctx.check("A5 spawned units = sum of the template sizes (a small loss in a fight is allowed)", 0.9 * planned_units <= units <= planned_units,
              [units, planned_units])
    ctx.check("A5 the state reports the same unit count", plan["raiders"] == planned_units, [plan["raiders"], planned_units])
    ranged = sum(1 for name in planned if name in RANGED)
    ctx.check("A4 ranged share is within range", ranged <= 0.25 * len(planned) + 1, [ranged, len(planned)])
    ctx.metric("difficulty", difficulty)
    ctx.metric("squads", len(planned))
    ctx.metric("ranged_squads", ranged)
    ctx.metric("spawned_units", units)
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=True)
    return ctx.result()
