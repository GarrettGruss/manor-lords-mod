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
Not started.

## Proven building blocks
- Mod state (deposit stock in region Tags): M01, `docs/harness/24-mod-save-state/README.md`.
- Game data tables: `docs/harness/10-invasion-testability/implementation-notes/game-data-tables.md`.
- Goods in and out of a store (`GiveItemByID`, `consumeGoodNoCheck`): `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md`.
- Review of the deposit rules: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-vassals.md`.

## Tunables (M00)
- Deposit size per resource, so that it lasts 2 to 4 game years at normal use.

## Dependencies
- M01. M07 and M08 supply the permanent goods.

## Open questions
1. How does the mod stop production when a deposit is empty: block the production building, remove the output, or hide the deposit? (M00 does not say.)
2. Which resources are finite? M00 names iron and salt only ("and similar").
3. How is "normal use" defined for the 2 to 4 year target?
4. Does the player see the remaining stock?
5. Can the mod read the extraction output of a building each period?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | iron-deposit | One deposit (iron) counts down and ends output when empty. | not started |
| 02 | more-resources | Salt and the other finite goods. | not started |
