# Immigration surge by `settleRegion` on a settled region (part 9, 2026-10-12)

Game 0.8.111, fixture `base` (Riesenbuckel, region object `Nusslohe`, 10 families, owner = player pawn, settled, type 1).
Scenario: `probe-immigration-surge` (hidden). Data: `runs/<id>/probe.jsonl`. No save function, no eval. No crash.
Runs: `s15-surge1` (2 settle calls), `s15-surge2` and `s15-surge3` (growth read only, 0 calls).

## Question
Does `PawnCPP:settleRegion` on the player's own, already settled region add homeless refugee families, without the raid and letter cycle?

## Method
`settle_region` (target 0, type 1 = the region's own type, supply 0), camp at spot 1 of `tent_find_spot`. The command did not refuse a settled region, so no flag was added. The command now takes the camp as `x`, `y`, `z` in the Python wrapper too. After each call: one read at once, then one read per game day for 5 days (speed 3).

## Result: it works
| Step | Families | Homeless | Residents | Tents (type 87) | Buildings (region) | Approval |
|---|---|---|---|---|---|---|
| start (day 0) | 10 | 0 | 35 | 0 | 24 | 71 |
| call 1, at once | 15 | 3 | 45 | 1 (3 families) | 28 | 71 |
| call 1, day 1 to 5 | 15 | 3 | 46, 47 | 1 | 28 | 63, 62, 61, 62, 61 |
| call 2 (new spot), at once | 20 | 8 | 57 | 2 (3 + 5 families) | 32 | 61 |
| call 2, day 1 to 5 | 20 | 8 | 57 | 2 | 32, 32, 30, 30, 30 | 58, 57, 56, 55, 54 |

- Each call adds 5 families (10 -> 15 -> 20) and a NEW homeless tent (`SMBuildingMaster`, `bType` 87, built, at once). The tent holds 3 families after call 1 and 5 after call 2; so the homeless count is 3 then 8, not 5 then 10. Where the other 2 families of call 1 live is open (vacant slots were 2 before, then -3).
- It acts like the first settle of an empty region (0 -> 5 families, S13), repeated. The camp spot is only a position hint here: each call made one tent.
- Approval fell at once on the day after each call (71 -> 63, then 61 -> 58) and kept falling about 1 a day (54 after 5 days). This is the wanted draw-down.
- Side effects: none seen on the old state. Owner, `isSettled` (true), settlement type and level did not change. The 9 residential buildings did not change. The region building count rose by 4 per call (the camp objects); it fell 32 -> 30 on day 3 after call 2 (2 camp objects vanished; not checked which).
- Silver, stock and bandit state were not read.

## Natural immigration (read only)
`family_state` now has `growth`: the map of `Region:GetMonthlyPopGrowthModifiersWithValues()` as `{ "1": Base, "2": NoBurgagePlotAvailability, "3": Approval }`.
`base` start (approval 71, 0 homeless, 2 vacant slots): `{ "1": 1, "3": 1 }` (runs s15-surge2, s15-surge3). So Base +1 and Approval +1 per month; no "no burgage plot" penalty. Natural growth is small and monthly (1 game month = many days), so `settleRegion` is the way to a surge.
The map comes back as a Lua table: iterate with `pairs`, not `ForEach` (`ForEach` is nil).

## Not done
- A camp near woods or the map edge was not tried (3 of 4 launches used; the spot did not seem to matter).
- Not tried: a third call, other types (2 to 5), supply above 0, a region with homeless families already present, the effect of the 5 days beyond day 5 (do the families starve or leave).
- Run `s15-surge1` ended with 20 families and 8 homeless: that is a usable surge size (+10 families, approval 71 -> 54).

## Decisions
- Part 9 answer: YES. Use `settle_region` on the player region, a free spot from `tent_find_spot`, as the surge. Max 2 calls were tested; cap a mod at a small number.
