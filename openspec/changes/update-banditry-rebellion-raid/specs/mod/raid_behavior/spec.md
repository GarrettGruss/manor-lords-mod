## ADDED Requirements
<!-- Issue: #480 -->

### Requirement: A loot override replaces the loot of a unit
The mod SHALL keep a loot override state: a map from a unit key (`GetAddress` of the SMUnit, which is also the address of its body, in memory; the saved key is fixed by task 2.8) to a list of goods. Any feature may set an entry. When the corpse pit pays out the body of a unit that has an entry, the mod SHALL add the goods of the entry to the pit (`addToInventory`) instead of the config loot, and SHALL clear the entry. A unit without an entry SHALL get the existing loot rules (the config values).

#### Scenario: A body with an override reaches the pit
- **WHEN** the body of a unit with the override `{spear}` reaches the pit
- **THEN** the pit gains one spear and the entry is cleared
- Checked by `harness/tests/test_fakegame_raid_behavior.py`. Real check: task 2.5 of `update-banditry-rebellion-raid`.

#### Scenario: A body without an override
- **WHEN** the body of a unit without an entry reaches the pit
- **THEN** the pit gets the same goods as before this requirement
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A loot override does not change plunder
The override SHALL NOT change what the game plunders (`ItemsLooted` and carried goods stay as they are), so live plunder works next to it. The entry of a unit that leaves the map SHALL be dropped, and its goods are lost.

#### Scenario: The squad leaves the map
- **WHEN** units with entries vanish without a body
- **THEN** their entries are cleared and no goods are paid
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Plunder next to an override
- **WHEN** a unit with an override also carries plundered goods
- **THEN** the mod does not change the plundered goods, and the pit pay-out is the override only
- Not checked yet.

### Requirement: The loot override map is saved with the game
While a unit with an entry is alive on the map, the mod SHALL keep the entry in the save through ModState (fixed string slots in the Tags of the player pawn, written in place, never removed). The entry SHALL use a unit key that is the same before and after a load (fixed by spike task 2.8 of `update-banditry-rebellion-raid`). The mod SHALL NOT call a save function.

#### Scenario: A save and a load round trip
- **WHEN** a rebellion squad with entries is alive, the harness saves with `save_game`, and the slot is loaded in a new run
- **THEN** the entries are linked to the units again
- **AND** the body of a killed unit gives its override goods at the pit
- Not checked yet. Planned: `mod/InvasionMod/scenarios/bandits/rebellion_loot_roundtrip.py` (task 2.9).

### Requirement: A load links or drops each saved entry
After a load the mod SHALL link each saved entry to its unit again, and SHALL drop and log an entry whose unit is not found.

#### Scenario: A saved entry whose unit is gone
- **WHEN** a load finds an entry whose unit does not exist
- **THEN** the entry is dropped, its slot is empty and an event is logged
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A saved entry follows the unit to its body and is limited by slots
When the unit dies, the entry SHALL move to its body and stay saved until the pit pays out or the body disappears (about 30 game days, owner accepted). When all slots are full the mod SHALL log an error and drop the new entry.

#### Scenario: All slots are full
- **WHEN** an entry is set while all slots hold entries
- **THEN** the mod logs an error and the new unit gives the config loot
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A unit with an entry dies
- **WHEN** a unit with an entry dies and the game is saved and loaded
- **THEN** the body keeps the entry until the pit pays out
- Not checked yet.
