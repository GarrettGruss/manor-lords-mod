"""Put loot on raiders, read it per unit, kill them and read it again (spec 10, spikes S3 and S5)."""

from runlib.units import loot_max, loot_total

NAME = "raid-loot"
DESCRIPTION = "set_unit_loot writes ItemsLooted, the census reads it, kill_units kills the carriers and their loot goes to 0."
COVERS = ["R2"]  # R3 (loot drop) is not proven: see criteria.json spike_note
LIMIT_S = 120
CARRIERS = 3
AMOUNT = 7


def run(ctx) -> dict:
    expect = ctx.expect
    ctx.actions.spawn_raid(squads=1)
    start = ctx.actions.units_census()
    expect.equals("no loot at the start", loot_total(start), 0)

    ctx.actions.set_unit_loot("bandit", CARRIERS, AMOUNT)
    loaded = ctx.actions.units_census()
    expect.equals("loot read back", loot_total(loaded), CARRIERS * AMOUNT)
    expect.equals("most loot on one unit", loot_max(loaded), AMOUNT)

    ctx.actions.kill_units("bandit", CARRIERS, with_loot=True)
    after = ctx.actions.units_census()
    expect.equals("loot after the death of the carriers", loot_total(after), 0)
    expect.equals("dead units", after["by_state"].get("dead"), CARRIERS)
    return ctx.result()
