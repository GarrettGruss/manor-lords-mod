# Home inventories in the fixtures (task 2.1)

Test scenario `bandits-homes-inventory` (read only), command `InvasionMod.bandits_homes`. Runs: `rb-homes-noai2` (playtest-noai), `rb-homes-base`, `rb-homes-base-corpse-pit`.

| Fixture | Families | Housed | Valid (a weapon or armor id at home) | Goods in homes |
|---|---|---|---|---|
| `playtest-noai` | 5 | 5 | 0 | none |
| `base` | 10 | 10 | 10 | id 133 (spears) 32, id 271 (large shields) 32, id 228 8 (not in the list) |
| `base-corpse-pit` | 10 | 10 | 10 | the same as `base` |

- The default list `rebellion_weapon_ids` (13 ids) is kept. Only 133 and 271 are stocked in the fixtures (the militia of the `base` save). The other ids are not seen in any home, so they stay a guess from `DT_Items`.
- Goods that a test puts into a home with `addToInventory` go back to the storehouse in about 1 game day (run `rb-raid-3`: 25 goods at the stock, 18 at the rebellion, 2 game days later). A test must stock the homes right before the rebellion, with the game paused. `bandits_set_timer_days_left days=0` makes the timer expire at the next poll.
- Two families can share one home (run `rb-raid-3`: 6 goods "could not be taken" because the first family had emptied the same home). `armed_families` gives every family a `key` (the home address); the rebellion takes the goods of a home once. The `valid` count counts both families.
- `consumeGoodNoCheck` removes one item of the id from the home (probe `bandits-take-goods-probe`, run `rb-take-1`: 3 of 3 items taken, inventory empty after).
