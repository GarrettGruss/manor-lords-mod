## Purpose
<!-- Issue: #271 -->
The liege_influence feature keeps the influence of the player with the liege. Tribute to the liege raises it. Later steps spend it.

## ADDED Requirements

### Requirement: Influence is a saved value
The mod SHALL keep an influence value for the player in ModState. The value SHALL start at 0 on a new game. It SHALL come back after a save and a load. The command `InvasionMod.liege_state` SHALL show it.

#### Scenario: Influence survives a load
- **WHEN** the influence is above 0, the game is saved with the harness action `save_game`, and the slot is loaded
- **THEN** `liege_state` shows the same influence
- Not checked yet (planned: `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`).

#### Scenario: A new game
- **WHEN** a new game starts with the feature on
- **THEN** `liege_state` shows an influence of 0
- Not checked yet (planned: `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`).

### Requirement: Tribute to the liege raises influence
The command `InvasionMod.liege_send_tribute` SHALL take the amount from the player and raise the influence by the amount times `influence_per_unit`. A request that the player cannot pay SHALL be refused with a message. A refused request SHALL not change the influence or the stock.

#### Scenario: A paid tribute
- **WHEN** the player has enough stock and sends a tribute of 100 units
- **THEN** the stock falls by 100
- **AND** the influence rises by a value between 1 and 1000 (100 times `influence_per_unit`)
- Not checked yet (planned: `mod/InvasionMod/scenarios/liege_influence/send_tribute.py`).

#### Scenario: A tribute the player cannot pay
- **WHEN** the player sends more than the stock holds
- **THEN** the command is refused with a message
- **AND** the influence and the stock are unchanged
- Not checked yet (planned: `harness/tests/test_fakegame_liege_influence.py`).
