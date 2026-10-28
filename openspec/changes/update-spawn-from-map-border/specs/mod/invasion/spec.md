## ADDED Requirements

<!-- Issue: #434 -->

### Requirement: Spawned armies arrive from the map border
When the mod spawns a hostile army (a role raid, a great raid wave, the final army), the army SHALL come in from the map border and SHALL NOT appear next to the target. The mod SHALL spawn the squads at a valid border point (requirement `A border point is valid and near the target`). The AI lord of the army SHALL have a challenge at the target, so the army walks in on its own. Each squad SHALL start at least `min_spawn_distance` (default 30000 game units) from the target. The raid SHALL start at arrival: the army has arrived when a share (`arrival_share`, default 0.2) of its living raiders stand within `arrival_radius` (default 12000 game units) of the target, or after `max_march_days` (default 12) game days. If the map border cannot be read, the mod SHALL log the problem and spawn the army as before.

The game call `spawnArmy` has an arrival time argument. It does not delay a lord army (spike A), so the mod does not use it.

#### Scenario: A lord raid enters at the border
- **WHEN** a role raid spawns
- **THEN** the first squad stands outside the playable square, at a border point that is at least 30000 game units from the player manor
- **AND** the squads walk to the manor and the raid has arrived within `max_march_days` game days
- Checked by `mod/InvasionMod/scenarios/invasion/border_arrival.py` and `harness/tests/test_fakegame_border.py`.

#### Scenario: A great raid wave enters at the border
- **WHEN** a great raid wave or the final army spawns
- **THEN** each army has a border point and none starts within 30000 game units of the manor
- Checked by `mod/InvasionMod/scenarios/invasion/great_raid_waves.py`.

#### Scenario: The raid starts at arrival
- **WHEN** a raid is marching and has not arrived
- **THEN** no leave rule, no plunder and no steal acts, and the tracker lists no active raid (`active_raids`, `active_role_raid`)
- **AND** after arrival the start day of the raid is the arrival day, the loss share and the loot goal count from the raiders that arrived (not from the army that left the edge), and the rules act as before
- Checked by `harness/tests/test_fakegame_raid_behavior.py` (`MarchingRaidTests`).

#### Scenario: The map border cannot be read
- **WHEN** the map edge actor is not found
- **THEN** the log names the problem and the army starts near the manor as before
- Checked by `harness/tests/test_fakegame_border.py`.

### Requirement: A border point is valid and near the target
A border point SHALL be a point 3000 game units (`margin`) outside the playable square of the map (the map edge actor of the game), on the side that is nearest to the target (`rule`, default `nearest`) among the sides at least `min_spawn_distance` from the target, and at least 5000 game units (`inset`) from the corners. If no side is far enough, the farthest side SHALL be used. The game has no navigation mesh, so the point is not tested for walkable land by a query. Instead the points of all 8 compass places were run in the real game and every army walked in (spike B).

#### Scenario: The border point is valid
- **WHEN** the mod picks a border point for a target
- **THEN** the point is outside the playable square, on the nearest side that is far enough from the target, and away from the corners
- Checked by `harness/tests/test_fakegame_border.py`.

### Requirement: The game tells the player from which direction the raid comes
When a lord army is spawned at the border, the mod SHALL show a banner that names the direction in 8 compass words (north, north-east, east, south-east, south, south-west, west, north-west). The word SHALL come from the border point seen from the target. The banner of a yearly or subjugation raid SHALL read "Raiders approach from the <direction>" (or "The subjugation raid approaches from the <direction>") with the raider estimate. The banner of a great raid wave SHALL name the direction in its title. The banner of the relief army and the final army SHALL name the direction of the final army. When the army has arrived, a yearly or subjugation raid SHALL show "Raiders are here". The compass SHALL be set by `north_axis` (default `-y`: north is -y and east is +x).

#### Scenario: The direction notice
- **WHEN** a role raid spawns at the west border point
- **THEN** a banner reads "Raiders approach from the west"
- Checked by `mod/InvasionMod/scenarios/invasion/border_arrival.py` and `harness/tests/test_fakegame_border.py`.

#### Scenario: The direction words
- **WHEN** the direction is computed from the target to a point in each of the 8 sectors
- **THEN** the words are east, south-east, south, south-west, west, north-west, north and north-east for `north_axis` -y
- Checked by `harness/tests/test_fakegame_border.py`.

## MODIFIED Requirements

### Requirement: The raid spawns on the planned day
The mod SHALL plan the yearly raid for the raid day and SHALL spawn the army `march_lead_days` (default 5) game days before it, so the army arrives at the raid day, plus or minus 2 game days. The army SHALL come in from the map border (requirement `Spawned armies arrive from the map border`). Bandit squads (no lord army) spawn on the raid day. The raid size SHALL be the size multiplier of the size class times the Yearly player raid level, in squads. The size class SHALL be picked at random between small, medium and large with the multipliers 1, 2 and 3 (`size_multipliers`), unless the settings menu fixed it. At level 0 the mod SHALL plan and spawn no yearly raid. The banner days (`raid_banner_days`) count to the raid day.

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
`relief_delay_days` (default 10) game days after the arrival of the last wave, the mod SHALL spawn the relief army on the player side (15, 8 or 0 squads at difficulty 1, 2 or 3) and a hostile final army of `final_squads` (default 25) squads, not scaled by difficulty. The final army SHALL arrive from the map border (requirement `Spawned armies arrive from the map border`). The relief army SHALL appear at `relief_offset` from the player pawn, as before: a player squad cannot be moved from Lua and a friendly lord army crashed the game, so the relief army cannot walk in from the border (change `update-spawn-from-map-border`, notes `march-order.md`). When the final army is dead, the phase SHALL become `won`.

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
