## ADDED Requirements
<!-- Issue: #386 -->

### Requirement: The plunder tick records the goods per Hussite raid
Each time the plunder tick takes goods from the village stores for a Hussite raid, the mod SHALL add the amount of each good to the plunder record of that raid. The record SHALL be kept in ModState and SHALL survive a save and load. A native raid SHALL have no record.

#### Scenario: The tick records what it takes
- **WHEN** the plunder tick takes 6 planks and 4 logs for a Hussite raid
- **THEN** the record of that raid holds 6 planks and 4 logs
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: The record survives a load
- **WHEN** the game is saved and loaded during a Hussite raid
- **THEN** the record of the raid is the same after the load
- Not checked yet.

#### Scenario: A native raid has no record
- **WHEN** a native Brigand raid plunders
- **THEN** the mod keeps no plunder record for it
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A delivered body of a Hussite raider gives its share to the corpse pit
The mod SHALL poll the corpse pit inventory entry `Type 233` (corpse) about once each game second. For each body that the pit receives, if the body belongs to a Hussite raid, the mod SHALL add the share of that body to the pit with `addToInventory`. The share of a good is the amount in the record of the raid divided by the raiders at the start of the raid, rounded down. The mod SHALL pay a share of one raid only once for each body. The mod SHALL NOT change the loot of the dead raider.

#### Scenario: One body is delivered
- **WHEN** a Hussite raid of 10 raiders has a record of 40 planks, and the body of one raider reaches the pit
- **THEN** the pit inventory gains 4 planks
- Checked by `mod/InvasionMod/scenarios/raid_behavior/pit_loot.py` (written, not run in the real game yet), on the default fixture `base-corpse-pit`.

#### Scenario: Rounding down
- **WHEN** the record holds 5 logs for 10 raiders and one body reaches the pit
- **THEN** the pit gains 0 logs
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Two bodies in one poll
- **WHEN** the corpse count of the pit rises by 2 between two polls
- **THEN** the pit gains two shares
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Native raids and a missing pit give nothing back
The mod SHALL NOT add goods to the pit for the body of a raider of a native raid. If no corpse pit exists, the mod SHALL add no goods and SHALL NOT add them to a store. The mod SHALL NOT start the give-back for bodies left on the ground.

#### Scenario: A native raider body reaches the pit
- **WHEN** the body of a native Brigand raider reaches the pit
- **THEN** the pit gains no goods from the mod
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: No pit
- **WHEN** a Hussite raider dies and no corpse pit exists
- **THEN** no goods are added to a pit or a store, and the mod logs no error
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
