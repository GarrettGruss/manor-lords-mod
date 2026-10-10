"""Item table check (spec 09): `itemStats` rows read at runtime must equal the vanilla file, or the values in HARNESS_EXPECT_ITEM_ROWS."""

from runlib import itemtable

NAME = "datatable-vanilla"
LIMIT_S = 120


def run(ctx) -> dict:
    vanilla = itemtable.load_vanilla()
    overrides = itemtable.overrides_from_environment()
    if overrides:
        ctx.log.info(f"expected values replaced for rows: {sorted(overrides)}")
    info = ctx.actions.datatable_info()
    ctx.expect.equals("item table row count", info.get("row_count"), vanilla["row_count"])
    itemtable.compare_rows(ctx.expect, ctx.actions.datatable_read, itemtable.expected_rows(vanilla, overrides))
    return ctx.result()
