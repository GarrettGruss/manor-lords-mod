"""M05 iteration 02, A3 to A5: a forced large raid spawns the planned Hussite composition.

Option INVASION_DIFFICULTY (1 to 3, default 1). The scenario forces a large raid and spawns it at once (invasion_force_next).
The mod reports the squads it made (id, template) with the mean stats of their living units. The scenario matches each squad to
a template by its stats (profiles from the probe `unit-balance-role-templates`) and compares with the plan.
The rule unit_balance is off while the stats are read, so the profiles are the vanilla ones. It saves nothing.
"""

from collections import Counter

NAME = "invasion-raid-composition"
DESCRIPTION = "A forced large raid spawns the planned composition (templates, units, ranged share)."
COVERS = []
LIMIT_S = 240
SIZE_MULTIPLIER = 3  # large
TOLERANCE = 0.2
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
    """The template whose profile is closest to the squad, or 'unknown'."""
    mean = squad["mean"]
    best, best_gap = "unknown", None
    for name, (att, defence, pierce, units) in PROFILES.items():
        if squad["alive"] > units:
            continue
        gap = abs(mean["att"] - att) + abs(mean["def"] - defence) + abs(mean["armorPierce"] - pierce)
        if best_gap is None or gap < best_gap:
            best, best_gap = name, gap
    return label(best) if best_gap is not None and best_gap <= TOLERANCE * 3 else "unknown"


def run(ctx) -> dict:
    difficulty = int(ctx.variant_option("INVASION_DIFFICULTY", "1"))
    ctx.mod.command("InvasionMod.unit_balance_set", enabled=False)
    ctx.mod.command("InvasionMod.invasion_set_difficulty", value=difficulty)
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raid_day"] > 0, 30, what="the raid plan")
    plan = ctx.mod.command("InvasionMod.invasion_set_size", size="large")
    planned = plan["composition"].split("-")
    ctx.log.info(f"COMPOSITION plan difficulty={difficulty} {plan['composition']} raiders={plan['raiders']}")
    ctx.check("A6 squads = multiplier x difficulty", plan["squads"] == SIZE_MULTIPLIER * difficulty, plan["squads"])
    ctx.check("A2 one template for each squad", len(planned) == plan["squads"], planned)
    ctx.check("A1 every planned template has a profile", all(name in PROFILES for name in planned), planned)

    ctx.mod.command("InvasionMod.invasion_force_next")
    ctx.run_until(lambda: ctx.mod.command("InvasionMod.invasion_state")["raids_spawned"] == 1, 30, what="the raid spawn")
    ctx.run_until(lambda: all(row["alive"] > 0 for row in ctx.mod.command("InvasionMod.invasion_raid_squads")["squads"]), 20,
                  what="all raid squads to have units")
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
