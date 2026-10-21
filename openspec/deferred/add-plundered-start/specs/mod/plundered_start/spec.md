## Purpose
<!-- Issue: #274 -->
The plundered_start feature makes a new game start in a damaged village. It runs the start sack once and never again for that game.

## ADDED Requirements

### Requirement: The start sack runs once in a new game
In a new game the mod SHALL run the start sack once, in the first game days. The sack SHALL take a share of the buildings, the stock and the people, set in the feature config. The mod SHALL save a start-done flag in ModState. After a load with the flag set, the mod SHALL NOT run the sack again.

#### Scenario: A new game
- **WHEN** a new game starts with the feature on
- **THEN** the sack runs once within the first 3 game days
- **AND** buildings, stock and families each fall by their configured share, between 1 and 90 percent
- **AND** the start-done flag is set
- Not checked yet (planned: `mod/InvasionMod/scenarios/plundered_start/start_sack.py`).

#### Scenario: A load after the start sack
- **WHEN** the game is saved with the harness action `save_game` and the slot is loaded
- **THEN** the start sack does not run again
- **AND** the number of buildings and families is the same as before the save
- Not checked yet (planned: `mod/InvasionMod/scenarios/plundered_start/start_sack_once.py`).

### Requirement: The village stays playable
The start sack SHALL leave the village alive. It SHALL leave at least one family and at least one building of the player. The game SHALL not end because of the sack.

#### Scenario: The largest share
- **WHEN** the start sack runs with the largest share that the config allows
- **THEN** at least 1 family and 1 building remain
- **AND** the game is still running 10 game days later
- Not checked yet (planned: `mod/InvasionMod/scenarios/plundered_start/start_sack.py`).
