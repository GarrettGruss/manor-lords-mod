## MODIFIED Requirements
<!-- Issue: #449 -->

### Requirement: A role raid is the army of an AI lord
With `roles.lord_army.enabled` (default on), the mod SHALL spawn a role raid as the army of the AI lord `Hussite Raiders`, at war with the player, with its battlefield at the player manor. The anchor SHALL be the player manor. If the player has no manor, the anchor SHALL be the average location of the buildings in the player home region. The anchor SHALL NOT depend on the camera. If that fails before any army exists, the mod SHALL spawn bandit squads instead. If it fails after some armies exist, the mod SHALL NOT spawn bandit squads on top, and SHALL try again on the next daily step.

#### Scenario: A lord raid
- **WHEN** a role raid spawns
- **THEN** the raid tracker reports `lord_raid = true`
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

#### Scenario: A failure after a partial spawn
- **WHEN** the lord raid fails after some armies were spawned
- **THEN** no bandit squads are added
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The player has a manor
- **WHEN** a role raid spawns and the player has a manor
- **THEN** the anchor is the location of the manor
- Checked by `mod/InvasionMod/scenarios/invasion/raid_anchor_manor.py` and `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: The player has no manor
- **WHEN** a role raid spawns and the player has no manor
- **THEN** the anchor is the average location of the buildings in the home region
- Checked by `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: The camera is over another region
- **WHEN** a role raid spawns while the camera is over a region that is not the home region
- **THEN** the anchor is the same as with the camera over the home region
- Checked by `mod/InvasionMod/scenarios/invasion/raid_anchor_manor.py` and `harness/tests/test_fakegame_harnessbattlefield.py`.
