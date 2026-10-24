## ADDED Requirements

<!-- Issue: #434 -->

### Requirement: Spawned armies arrive from the map border
When the mod spawns a hostile or arriving army, the army SHALL come in from the map border and SHALL NOT appear next to the target. The mod SHALL first try the game arrival time (`spawnArmy` with more than 0 days). Else it SHALL spawn the squads on a valid border point and order a march. Each squad SHALL start at least `min_spawn_distance` (default 30000 game units) from the target. The raid SHALL start at arrival.

#### Scenario: A lord raid enters at the border
- **WHEN** a role raid spawns
- **THEN** the first squad stands at a map border point or is off the map
- **AND** its distance from the player manor is at least 30000 game units
- **AND** between 1 and 3 game days later the squads are within 5000 game units of the target region
- Checked by `mod/InvasionMod/scenarios/invasion/border_arrival.py`.

#### Scenario: A great raid wave enters at the border
- **WHEN** a great raid wave spawns
- **THEN** all squads of the wave start at the border and none starts within 30000 game units of the manor
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

#### Scenario: The relief army enters at the border
- **WHEN** the relief army spawns
- **THEN** it starts at a border point and none of its squads starts within 30000 game units of the manor centre
- **AND** the army walks to the manor
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

#### Scenario: A raid stand-in enters at the border
- **WHEN** a test spawns a raid stand-in (no AI lord)
- **THEN** it starts at a border point
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The raid starts at arrival
- **WHEN** a raid is marching and has not arrived
- **THEN** the raid tracker reports no active raid and no leave rule fires
- **AND** after arrival the tracker reports the raid
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A border point is valid and near the target
A border point SHALL be the point of the map border nearest to the target region (`border_rule`, default `nearest`). The point SHALL be on walkable land, inside the playable area and not in water. If the nearest point is not valid, the mod SHALL use the next valid point along the border.

#### Scenario: The border point is valid
- **WHEN** the mod picks a border point for a target region
- **THEN** the point is on walkable land inside the playable area, not in water
- **AND** it is the nearest valid point to the region, or the next valid one along the border
- Checked by `harness/tests/test_fakegame_invasion.py`.

## MODIFIED Requirements

### Requirement: The raid spawns on the planned day
The mod SHALL spawn the planned yearly raid on the raid day, plus or minus 1 game day. The army SHALL arrive from the map border (requirement `Spawned armies arrive from the map border`), so the raid starts at arrival, on the raid day, plus or minus 1 game day. The raid size SHALL be the size multiplier of the size class times the Yearly player raid level, in squads. The size class SHALL be picked at random between small, medium and large with the multipliers 1, 2 and 3 (`size_multipliers`), unless the settings menu fixed it. At level 0 the mod SHALL plan and spawn no yearly raid.

#### Scenario: A medium raid at difficulty 2
- **WHEN** the raid day arrives for a medium raid at the yearly level 2
- **THEN** the raid has 4 squads (2 x 2)
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).

#### Scenario: A forced raid
- **WHEN** a test calls `invasion_force_next` after the plan exists
- **THEN** the raid spawns at the next check, and a second call is refused because the raid was spawned
- Checked by `harness/tests/test_fakegame_invasion.py`.

#### Scenario: The yearly level is 0
- **WHEN** the yearly level is 0 and a game year passes
- **THEN** no yearly raid is planned or spawned and no banner shows
- Checked by `harness/tests/test_fakegame_scenario_settings.py` (`LevelTests`).

### Requirement: A role raid is the army of an AI lord
With `roles.lord_army.enabled` (default on), the mod SHALL spawn a role raid as the army of the AI lord `Hussite Raiders`, at war with the player, with its battlefield at the player manor. The army SHALL arrive from the map border (requirement `Spawned armies arrive from the map border`). The anchor SHALL be the player manor. If the player has no manor, the anchor SHALL be the average location of the buildings in the player home region. The anchor SHALL NOT depend on the camera. If that fails before any army exists, the mod SHALL spawn bandit squads instead. If it fails after some armies exist, the mod SHALL NOT spawn bandit squads on top, and SHALL try again on the next daily step.

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

### Requirement: The great raid starts with waves
When the clock ends, the mod SHALL spawn one wave for each difficulty point. Each wave SHALL have `wave_squads` (default 15) squads. Waves SHALL be `wave_gap_days` (default 10) game days apart, counted from the arrival of the previous wave. Each wave SHALL arrive from the map border (requirement `Spawned armies arrive from the map border`). The mod SHALL NOT spawn a wave twice.

#### Scenario: The first wave at difficulty 1
- **WHEN** a test forces the clock to end at difficulty 1
- **THEN** wave 1 has 15 squads and exactly 1 wave spawns
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

### Requirement: A relief army and a final battle end the great raid
`relief_delay_days` (default 10) game days after the last wave, the mod SHALL spawn the relief army on the player side (15, 8 or 0 squads at difficulty 1, 2 or 3) and a hostile final army of `final_squads` (default 25) squads, not scaled by difficulty. Both armies SHALL arrive from the map border (requirement `Spawned armies arrive from the map border`). The relief army SHALL NOT appear at `relief_offset` from the manor centre. When the final army is dead, the phase SHALL become `won`.

#### Scenario: The relief army and the final army at difficulty 1
- **WHEN** the wait after the last wave is over
- **THEN** the relief army has 15 squads and spawned
- **AND** the final army has 25 squads
- **AND** the game still answers with all squads on the map
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

#### Scenario: The win
- **WHEN** the final army has no living unit
- **THEN** the phase is `won`
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
