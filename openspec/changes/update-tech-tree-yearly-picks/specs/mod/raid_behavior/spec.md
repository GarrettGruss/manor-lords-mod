## MODIFIED Requirements
<!-- Issue: #499 -->

### Requirement: A delivered body of a Hussite raider gives its share to the corpse pit
While the law Strip the Dead (`mod/tech_tree`) is in force, the mod SHALL poll the corpse pit inventory entry `Type 233` (corpse) about once each game second. For each body that the pit receives, if the body belongs to a Hussite raid, the mod SHALL add the share of that body to the pit with `addToInventory`. The share of a good is the amount in the record of the raid divided by the raiders at the start of the raid, rounded down. The mod SHALL pay a share of one raid only once for each body. The mod SHALL NOT change the loot of the dead raider. While the law is not in force, the mod SHALL add no goods for any body (this was always on before the change `update-tech-tree-yearly-picks`).

#### Scenario: One body is delivered
- **WHEN** Strip the Dead is in force, a Hussite raid of 10 raiders has a record of 40 planks, and the body of one raider reaches the pit
- **THEN** the pit inventory gains 4 planks
- Checked by `mod/InvasionMod/scenarios/raid_behavior/pit_loot.py` (real run 20261023-032125-a80d passed before the change; rerun with the law enacted: see the pull request).

#### Scenario: The law is not in force
- **WHEN** Strip the Dead is not in force and the body of a Hussite raider reaches the pit
- **THEN** the pit gains no goods
- Checked by `harness/tests/test_fakegame_raid_behavior.py` (the Hussite part is covered by the rules; the body count of a Hussite raid is consumed without pay-out).

#### Scenario: Rounding down
- **WHEN** the record holds 5 logs for 10 raiders and one body reaches the pit
- **THEN** the pit gains 0 logs
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Two bodies in one poll
- **WHEN** the corpse count of the pit rises by 2 between two polls
- **THEN** the pit gains two shares
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Native raids and a missing pit give nothing back
The mod SHALL NOT add goods to the pit for the body of a raider of a native raid, except while Strip the Dead is in force (see `mod/tech_tree`). Then the goods come from the loot override of the body when it has one, else from the table `raid_behavior.body_loot`: one list of loot variants for each body kind (`bandit`, `soldier`), each variant with an optional weight (default 1), and the mod draws one variant at random for each body. The kind `soldier` has no variants yet (the owner has not given values), and the mod cannot tell a soldier body from another body at the pit, so only the dead raiders that the mod tracked are looted. If no corpse pit exists, the mod SHALL add no goods and SHALL NOT add them to a store. The mod SHALL NOT start the give-back for bodies left on the ground.

#### Scenario: A native raider body reaches the pit
- **WHEN** Strip the Dead is not in force and the body of a native Brigand raider reaches the pit
- **THEN** the pit gains no goods from the mod
- Checked by `harness/tests/test_fakegame_raid_behavior.py` and `mod/InvasionMod/scenarios/tech_tree/strip_the_dead.py`.

#### Scenario: A native raider body under Strip the Dead
- **WHEN** Strip the Dead is in force and the body of a native Brigand reaches the pit
- **THEN** the pit gains one variant of the entry for its kind in `raid_behavior.body_loot` (the Brigand entry has two variants of equal weight: 1 sword and 1 small shield, with or without 1 helmet), or the goods of its loot override when it has one
- Checked by `harness/tests/test_fakegame_raid_behavior.py` and `mod/InvasionMod/scenarios/tech_tree/strip_the_dead.py`.

#### Scenario: No pit
- **WHEN** a Hussite raider dies and no corpse pit exists
- **THEN** no goods are added to a pit or a store, and the mod logs no error
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
