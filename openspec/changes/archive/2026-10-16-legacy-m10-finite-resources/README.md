# M10: finite-resources

Feature folder: `finite_resources`. Batch 4.

## Goal
Home deposits of iron, salt and similar goods run out. Vassals are the permanent source.

## Player rules (from M00)
- The home region has plentiful natural resources, but they are finite.
- Iron, salt and other exhaustible goods run out. Home finite deposits last 2 to 4 game years at normal use.
- Vassal tribute is the permanent supply.
- The deposit stock is a mod-owned value.

## Current state
Iteration 01 done: a mod ledger for iron, fed by the production counter; an empty deposit sets the production limit to 0. Iteration 02 done: salt and clay deposits, and iron and salt in the vassal tribute.

## Proven building blocks
- Mod state (deposit stock in region Tags): M01, `openspec/changes/archive/2026-10-15-legacy-24-mod-save-state/README.md`.
- Game data tables: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/game-data-tables.md`.
- Goods in and out of a store (`GiveItemByID`, `consumeGoodNoCheck`): `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S6.md`.
- Review of the deposit rules: `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-vassals.md`.

## Tunables (M00)
- Deposit size per resource, so that it lasts 2 to 4 game years at normal use.

## Dependencies
- M01. M07 and M08 supply the permanent goods.

## Open questions
1. How does the mod stop production when a deposit is empty? Answered: `Region:setProductionLimit(good, 0)` (iteration 01).
2. Which resources are finite? Iron, salt and clay (clay is an agent choice, TBD).
3. How is "normal use" defined for the 2 to 4 year target?
4. Does the player see the remaining stock?
5. Can the mod read the extraction output of a building each period? Yes: `ProductionTrackerComponent:getGoodsProducedOver` (iteration 01).

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | iron-deposit | One deposit (iron) counts down and ends output when empty. | pass, see [iterations/01-iron-deposit.md](iterations/01-iron-deposit.md) |
| 02 | more-resources | Salt and the other finite goods. | pass, see [iterations/02-more-resources.md](iterations/02-more-resources.md) |
