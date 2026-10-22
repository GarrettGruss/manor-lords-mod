## MODIFIED Requirements

### Requirement: Every spawned raid is tracked
<!-- Issue: #373 -->
The mod SHALL start a raid record when the invasion feature spawns a raid. The record SHALL hold the units that are new since the spawn. The count of living raiders SHALL equal the unit count read from the game census; a unit that the census no longer counts SHALL NOT count as living. A raid SHALL end as `left` when raiders walked off the map or the native leave line was seen, or as `destroyed` when all raiders died.

#### Scenario: A one-squad native raid
- **WHEN** a raid of 1 squad (18 raiders) runs under the native plunder AI
- **THEN** the tracker count of living raiders equals the game census count at every sample
- **AND** the raid ends as `left` or `destroyed`, with no limit on game days
- **AND** when the raid ends as `left`, the native leave line is in the log
- Checked by `mod/InvasionMod/scenarios/raid_behavior/native_plunder.py`.

#### Scenario: A raider that left the census
- **WHEN** a raider is still in the `SMUnit` list but the census no longer counts it
- **THEN** the tracker does not count it as living
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Units that existed before the spawn
- **WHEN** a raid spawns and other bandit units already exist
- **THEN** only the new units are raiders
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
