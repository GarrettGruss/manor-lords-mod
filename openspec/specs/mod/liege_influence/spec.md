# mod/liege_influence Specification

## Purpose
The player is sworn to an off-screen liege. This feature lets the player pay silver from the lord treasury as tribute to the liege and earn influence. It keeps the influence value in ModState across saves and gives a custom tribute menu, because the game has no liege of its own.

## Requirements

### Requirement: Influence is a saved value
The mod SHALL keep an influence value for the player in ModState. The value SHALL start at 0 on a new game. It SHALL come back after a save and a load. The command `InvasionMod.liege_state` SHALL show it. Only contract rewards and contract penalties (see `mod/liege_contracts`) SHALL change it. A penalty SHALL NOT take it below 0. The value SHALL NOT decay over time and SHALL NOT have a cap.

#### Scenario: Influence survives a load
- **WHEN** the influence is above 0, the game is saved with the harness action `save_game`, and the slot is loaded
- **THEN** `liege_state` shows the same influence
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py` (updated: it sets the influence through a completed contract and not through a tribute).

#### Scenario: A new game
- **WHEN** a new game starts with the feature on
- **THEN** `liege_state` shows an influence of 0
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`.

#### Scenario: No decay
- **WHEN** the influence is above 0 and several game days pass with no contract event
- **THEN** the influence is unchanged
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: No cap
- **WHEN** contract rewards raise the influence above 1000
- **THEN** each reward still raises the influence
- Checked by `harness/tests/test_fakegame_liege_influence.py` (updated).

#### Scenario: A penalty stops at 0
- **WHEN** the influence is 5 and a contract penalty of 500 applies
- **THEN** the influence is 0
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

### Requirement: The liege screen has a button to request an arms shipment
The liege screen SHALL have a button "Request arms shipment". A click SHALL cost 200 silver and SHALL deliver 30 large shields and 30 spears to the manor store at once. The amounts and the cost SHALL come from config values. The mod SHALL take the silver only when the delivery succeeded. While no manor is built, the button SHALL be disabled (grey look, clicks ignored) and the reason "Build a manor first" SHALL show under it.

#### Scenario: Buy a shipment
- **WHEN** the player has 200 or more silver, no cooldown runs, a manor is built, and the player clicks the button
- **THEN** the manor store holds 30 more large shields and 30 more spears
- **AND** the silver is 200 lower
- **AND** the button is disabled and shows the days left
- Checked by `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py` and `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: A failed delivery costs nothing
- **WHEN** the delivery to the manor store fails
- **THEN** the silver and the cooldown day do not change and a log line says why
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: No manor built
- **WHEN** no manor is built
- **THEN** the button is disabled (grey look) and the text "Build a manor first" shows under it
- **AND** a click delivers nothing, takes no silver and starts no cooldown
- Checked by `harness/tests/test_fakegame_liege_influence.py` and `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`.

#### Scenario: A manor is built
- **WHEN** a manor is built, the silver is enough and no cooldown runs
- **THEN** the button is enabled (normal look) and no reason shows
- Checked by `harness/tests/test_fakegame_liege_influence.py` and `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py`.

### Requirement: The arms shipment has a cooldown
After a shipment the button SHALL be disabled for 180 game days (a config value). The button SHALL also be disabled, with the reason shown, when the silver is below 200. While it is disabled for the cooldown, it SHALL show the days left. A disabled button SHALL have the same grey look in every case (no manor, cooldown, not enough silver). The mod SHALL store the day of the last shipment in the mod state, so the cooldown is kept over a save and load.

#### Scenario: Not enough silver
- **WHEN** the player has less than 200 silver
- **THEN** the button is disabled (grey look) and the reason names the missing silver
- **AND** a click delivers nothing and takes no silver
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: Cooldown
- **WHEN** a shipment came 100 game days ago
- **THEN** the button is disabled (grey look) and shows 80 days left
- **AND** after 180 game days it is enabled again if the silver is enough
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: The cooldown is saved
- **WHEN** a shipment was bought, the game is saved and loads in a new run
- **THEN** the cooldown day is the same and the button shows the days left
- Checked by `harness/tests/test_fakegame_liege_influence.py` (the mod state entry `arms_last_day`). A real save and load is not run (needs the guarded `save_game`).
