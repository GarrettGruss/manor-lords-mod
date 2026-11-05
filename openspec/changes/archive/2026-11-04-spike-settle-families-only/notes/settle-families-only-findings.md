# Spike: can a pak data change make settleRegion add only families? (2026-11-04)

Verdict: no data row found that drives the extras. The extras are native code. A pak cannot remove them.

## 1. Data search (names of all 20 game paks, `pakmod.py find`)
- No table or asset with settle, settlement, supply package, newcomer, immigration, caravan (as data) or starting goods. Terms tried: settle, supply, Suppl, newcomer, Immigr, Starting, Provision, Initial, Inventory, Cargo.
- `DT_GameSetupPresets` (one row per scenario, 3 difficulties) has `startingSuppliesMultiplier` (1 Medium/High, 2 Low). It belongs to the new game menu start, not to `settleRegion`.
- `BP_MLGameInstance` has no supply data. `settlementInitializerWidget` (the settler camp menu) only calls the native `MLGameInstance:getStartingSupplies(Level, outCost)` and `ESettlementType` (1 Town, 2 FarmingVillage, 3 ForestVillage, 4 MiningOutpost, 5 Outpost). The goods of Modest/Average/Plentiful are in native code.
- `buildingStats` row 87 is the tent camp (`homeless_tents`, `buildingFunction` Temporary). It has no capacity, family or ox field. The camp and its families come from native code.

## 2. Real game tests (slot 1, save fixture saveGame_57, Riesenbuckel, 10 families, 25 buildings)
One `settleRegion` call on the settled home region, `supply` 0. The result is the same in every run:

| Run | Variable | Families | Tent camps (type 87) | Buildings | Oxen | Goods |
|---|---|---|---|---|---|---|
| sfo-mult0 | none (write refused: field not on the whitelist) | 10 -> 15 | 0 -> 1 | 25 -> 29 | 17 -> 18 | 449 -> 528 (+79) |
| sfo-mult0b | `startingSuppliesMultiplier` = 0 (write worked, read back 0) | 10 -> 15 | 0 -> 1 | 25 -> 29 | 17 -> 18 | 451 -> 530 (+79) |
| sfo-type5 | settlement type 5 (Outpost) | 10 -> 15 | 0 -> 1 | 25 -> 29 | 17 -> 18 | 450 -> 529 (+79) |
| sfo-type4 | settlement type 4 (MiningOutpost) | 10 -> 15 | 0 -> 1 | 25 -> 29 | 17 -> 18 | 450 -> 529 (+79) |
| sfo-grow1 | `Region:growPopulation()` x5, 2 vacant homes | 10 -> 10 | 0 | 25 | not read | no change |

- The settlement type has no effect on a settled region. The multiplier has no effect on the goods.
- The extra goods: 15 +20, 16 +8, 172 +20, 216 +20, 234 +1, 6 +10.
- The 5 new families (3 homeless at once) live in the new camp.
- `growPopulation` adds no family, also with free homes (it needs the right day and approval).

## 3. Not tested
- A pak that edits `buildingStats` row 87. No field there can remove the camp, the ox or the goods, so a test would only change the look or the cost of the camp.
- `settleRegion` on an unsettled region with other types (it crashed the game 3 of 3 times without an owner; see DANGEROUS_ACTIONS.md and `dynamic-lords.md`).
- The natural immigration of families over time (approval based): no data table was found, and `growPopulation` did nothing.

## 4. Recommendation
- Keep the accepted extras (spec delta of this change).
- A data-only fix is not possible. Options that stay: (a) cleanup in Lua after the call (demolish the new camp is not possible because its families live in it; `just_die` + hide the new ox; `consumeGoodNoCheck` for the 79 goods), not tested; (b) a native or C++ hook (out of scope for UE4SS Lua); (c) leave as is.
- If the owner wants to continue, a spike on Lua cleanup (ox by before/after comparison, goods by `consumeGoodNoCheck`) is the next small step.
