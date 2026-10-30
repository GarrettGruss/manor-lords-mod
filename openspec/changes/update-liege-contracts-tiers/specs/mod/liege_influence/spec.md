## MODIFIED Requirements
<!-- Issue: #TBD -->

### Requirement: The liege screen has a button to request an arms shipment
The button "Request arms shipment" SHALL be in the manor (the menu or panel of the manor building), not in the liege contracts window (owner decision 2026-10-30). The exact manor UI hook is checked in task 3.4 of the change. A click SHALL cost 200 silver and SHALL deliver 30 large shields and 30 spears to the manor store at once. The amounts and the cost SHALL come from config values. The mod SHALL take the silver only when the delivery succeeded. The cooldown rules do not change.

#### Scenario: Buy a shipment
- **WHEN** the player has 200 or more silver, no cooldown runs, and the player clicks the button in the manor
- **THEN** the manor store holds 30 more large shields and 30 more spears
- **AND** the silver is 200 lower
- **AND** the button is disabled and shows the days left
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py` and `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: A failed delivery costs nothing
- **WHEN** the delivery to the manor store fails
- **THEN** the silver and the cooldown day do not change and a log line says why
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: The button is in the manor only
- **WHEN** the liege contracts window is open
- **THEN** it shows no "Request arms shipment" button
- **AND** the manor shows the button, so no "Build a manor first" reason is needed
- Not checked yet. Planned: `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`.

#### Scenario: No manor built
- **WHEN** no manor is built
- **THEN** the manor has no menu, so the player cannot request a shipment
- **AND** nothing is delivered, no silver is taken and no cooldown starts
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: A manor is built
- **WHEN** a manor is built, the silver is enough and no cooldown runs
- **THEN** the button in the manor is enabled (normal look) and no reason shows
- Not checked yet. Planned: `harness/tests/test_fakegame_liege_influence.py` and `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`.
