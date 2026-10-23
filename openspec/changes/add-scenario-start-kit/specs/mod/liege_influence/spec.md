## ADDED Requirements
<!-- Issue: #425 -->

### Requirement: The liege screen has a button to request an arms shipment
The liege screen SHALL have a button "Request arms shipment". A click SHALL cost 200 silver and SHALL deliver 30 large shields and 30 spears to the manor store at once. The amounts and the cost SHALL come from config values. The mod SHALL take the silver only when the delivery succeeded.

#### Scenario: Buy a shipment
- **WHEN** the player has 200 or more silver, no cooldown runs, and the player clicks the button
- **THEN** the manor store holds 30 more large shields and 30 more spears
- **AND** the silver is 200 lower
- **AND** the button is disabled and shows the days left
- Checked by `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py` (proposed) and `harness/tests/test_fakegame_liege_influence.py` (proposed).

#### Scenario: A failed delivery costs nothing
- **WHEN** the delivery to the manor store fails
- **THEN** the silver and the cooldown day do not change and a log line says why
- Checked by `harness/tests/test_fakegame_liege_influence.py` (proposed).

### Requirement: The arms shipment has a cooldown
After a shipment the button SHALL be disabled for 180 game days (a config value). The button SHALL also be disabled, with the reason shown, when the silver is below 200. While it is disabled for the cooldown, it SHALL show the days left. The mod SHALL store the day of the last shipment in the mod state, so the cooldown is kept over a save and load.

#### Scenario: Not enough silver
- **WHEN** the player has less than 200 silver
- **THEN** the button is disabled and the reason names the missing silver
- **AND** a click delivers nothing and takes no silver
- Checked by `harness/tests/test_fakegame_liege_influence.py` (proposed).

#### Scenario: Cooldown
- **WHEN** a shipment came 100 game days ago
- **THEN** the button is disabled and shows 80 days left
- **AND** after 180 game days it is enabled again if the silver is enough
- Checked by `harness/tests/test_fakegame_liege_influence.py` (proposed).

#### Scenario: The cooldown is saved
- **WHEN** a shipment was bought, the game is saved and loads in a new run
- **THEN** the cooldown day is the same and the button shows the days left
- Not checked yet (proposed: fake game test of the mod state key; a real load needs the guarded `save_game`).
