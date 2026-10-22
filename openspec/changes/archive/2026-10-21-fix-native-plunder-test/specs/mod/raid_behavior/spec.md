## REMOVED Requirements
<!-- Issue: #373 -->

### Requirement: Bandit squads leave only in a quiet spot
**Reason**: Owner decision 2026-10-21. The feature steers Hussite raids. Native bandit raids are left to the game.
**Migration**: None. A bandit squad raid ends under the game's own rules.

### Requirement: The loot of a dead raider goes to the nearest store
**Reason**: Owner decision 2026-10-21. The corpse pit (#360) replaces the direct store add.
**Migration**: The loot stays with the body until the corpse pit change gives it back.

### Requirement: A native raid is left alone
**Reason**: Owner decision 2026-10-21. Its spec scenario "Native plunder" measured the game's AI, not the mod. The rule moves to the requirement "The mod never steers or removes a native raid".
**Migration**: None.

### Requirement: Every spawned raid is tracked
**Reason**: Owner decision 2026-10-21. Its spec scenario tested a native raid with a 20 day limit and the native leave line. The rule moves to "Every spawned raid is tracked by the game census", with a Hussite raid under the baron AI.
**Migration**: None.

## ADDED Requirements

### Requirement: The mod never steers or removes a native raid
<!-- Issue: #373 -->
The mod SHALL NOT steer or rout a raid that runs under the native plunder AI, and SHALL NOT remove its units.

#### Scenario: No removal of native raiders
- **WHEN** a native raid runs
- **THEN** the mod removes no raider
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Every spawned raid is tracked by the game census
<!-- Issue: #373 -->
The mod SHALL start a raid record when the invasion feature spawns a raid. The record SHALL hold the units that are new since the spawn. The count of living raiders SHALL equal the unit count read from the game census; a unit that the census no longer counts SHALL NOT count as living. A raid SHALL end as `left` when raiders walked off the map or the native leave line was seen, or as `destroyed` when all raiders died.

#### Scenario: A Hussite raid
- **WHEN** a Hussite raid runs under the baron AI
- **THEN** the tracker count of living raiders equals the game census count at every sample
- **AND** the raid ends as `left` or `destroyed`, with no limit on game days
- Checked by `mod/InvasionMod/scenarios/raid_behavior/carry_caps.py`.

#### Scenario: A raider that left the census
- **WHEN** a raider is still in the `SMUnit` list but the census no longer counts it
- **THEN** the tracker does not count it as living
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Units that existed before the spawn
- **WHEN** a raid spawns and other bandit units already exist
- **THEN** only the new units are raiders
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

