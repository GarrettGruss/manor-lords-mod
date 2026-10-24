## 1. Spikes (notes in `notes/`)

- [x] 1.1 Find the item ids of the large shield and the spear (data tables, `GetEquippedID` ids of `docs/wiki/concepts/unit-templates.md`, item data in the pak). Write `notes/item-ids.md`.
- [x] 1.2 Find the call that adds villagers to a new game (for example `settleRegion` or `Region:AddNewFamily`) and how to reach exactly 10 people. Write `notes/villager-call.md`.
- [x] 1.3 Find the call that puts goods into the manor store (see `HarnessManor`, `manor_stronghold`; `GiveItemByID` goes to the region stock, which may not be the manor store). Decide the fallback. Write `notes/manor-store-delivery.md`.
- [x] 1.4 Find how to add a button to the liege screen (see `liege_influence` and its menu) and how to disable it with a reason text. Write `notes/liege-button.md`.

## 2. Code

- [x] 2.1 Config values: villagers 10, start silver 300, shipment cost 200, shipment goods (ids and amounts), cooldown 180 days.
- [x] 2.2 `scenario_settings`: give the kit (villagers, silver) after "Begin the game" in a new game only; store "kit given" in ModState.
- [x] 2.3 `liege_influence`: button "Request arms shipment" with the rules in the delta spec; take silver only after a successful delivery; store the last shipment day in ModState.
- [x] 2.4 Commands to read the kit state and the shipment state for tests.

## 3. Tests

- [x] 3.1 Fake game tests in `test_fakegame_scenario_settings.py`: new game gives the kit; loaded save does not; second apply does not.
- [x] 3.2 Fake game tests in `test_fakegame_liege_influence.py`: buy, not enough silver, cooldown, failed delivery, saved cooldown key.
- [x] 3.3 Test scenarios `scenario_settings/start_kit.py` and `liege_influence/arms_shipment.py` in the real game.
- [x] 3.4 Take pictures (`ctx.screenshot`) of the liege screen with the button (enabled, and disabled with days left); put them in `evidence/`.

## 4. Close

- [x] 4.1 Update the wiki and `CHANGELOG.md` (Unreleased).
- [x] 4.2 Run the full test set and `openspec validate add-scenario-start-kit --strict`.
- [x] 4.3 Archive as the last commit: `openspec archive add-scenario-start-kit --yes`.
