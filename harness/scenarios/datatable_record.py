"""Hidden tool scenario: record vanilla `itemStats` rows into harness/vanilla/itemStats.json. Run it on a game without a data pak."""

import json

from runlib import itemtable
from runlib.commands import CommandError

NAME = "datatable-record"
LIMIT_S = 120
HIDDEN = True
FIRST_ID = -1
LAST_ID = 120
SAMPLE_SIZE = 24


def read_row(actions, row: int):
    """Return the field values of a row, or None when the row does not exist."""
    values = {}
    for field in itemtable.FIELDS:
        try:
            values[field] = actions.datatable_read(row, field)
        except CommandError as error:
            if "no row named" in str(error):
                return None
            raise
    return values


def spread(ids: list, count: int) -> list:
    step = max(1, len(ids) // count)
    return ids[::step][:count]


def run(ctx) -> dict:
    info = ctx.actions.datatable_info()
    found = {}
    for row in range(FIRST_ID, LAST_ID + 1):
        values = read_row(ctx.actions, row)
        if values is not None:
            found[str(row)] = values
    chosen = {row: found[row] for row in spread(list(found), SAMPLE_SIZE)}
    data = {"table": "RTSMultiEngineCPP.itemStats", "row_count": info["row_count"], "fields": list(itemtable.FIELDS), "rows": chosen}
    itemtable.VANILLA_PATH.parent.mkdir(exist_ok=True)
    itemtable.VANILLA_PATH.write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    ctx.expect.at_least("rows found", len(found), SAMPLE_SIZE)
    ctx.expect.equals("row count", info["row_count"], 213)
    return ctx.result()
