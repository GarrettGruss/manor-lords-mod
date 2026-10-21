## ADDED Requirements
<!-- Issue: #276 -->

### Requirement: Stores have a tier
The mod SHALL give each store type a tier from the feature config. Tier 1 SHALL be the storehouse and the granary. Tier 2 SHALL be the manor storage. The mod SHALL steal only from tier 1 stores. The mod SHALL NOT steal from tier 2. In a game raid the game may rob any store, also the manor store; the mod SHALL NOT protect or restore it.

#### Scenario: A baron AI raid never robs the manor store
- **WHEN** a baron AI raid runs while the manor store and a tier 1 store both hold goods
- **THEN** the goods in the manor store are unchanged at the end of the raid
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`).

### Requirement: The game manages the loss in a game raid
In a game raid, where the game steers the raiders to pillage and steal, the mod SHALL NOT compute or remove stolen goods. The game SHALL manage the stolen goods.

#### Scenario: A game raid has no mod steal
- **WHEN** a game raid runs
- **THEN** the mod removes no goods from any store
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`).

### Requirement: Stealing units in a baron AI raid take goods from tier 1 stores
In a baron AI raid, where baron units cannot pillage or steal, the mod SHALL measure the distance of each baron unit to the battle marker. A unit farther than the steal distance threshold (feature config, 200 m for now; the army fights about 140 m from the marker) SHALL be a stealing unit. Each stealing unit SHALL take the steal rate (feature config, 10 goods per in-game day for now) from tier 1 stores only.

#### Scenario: A far unit steals
- **WHEN** a baron unit is farther than the threshold from the battle marker for one in-game day
- **THEN** tier 1 stores lose about the steal rate in total
- **AND** the manor store loses nothing
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py`).

#### Scenario: A near unit does not steal
- **WHEN** a baron unit stays within the threshold of the battle marker
- **THEN** no store loses goods because of that unit
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py`).

### Requirement: A baron AI raid has a steal goal
Each baron AI raid SHALL have a total steal goal from the feature config, scaled by game difficulty (for now 100 for a small raid and 300 for a large raid). The mod SHALL stop stealing when the goods taken by the raid reach the goal.

#### Scenario: Stealing stops at the goal
- **WHEN** stealing units of a small raid have taken the goal
- **THEN** no more goods are taken
- **AND** the total taken is not above the goal
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py`).

### Requirement: STRETCH: a Manor tech unlocks storage under the manor
As a stretch goal, the mod SHOULD add a tech "Manor" in a third, common branch of the tech tree. The tech SHALL unlock storage under the manor with the capacity and the job slots of a level 1 storehouse. The mod SHALL add one tech for now.

#### Scenario: Researching the Manor tech
- **WHEN** the player researches the Manor tech
- **THEN** the manor can hold goods up to the capacity of a level 1 storehouse
- **AND** the manor has the job slots of a level 1 storehouse
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/manor_storage_tech.py`).
