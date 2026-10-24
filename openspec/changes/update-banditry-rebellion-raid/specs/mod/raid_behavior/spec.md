## ADDED Requirements
<!-- Issue: #480 -->

### Requirement: A loot override replaces the loot of a unit
The mod SHALL keep a loot override state: a map from a unit key (`GetAddress` of the SMUnit, which is also the address of its body) to a list of goods. Any feature may set an entry. When the corpse pit pays out the body of a unit that has an entry, the mod SHALL add the goods of the entry to the pit (`addToInventory`) instead of the config loot, and SHALL clear the entry. A unit without an entry SHALL get the existing loot rules (the config values).

#### Scenario: A body with an override reaches the pit
- **WHEN** the body of a unit with the override `{spear}` reaches the pit
- **THEN** the pit gains one spear and the entry is cleared
- Checked by `harness/tests/test_fakegame_raid_behavior.py`. Real check: task 2.5 of `update-banditry-rebellion-raid`.

#### Scenario: A body without an override
- **WHEN** the body of a unit without an entry reaches the pit
- **THEN** the pit gets the same goods as before this requirement
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A loot override does not change plunder and does not survive a load
The override SHALL NOT change what the game plunders (`ItemsLooted` and carried goods stay as they are), so live plunder works next to it. The entry of a unit that vanishes (for example a squad that leaves the map) SHALL be cleared, and its goods are lost. The map is NOT saved: after a load it is empty (open question: the owner may want it in ModState).

#### Scenario: The squad leaves the map
- **WHEN** units with entries vanish without a body
- **THEN** their entries are cleared and no goods are paid
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Plunder next to an override
- **WHEN** a unit with an override also carries plundered goods
- **THEN** the mod does not change the plundered goods, and the pit pay-out is the override only
- Not checked yet.

#### Scenario: A load clears the map
- **WHEN** the game is saved and loaded
- **THEN** the map is empty and bodies give the normal loot
- Not checked yet.
