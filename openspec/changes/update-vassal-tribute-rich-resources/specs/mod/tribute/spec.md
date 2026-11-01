## MODIFIED Requirements
<!-- Issue: #552 -->

### Requirement: Vassals pay goods each season
At each game month change the mod SHALL pay goods into a player store for each handed-over vassal. No goods SHALL move between regions. The payment SHALL be `base x policy factor` units of each rich resource of the vassal region. The base SHALL be 100 (`tribute.base`). The policy factor SHALL be 0.5 for `light`, 1.0 for `fair` and 1.5 for `heavy`, so a vassal pays 50, 100 or 150 units of each good. The result SHALL be rounded to a whole number. A vassal SHALL pay 2 goods. The share, the production by families and the goods list `tribute.goods` (fish and timber) SHALL NOT be used.

#### Scenario: A season change with one vassal
- **WHEN** one `fair` vassal is registered, its region has 2 rich resources, and the month changes
- **THEN** the home stores gain 100 units of each of the 2 goods (200 in total)
- **AND** the game runs without a crash
- Not checked yet (planned: `mod/InvasionMod/scenarios/tribute/tribute_rich.py`, new).

#### Scenario: Payout rules without the game
- **WHEN** the amount is computed for `light`, `fair`, `heavy` and for an unknown policy
- **THEN** the amounts are 50, 100, 150 and 100 (an unknown policy counts as `fair`)
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`, updated).

### Requirement: Tribute is paid once for each season change
The mod SHALL pay at most one tribute for each game month change and none while the month stays. The mod SHALL NOT pay on the first poll after a load. A month change with no handed-over vassal SHALL pay nothing. A vassal that is rebuilding, or whose slot has no lord, SHALL pay nothing.

#### Scenario: Two polls in one season
- **WHEN** the month changes once and the poll runs several times
- **THEN** exactly one payment happens
- **AND** a month change with no vassal pays 0
- Not checked yet (planned: `mod/InvasionMod/scenarios/tribute/tribute_payout.py`, updated).

#### Scenario: The first poll
- **WHEN** the mod loads and polls for the first time
- **THEN** no tribute is paid
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`, updated).

#### Scenario: A rebuilding vassal
- **WHEN** a vassal is rebuilding and the month changes
- **THEN** that vassal pays nothing
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

### Requirement: The policy factor scales the tribute
The mod SHALL multiply the base amount by the tribute factor of the vassal policy (0.5 `light`, 1.0 `fair`, 1.5 `heavy`). The factor SHALL scale every paid good. The tech tree factor set by `set_share_factor` SHALL keep multiplying the amount.

#### Scenario: Heavy and light policies
- **WHEN** a month changes with a `heavy` vassal and with a `light` vassal
- **THEN** each good is 1.5 times and 0.5 times the `fair` amount
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`, updated).

## ADDED Requirements

### Requirement: Only rich resources are paid
The mod SHALL pay only goods that are rich in the region of the vassal. It SHALL read them at run time, with no table of regions. It SHALL match a node to a region with `getRegionByPos(position, true)` on the decal position. The next requirement says how a node is rich.

#### Scenario: Goods of other regions
- **WHEN** region A has a rich stone deposit and region B has none
- **THEN** a vassal in region B does not pay stone
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

### Requirement: A node is rich by decal size or clump capacity
The mod SHALL use these rules:
- Ore, clay, salt, stone: a `depositMaterial*` decal with `DecalSize.X` of at least `tribute.rich.decal_size` (5000).
- Berries, fish, eel, mushrooms: `resourceClumps` with a capacity sum of at least `tribute.rich.clump_capacity` (berries 130, fish and eel 385, mushrooms 122).

#### Scenario: A region with a rich deposit and a rich clump node
- **WHEN** a region holds a stone deposit with a decal width of 5000 or more and a mushroom node with a clump capacity of 122 or more
- **THEN** the detected rich resources of the region are stone and mushrooms
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

#### Scenario: A poor node is ignored
- **WHEN** a deposit decal is smaller than 5000, or the clump capacity is below the limit
- **THEN** that good is not detected for the region
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

#### Scenario: Real regions on the test map
- **WHEN** the vassals Krumme Leite and Hochweg of the test map pay one month
- **THEN** Krumme Leite pays stone and salt, and Hochweg pays mushrooms and flax
- Not checked yet (planned: `mod/InvasionMod/scenarios/tribute/tribute_rich.py`).

### Requirement: Game and rich soil are not detected
The mod SHALL NOT count game (hunting area) as a rich resource. Rich game is not readable from Lua (spike `spike-rich-game-detection`, owner decision 2026-11-01). The mod SHALL NOT detect rich soil. The goods ids SHALL be: iron 14, clay 146, salt 145, stone 27 (rough stone), berries 171, mushrooms 279, carp 30, eel 32, flax 11.

#### Scenario: Game never counts
- **WHEN** a region holds a hunting area
- **THEN** game is not a detected rich resource and is not paid
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

### Requirement: A region with one detected rich resource pays flax as the second good
A vassal region SHALL pay 2 goods. When the mod detects exactly 1 rich resource in the region, the second good SHALL be flax (good 11), the stand-in for rich soil. The flax amount SHALL follow the same base and policy factor. If a method to detect rich soil is found, a region with rich soil SHALL count it and pay flax for it.

#### Scenario: One detected rich resource
- **WHEN** a region has exactly 1 detected rich resource, for example mushrooms
- **THEN** the vassal pays that good and flax, each 100 units for a `fair` vassal
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

### Requirement: The rich resources of a region are read once
The mod SHALL read the rich resources of a region once, at the first tribute tick that needs them, and SHALL keep the result in memory for the session. The mod SHALL NOT save the cache in mod state. After a load the mod SHALL read the nodes again.

#### Scenario: Two ticks read the nodes once
- **WHEN** a vassal pays in two months
- **THEN** the nodes of its region are scanned once
- Not checked yet (planned: `harness/tests/test_fakegame_tribute.py`).

#### Scenario: The same result after a load
- **WHEN** the game is saved and loaded, and the vassal pays again
- **THEN** the paid goods are the same as before the load
- Not checked yet (planned: `mod/InvasionMod/scenarios/tribute/tribute_rich.py`).

## REMOVED Requirements

### Requirement: Vassals also pay finite goods
**Reason**: Iron and salt are paid only when they are rich in the region (requirement "Only rich resources are paid"). There is no fixed iron and salt for each family any more.
**Migration**: Remove `tribute.finite_goods` and `finite_paid` in `tribute_state`. Change the test scenario `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py` to check the new rule.
