## 1. Spikes (notes in `notes/`)

- [ ] 1.1 Find the item ids of the large shield and the spear (data tables, `GetEquippedID` ids of `docs/wiki/concepts/unit-templates.md`, item data in the pak). Write `notes/item-ids.md`.
- [ ] 1.2 Find the call that adds villagers to a new game (for example `settleRegion` or `Region:AddNewFamily`) and how to reach exactly 10 people. Write `notes/villager-call.md`.
- [ ] 1.3 Find where `GiveItemByID` goods go at the start of a new game (store or none). Decide the fallback (pile at the manor). Write `notes/goods-target.md`.

## 2. Code

- [ ] 2.1 Add config values for the kit amounts and item ids.
- [ ] 2.2 Give the kit in `scenario_settings` after "Begin the game" in a new game only; store "kit given" in ModState.
- [ ] 2.3 Add a command to read the kit state for tests.

## 3. Tests

- [ ] 3.1 Fake game tests: new game gives the kit; loaded save does not; second apply does not.
- [ ] 3.2 Test scenario `scenario_settings/start_kit.py` in the real game.
- [ ] 3.3 Take a picture (`ctx.screenshot`) of the stock and the population; put it in `evidence/`.

## 4. Close

- [ ] 4.1 Update the wiki and `CHANGELOG.md` (Unreleased).
- [ ] 4.2 Run the full test set and `openspec validate add-scenario-start-kit --strict`.
- [ ] 4.3 Archive as the last commit: `openspec archive add-scenario-start-kit --yes`.
