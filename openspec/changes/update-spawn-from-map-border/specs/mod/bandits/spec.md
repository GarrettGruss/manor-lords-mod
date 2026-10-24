## ADDED Requirements

<!-- Issue: #434 -->

### Requirement: Bandit bands arrive from the map border
When the mod spawns a bandit squad, the squad SHALL come in from the map border and SHALL NOT appear next to the village. The rules of the requirement `Spawned armies arrive from the map border` in `mod/invasion` apply: the game's arrival time first, a border point and a march order as the fallback, a valid point on walkable land.

#### Scenario: A bandit band enters at the border
- **WHEN** a conversion spawns a bandit squad
- **THEN** the squad starts at a border point at least 30000 game units from the village
- **AND** within 3 game days the squad is within 5000 game units of the village
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.

#### Scenario: A test spawn of bandits
- **WHEN** a test calls `bandit_spawn_at` with no point
- **THEN** the squad starts at a border point
- Checked by `harness/tests/test_fakegame_bandits.py`.

## MODIFIED Requirements

### Requirement: A conversion removes two families and spawns a bandit squad
A successful roll SHALL remove `families_per_conversion` (default 2) families through `homeless_rebel` and SHALL spawn one Brigands squad of 18 units for each `families_per_squad` (default 2) families. The squads SHALL arrive from the map border (requirement `Bandit bands arrive from the map border`). The village SHALL keep at least `min_families_left` (default 1) families. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** Public Order is under 25 and the roll is 0
- **THEN** 2 families are removed and 18 bandit units appear
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the roll wins
- **THEN** no family is converted
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The conversion banner
- **WHEN** a conversion succeeds
- **THEN** the banner `Families have turned to banditry` shows
- Not checked yet.
