"""Read one item number for a pak A/B suite (spec 09). It records a metric and asserts only that the value was read."""

NAME = "pak-item-value"
DESCRIPTION = "Records the Value of item 17 (vanilla 0.5; 0.75 with the itemvalue17 pak) as a metric, for an A/B suite."
COVERS: list[str] = []
LIMIT_S = 120
HIDDEN = True

ITEM_ROW = 17
FIELD = "Value"


def run(ctx) -> dict:
    value = ctx.actions.datatable_read(ITEM_ROW, FIELD)
    ctx.metric(f"item{ITEM_ROW}_{FIELD.lower()}", value)
    ctx.expect.at_least("item value was read", value, 0.0)
    return ctx.result()
