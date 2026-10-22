## MODIFIED Requirements
<!-- Issue: #360 -->

### Requirement: The loot of a dead raider goes to the nearest store
When a raider dies in the village, the mod SHALL add its loot to the store that is nearest to the place of death, in the good that the store holds most of (`fallback_good` if the store is empty). If there is no store, the loot SHALL be counted as lost. A raider that walks off the map at or below `exit_y` (default -85000) SHALL keep its loot and count as a departure. When a corpse pit exists and the body of the raider is brought to it, the mod SHALL spawn the loot at the corpse pit instead of adding it to a store.

#### Scenario: A death near a far store
- **WHEN** a raider dies nearer to a far store than to a near store
- **THEN** the loot goes to the far store
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Eighteen raiders die with loot
- **WHEN** 18 raiders that carry loot are killed
- **THEN** the tracker counts 18 deaths and the returned goods equal the carried loot
- **AND** the village stock rises by the same amount and nothing is lost
- Checked by `mod/InvasionMod/scenarios/raid_behavior/loot_return.py`.

#### Scenario: A body reaches the corpse pit
- **WHEN** villagers bring the body of a raider that carried loot to the corpse pit
- **THEN** the loot of that raider spawns at the corpse pit
- Not checked yet.

#### Scenario: No corpse pit
- **WHEN** a raider dies with loot and no corpse pit exists, or its body is not collected
- **THEN** the loot goes to the nearest store as before
- Not checked yet.
