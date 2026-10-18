# M10 iteration 01: iron-deposit

Branch: `feat/M10-finite_resources-01-iron-deposit` (stacked on M12.04, PR #219). Issue: #222.

## Goal
One home deposit (iron) counts down with use and ends the output when empty. The stock is mod-owned (M00).

## Spike: how are deposits represented, and can Lua cap or deplete them?
Notes: `../implementation-notes/iteration-01-iron-deposit.md`. Short answer:
- The game has real finite deposits (struct `Ore`, `SavedDeposit.Limit`, `ResourceNodeProperties.bIsLimitedResource`, class `DepositDecal`), but on the `base` fixture `RTSMultiEngineCPP.deposits` is empty, there is no `DepositDecal` object, and the 35 `ResourceNode` actors hold only surface goods (berries, fish, stone, mushrooms, eel). No iron, salt or clay node was found. So the mod cannot read or write a game deposit there.
- Production can be read: `ProductionTrackerComponent:getGoodsProducedOver(days)` of each building (a table of good to units).
- Production can be stopped: `Region:setProductionLimit(good, 0)` (the workplace limit rule). Real game: a good with a running producer stopped at once (run below).

## Design
- Ledger per resource in ModState: `fin_<name>_mined` and `fin_<name>_last` (the last production total, to count only new units).
- A scheduler poll (5 s real time) sums the production of the player buildings, counts the new units, and when the stock is used up sets the production limit of the good to 0. Goods from vassal tribute are not counted and not blocked.
- Config `finite_resources.resources.iron = { good = 14 (IronOre), size = 400 }` (TBD; 2 to 4 game years at normal use needs a measured use rate).
- Commands `finite_resources_state`, and session-only `finite_resources_test_set` and `_test_clear`.

## Acceptance criteria
- D1 start full, no limit. D2 production counts the stock down. D3 empty sets limit 0. D4 production of the good stops (at most 2 units in 3 game days). D5 the limit can be lifted.
- Fake game: counting, first look, fall of the total, empty limit, tags (`test_fakegame_finite_resources.py`).

## Result
PASS in the real game (2026-10-18), base fixture. Runs `20261018-103614-434f` and `20261018-103826-5ac9` pass (D1 to D5). A real iron mine could not be placed (real mouse), so the scenario lends the deposit to a good that the saved game already produces (good 216, 136 units produced): the count fell 4 to 0, the limit became 0, and the total stayed at 139 for 3 game days.
Open: a test with a real iron mine; the use rate for the 2 to 4 year target; player-visible stock (no UI yet); what the AI lords do (limit is for the player region only).
