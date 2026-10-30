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
