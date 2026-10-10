"""Spawn raiders, elite raiders and a bandit camp with actions and count the units by side (spec 10, spikes S2 and S3)."""

from runlib.units import ELITE_RAID_UNITS, SQUAD_UNITS, side_count, squads_of_side

NAME = "raid-spawn"
DESCRIPTION = "spawn_raid adds 18 bandit units a squad, the elite raid adds 54, a bandit camp adds 18. Civil units do not change."
COVERS = ["T2"]  # T3 (unit types) is not proven: see criteria.json spike_note
LIMIT_S = 120


def run(ctx) -> dict:
    expect = ctx.expect
    start = ctx.actions.units_census(sample=3)
    ctx.actions.spawn_raid(squads=2)
    ctx.actions.spawn_raid(elite=True)
    ctx.actions.spawn_bandit_camp()
    end = ctx.actions.units_census(sample=3)

    added = side_count(end, "bandit") - side_count(start, "bandit")
    expect.equals("bandit units added", added, 2 * SQUAD_UNITS + ELITE_RAID_UNITS + SQUAD_UNITS)
    expect.equals("civil units unchanged", side_count(end, "civil"), side_count(start, "civil"))
    expect.at_least("bandit squads added", len(squads_of_side(end, "bandit")) - len(squads_of_side(start, "bandit")), 4)
    expect.at_least("sample rows are not civil", len(end["sample"]), 1)
    expect.at_most("census cost in ms", end["ms"], 100)
    return ctx.result()
