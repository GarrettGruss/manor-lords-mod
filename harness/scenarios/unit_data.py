"""Read the unit template table DT_UnitTemplates, change one number live and see the behavior change (spec 10, spike S7, criterion C3)."""

from runlib import battle
from runlib.actions import ActionNotPossible
from runlib.commands import CommandRefused

NAME = "unit-data"
DESCRIPTION = "datatable_rows lists DT_UnitTemplates; writing maxSize of a row changes the size of the next squad of that template; the value is restored."
COVERS = ["C3"]
LIMIT_S = 120

TEMPLATE = battle.SPEAR
FIELD = "maxSize"
SMALL_SIZE = 10
NUMBER_FIELDS = ("combatExperience", "cost", "maxSize", "minArcheryTraining", "minHouseLv", "minMeleeTraining")
MIN_ROWS = 20   # the table has 25 rows without the separator lines
KNOWN_ROWS = (battle.SPEAR, battle.SWORD, battle.BOW, battle.HEAVY, "mercenary_spearmen", "Brigands")


def check_table(ctx) -> dict:
    expect = ctx.expect
    info = ctx.actions.datatable_info("units")
    expect.at_least("unit table rows (with separators)", info["name_count"], MIN_ROWS)
    expect.record("row struct is the unit template", "UnitTemplate" in info["row_struct"], info["row_struct"], "UnitTemplate")
    rows = ctx.actions.datatable_rows("units")
    expect.at_least("listed rows", len(rows), MIN_ROWS)
    names = {row["row"] for row in rows}
    expect.record("known templates are listed", set(KNOWN_ROWS) <= names, sorted(set(KNOWN_ROWS) - names), "none missing")
    every_field = all(set(row["values"]) == set(NUMBER_FIELDS) for row in rows)
    expect.record("every row has the six number fields", every_field, len(rows), "all rows")
    expect.record("every maxSize is positive", all(row["values"]["maxSize"] >= 1 for row in rows), "", "maxSize >= 1")
    return battle.row_values(rows, TEMPLATE)


def check_refusals(ctx) -> None:
    refused = (
        ("unknown table", lambda: ctx.actions.datatable_read(TEMPLATE, FIELD, table="monsters")),
        ("field not in the list", lambda: ctx.commands.send("datatable_read", row=TEMPLATE, field="Name", table="units")),
        ("unknown row", lambda: ctx.commands.send("datatable_read", row="no_such_unit", field=FIELD, table="units")),
        ("missing value", lambda: ctx.commands.send("datatable_write", row=TEMPLATE, field=FIELD, table="units")),
    )
    for name, call in refused:
        try:
            call()
            ctx.expect.record(f"refused: {name}", False, "accepted", "refused")
        except (CommandRefused, ActionNotPossible) as error:
            ctx.expect.record(f"refused: {name}", True, str(error)[:60], "refused")


def squad_size(ctx, template: str) -> int:
    ctx.actions.clear_battle()
    record = ctx.actions.spawn_units("player", template)
    size = record["answer"]["units"]
    ctx.actions.clear_battle()
    return size


def run(ctx) -> dict:
    expect = ctx.expect
    original = check_table(ctx)
    check_refusals(ctx)
    start_size = original[FIELD]
    other_size = ctx.actions.datatable_read(battle.SWORD, FIELD, table="units")
    expect.equals("read of one field equals the listed value", ctx.actions.datatable_read(TEMPLATE, FIELD, table="units"), start_size)

    # The row says 32 and the game spawns 32 units: the squad size follows the row (spike S7).
    expect.equals("squad size before the change", squad_size(ctx, TEMPLATE), start_size)
    try:
        ctx.actions.datatable_write(TEMPLATE, FIELD, SMALL_SIZE, table="units")
        expect.equals("field read back", ctx.actions.datatable_read(TEMPLATE, FIELD, table="units"), SMALL_SIZE)
        expect.equals("squad size after the change", squad_size(ctx, TEMPLATE), SMALL_SIZE)
        expect.equals("another template is not changed", ctx.actions.datatable_read(battle.SWORD, FIELD, table="units"), other_size)
    finally:
        ctx.actions.datatable_write(TEMPLATE, FIELD, start_size, table="units")
    expect.equals("field restored", ctx.actions.datatable_read(TEMPLATE, FIELD, table="units"), start_size)
    expect.equals("squad size after the restore", squad_size(ctx, TEMPLATE), start_size)
    ctx.metric("squad_size_changed", SMALL_SIZE)
    return ctx.result()
