# Herd cost (spike 1.4): fails, the cost is dropped

Runs 20261106-001313-77bd, -001542-9c52 and -001719-bfb7 (slot 1, fixture `playtest-noai`, variant `herd`).

- `region:getStockOfGood(id, false, false)` counts animals: ox (234) gave 2, the other animal ids gave 0 (the fixture has no other animals).
- Animals are not in the `Inventory` of a building. `consumeGoodNoCheck(234)` over every building that lists the good found no holder (0 taken, stock stayed 2 for a game day).
- An ox shed (building type 97) holds the animal actors in its `animals` array (1 entry, class `VAMP_Ox_C`). The other buildings have an empty array.
- `just_die()` on that `VAMP_Ox_C` returned without an error, but `dead` stayed false and the stock stayed 2 for a game day. It does nothing.
- `K2_DestroyActor` is on the crash list (DANGEROUS_ACTIONS.md) and was not tried.

Verdict: no safe way to remove an animal. The `herd` cost is not in the table (design decision 9). Open for the owner: a later spike on pens (sheep, goats, pigs) with a real herder, or on selling animals through the livestock market.
