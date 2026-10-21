# Does a burned store lose its goods (task 1.2, design question 3)

Date: 2026-10-20. Same test scenario and runs as `fire-during-raid.md`. Numbers are goods in one store (census `stores`), read right after lighting and 10 to 30 game seconds later. Two stores burn each time.

| Run id | Store (type before) | Goods at lighting | Goods 10 s later | Goods 30 s later |
|---|---|---|---|---|
| `20261021-034539-1b8d` (raiders) | ...468110 (80) | 30 | 12 | not read |
| `20261021-034539-1b8d` (raiders) | ...468274 (72) | 107 | 95 | not read |
| `20261021-035316-f1d4` (raiders) | ...468092 (80) | 30 | 15 | 14 |
| `20261021-035316-f1d4` (raiders) | ...468256 (72) | 107 | 85 | 85 |
| `20261021-035711-e76b` (no raiders, 1 rubble) | ...468271 (72) | 107 | 80 | 79 |

Per good in `1b8d`, store ...468274: good 17 from 14 to 10, good 216 from 13 to 10, good 6 from 6 to 3, good 9 from 10 to 8, good 15 stays 64.

## Answer (data for design question 3)
- Yes. A burned store loses part of its goods in the first 10 game seconds: 50 to 60 percent of the small store (30 goods) and 11 to 26 percent of the large store (107 goods). After that the amount is stable (checked to 30 s in `f1d4`, `e76b`).
- The rubble keeps the rest. The ruin still counts as a store with goods (type 75, 12 to 95 goods). The existing check "ruins hold no goods" in `sack-ruins` is wrong for this fixture.
- Other stores did not change (for example the 124 goods store).
- The village stock total fell by 19 to 33 in every run, also in runs with no rubble (`78c1`: 428 to 400), so the total is a noisy measure. Use the per-store numbers.
- Consequence for the change: if goods must not be destroyed, the mod has to move or add back the lost part (about 10 to 60 percent of a burned store), or use `collapse` for stores. `collapse` was not measured here. The owner decides; this note is data only.

## Not verified
- Where the lost goods go (burned, or carried away by villagers).
- The loss for store types other than 80 and 72.
- `collapse` on the same stores.
