# Spike P5: mercenaries

Date: 2026-10-10. Branch `feat/28-unit-data-combat`. Real game, base fixture. Runs: `s7-explore2` (probes), `s7-m1`, series of `mercenary-hire` (3 of 3: `20261011-023026-c5da`, `-023115-0d79`, `-023207-66c0`, about 50 s each).
Verdict: **verified.** A company can be hired from Lua, the cost is paid and the units are there at once. Criterion P5 has a verified method.

## How a company is hired
- `RTSMultiEngineCPP.availableMercs` is an array of `MercenaryCompany` structs (`Name`, `units` = array of unit template names, `cost` silver, `arrivesIn` days, `traits`, colors). It holds **3 offers**. The offers **differ between games**: seen `greencaps` (90), `vultures` (110), `battle_brothers` (50), `brotherhood_of_the_forest` (60), `wayward_sons` (45), `huntsmen` (250), `brigands` (30). The scenario therefore reads the offers and picks the cheapest.
- `RTSMultiEngineCPP:hireMercs(company, pawnRef)` (parameters from the jmap) returns the new squads. In Lua it works with the struct from `availableMercs` and `engine.playerRef`.
- `engine.hiredMercs` is a map (count read with `ForEach`): 0 before, 1 after.
- `DT_MercenaryCompanies` holds 11 rows (`brotherhood_of_the_forest, crazy_goose, Brigands, brigands_small, wayward_sons, greencaps, vultures, battle_brothers, hildebolts_army, hildebolts_army_large, the_huntsmen`), row struct `MercenaryCompany`. Only the offered ones can be hired by the action.

## Numbers from the probe (company `greencaps`, units `mercenary_infantry x2, Mercenary_Archers`)
Silver 500 -> 410 (cost 90), offers 3 -> 2, `hiredMercs` 0 -> 1, player units +108 (3 squads of 36), at once. `arrivesIn` 11 days is **not** waited for.
**The game does not check the cost.** A second hire with silver 10 and cost 110 gave silver -100 and 108 more units. The action and the Lua command refuse when the silver is below the cost.

## Scenario `mercenary-hire` (COVERS P5)
Offers listed with plausible costs (1 to 400) and units; hire without enough silver is refused (silver cost - 1) and nothing is hired; hire with cost + 40 silver: silver paid equals the cost exactly, silver left 40, `hired` +1, squads = company units by template, each squad at least 12 units, living player units equal the answer, the census counts them, the offer left the list, 10 game seconds later at least 90% still there.
Results in 3 real runs: cost 45 -> 72 units, cost 30 -> 36 units, cost 50 -> 72 units (2 squads of 36, or 2 of 18 for `Brigands`).

## Not verified
Upkeep (`getDaysUntilCompanyGetsPaid`, wages after the first payment), company traits, firing or disbanding a company, hiring a row of `DT_MercenaryCompanies` that is not on offer, the arrival place (`arrivalRegion`), `rerollMercenaries` and `refillMercenaries`.
