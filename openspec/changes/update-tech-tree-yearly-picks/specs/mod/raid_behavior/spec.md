## MODIFIED Requirements
<!-- Issue: #499 -->

### Requirement: A delivered body of a Hussite raider gives its share to the corpse pit
While the law Strip the Dead (`mod/tech_tree`) is in force, the mod SHALL poll the corpse pit inventory entry `Type 233` (corpse) about once each game second. For each body that the pit receives, if the body belongs to a Hussite raid, the mod SHALL add the share of that body to the pit with `addToInventory`. The share of a good is the amount in the record of the raid divided by the raiders at the start of the raid, rounded down. The mod SHALL pay a share of one raid only once for each body. The mod SHALL NOT change the loot of the dead raider. While the law is not in force, the mod SHALL add no goods for any body (this was always on before the change `update-tech-tree-yearly-picks`).

#### Scenario: One body is delivered
- **WHEN** Strip the Dead is in force, a Hussite raid of 10 raiders has a record of 40 planks, and the body of one raider reaches the pit
- **THEN** the pit inventory gains 4 planks
- Checked by `mod/InvasionMod/scenarios/raid_behavior/pit_loot.py` (real run 20261023-032125-a80d passed without the law; to rerun with the law enacted).

#### Scenario: The law is not in force
- **WHEN** Strip the Dead is not in force and the body of a Hussite raider reaches the pit
- **THEN** the pit gains no goods
- Not checked yet (planned: `harness/tests/test_fakegame_raid_behavior.py`, updated).

#### Scenario: Rounding down
- **WHEN** the record holds 5 logs for 10 raiders and one body reaches the pit
- **THEN** the pit gains 0 logs
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Two bodies in one poll
- **WHEN** the corpse count of the pit rises by 2 between two polls
- **THEN** the pit gains two shares
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Native raids and a missing pit give nothing back
The mod SHALL NOT add goods to the pit for the body of a raider of a native raid, except while Strip the Dead is in force (see `mod/tech_tree`). Then the goods come from the loot override of the body when it has one, else from the table `raid_behavior.body_loot` (one entry per unit type). If no corpse pit exists, the mod SHALL add no goods and SHALL NOT add them to a store. The mod SHALL NOT start the give-back for bodies left on the ground.

#### Scenario: A native raider body reaches the pit
- **WHEN** Strip the Dead is not in force and the body of a native Brigand raider reaches the pit
- **THEN** the pit gains no goods from the mod
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A native raider body under Strip the Dead
- **WHEN** Strip the Dead is in force and the body of a native Brigand reaches the pit
- **THEN** the pit gains the goods of the entry for its unit type in `raid_behavior.body_loot`, or the goods of its loot override when it has one
- Not checked yet (planned: `harness/tests/test_fakegame_raid_behavior.py`, updated).

#### Scenario: No pit
- **WHEN** a Hussite raider dies and no corpse pit exists
- **THEN** no goods are added to a pit or a store, and the mod logs no error
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
