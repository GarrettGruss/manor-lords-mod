"""Spike scenario (spec 29): does a data row that a pak added load, spawn and shoot?

Options (variant, `--env`): CUSTOM_UNIT (unit row name), CUSTOM_ITEM (item row), CUSTOM_FIELDS (item fields to read).
It only reads and spawns. It never saves.
"""

from runlib import battle

NAME = "probe-custom-unit"
DESCRIPTION = "Spike: reads a pak-added unit row and item row, spawns the unit and records squad size and stats."
COVERS: list[str] = []
LIMIT_S = 180
HIDDEN = True

ITEM_FIELDS = ("rangedAtt", "armorPierce", "shootingRange", "Speed", "att", "def", "block")


def run(ctx) -> dict:
    unit = battle.check_name("CUSTOM_UNIT", ctx.variant_option("CUSTOM_UNIT", "handCannon"))
    item = ctx.variant_option("CUSTOM_ITEM", "359")
    units_info = ctx.actions.datatable_info("units")
    items_info = ctx.actions.datatable_info("items")
    ctx.log.info(f"units table: {units_info}")
    ctx.log.info(f"items table: {items_info}")
    names = {row["row"] for row in ctx.actions.datatable_rows("units")}
    ctx.expect.record("new unit row is listed", unit in names, sorted(names), unit)
    for field in ITEM_FIELDS:
        try:
            ctx.log.info(f"item {item} {field} = {ctx.actions.datatable_read(item, field, table='items')}")
        except Exception as error:  # a refused read is a finding, not a harness failure
            ctx.log.info(f"item {item} {field} read failed: {error}")
    ctx.actions.clear_battle()
    try:
        record = ctx.actions.spawn_units("player", unit)
        ctx.log.info(f"spawn answer: {record['answer']}")
        ctx.log.info(f"unit stats: {ctx.actions.unit_stats()['squads']}")
        ctx.metric("spawned_units", record["answer"]["units"])
        ctx.screenshot("custom_unit")
    finally:
        ctx.actions.clear_battle()
    return ctx.result()
