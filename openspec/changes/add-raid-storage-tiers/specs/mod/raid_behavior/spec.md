## ADDED Requirements
<!-- Issue: #276 -->

### Requirement: A store tier sets the share that raiders take
The mod SHALL give each store type a tier from the feature config. When a raid plunders a store, the share of goods that leaves the store SHALL depend on that tier. A guarded store SHALL lose a smaller share than an open store. The manor store SHALL be the safest tier.

#### Scenario: A guarded store against an open store
- **WHEN** the same raid plunders a guarded store and an open store that hold the same goods
- **THEN** the guarded store loses a smaller share than the open store
- **AND** both shares are between 0 and 100 percent of the goods
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`).

#### Scenario: The manor store
- **WHEN** a raid plunders the manor store and an open store with the same goods
- **THEN** the manor store loses the smallest share
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`).

### Requirement: A ruin from a raid rebuilds at partial cost
A building that a raid burned SHALL become a ruin. The player SHALL be able to rebuild the ruin for a part of the full building cost. The part is set by a rebuild discount in the feature config.

#### Scenario: Rebuilding a burned building
- **WHEN** a raid burns a building and the player rebuilds the ruin
- **THEN** the cost is between 1 and 99 percent of the full cost
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/ruin_rebuild.py`).
