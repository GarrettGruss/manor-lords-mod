## RENAMED Requirements
<!-- Issue: #552 -->

- FROM: `### Requirement: Vassals pay goods each season`
- TO: `### Requirement: Vassals pay goods each month`

- FROM: `### Requirement: Tribute is paid once for each season change`
- TO: `### Requirement: Tribute is paid once for each month change`

## MODIFIED Requirements

### Requirement: Vassals pay goods each month
At each game month change the mod SHALL pay goods into a player store for each handed-over vassal. No goods SHALL move between regions. The payment SHALL be `base x policy factor` units of each of 2 goods of the vassal region. The base SHALL be 100 (`tribute.base`). The policy factor SHALL be 0.5 for `light`, 1.0 for `fair` and 1.5 for `heavy`, so a vassal pays 50, 100 or 150 units of each good. The result SHALL be rounded to a whole number. A vassal SHALL always pay 2 goods (see "A region always pays two goods"). The share, the production by families and the goods list `tribute.goods` (fish and timber) SHALL NOT be used. The game month SHALL be read from `TemporalComponent.month`.

#### Scenario: A season change with one vassal
- **WHEN** one `fair` vassal is registered and the month changes
- **THEN** the home stores gain 100 units of each of the 2 goods (200 in total)
- **AND** the game runs without a crash
- Checked by `mod/InvasionMod/scenarios/tribute/tribute_payout.py` and `tribute_rich.py`.

#### Scenario: Payout rules without the game
- **WHEN** the amount is computed for the factors 0.5, 1.0 and 1.5
- **THEN** the amounts are 50, 100 and 150
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: Tribute is paid once for each month change
The mod SHALL pay at most one tribute for each game month change and none while the month stays. A change of the season inside the same month SHALL pay nothing. The mod SHALL NOT pay on the first poll after a load. A month change with no handed-over vassal SHALL pay nothing. A vassal that is rebuilding, or whose slot has no lord, SHALL pay nothing.

#### Scenario: Two polls in one season
- **WHEN** the month changes once and the poll runs several times
- **THEN** exactly one payment happens
- **AND** a month change with no vassal pays 0
- Checked by `harness/tests/test_fakegame_tribute.py` and `mod/InvasionMod/scenarios/tribute/tribute_payout.py`.

#### Scenario: The first poll
- **WHEN** the mod loads and polls for the first time
- **THEN** no tribute is paid
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: A rebuilding vassal
- **WHEN** a vassal is rebuilding and the month changes
- **THEN** that vassal pays nothing
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: The policy factor scales the tribute
The mod SHALL multiply the base amount by the tribute factor of the vassal policy (0.5 `light`, 1.0 `fair`, 1.5 `heavy`). An unknown policy SHALL count as `fair`. The factor SHALL scale every paid good. The tech tree factor set by `set_share_factor` SHALL keep multiplying the amount.

#### Scenario: Heavy and light policies
- **WHEN** a month changes with a `heavy` vassal and with a `light` vassal
- **THEN** each good is 1.5 times and 0.5 times the `fair` amount
- Checked by `harness/tests/test_fakegame_tribute.py` and `mod/InvasionMod/scenarios/tribute/tribute_rich.py`.

## ADDED Requirements

### Requirement: Only rich resources are paid
The mod SHALL pay only goods that are rich in the region of the vassal, and flax as the stand-in for rich soil (see "A region always pays two goods"). It SHALL read the rich resources at run time, with no table of regions. It SHALL match a node to a region with `getRegionByPos(position, true)` on the decal position. The next requirement says how a node is rich.

#### Scenario: Goods of other regions
- **WHEN** region A has a rich stone deposit and region B has none
- **THEN** a vassal in region B does not pay stone
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: A node is rich by decal size or clump capacity
The mod SHALL use these rules:
- Ore, clay, salt, stone: a `depositMaterial*` decal with `DecalSize.X` of at least `tribute.rich.decal_size` (5000).
- Berries, fish, eel, mushrooms: `resourceClumps` with a capacity sum of at least `tribute.rich.clump_capacity` (berries 130, fish and eel 385, mushrooms 122).

#### Scenario: A region with a rich deposit and a rich clump node
- **WHEN** a region holds a stone deposit with a decal width of 5000 or more and a mushroom node with a clump capacity of 122 or more
- **THEN** the detected rich resources of the region are stone and mushrooms
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: A poor node is ignored
- **WHEN** a deposit decal is smaller than 5000, or the clump capacity is below the limit
- **THEN** that good is not detected for the region
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: Real regions on the test map
- **WHEN** the vassals Krumme Leite and Hochweg of the test map pay one month
- **THEN** Krumme Leite pays stone and salt, and Hochweg pays mushrooms and flax
- Checked by `mod/InvasionMod/scenarios/tribute/tribute_rich.py`.

### Requirement: Game and rich soil are not detected
The mod SHALL NOT count game (hunting area) as a rich resource. Rich game is not readable from Lua (spike `spike-rich-game-detection`, owner decision 2026-11-01). The mod SHALL NOT detect rich soil. The goods ids SHALL be: iron 14, clay 146, salt 145, stone 27 (rough stone), berries 171, mushrooms 279, carp 30, eel 32, flax 11.

#### Scenario: Game never counts
- **WHEN** a region holds a hunting area
- **THEN** game is not a detected rich resource and is not paid
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: A region always pays two goods
A vassal region SHALL pay exactly 2 goods (`tribute.rich.per_region`). Flax (good 11, the stand-in for rich soil) SHALL be added only when fewer than 2 rich resources are detected: 1 detected resource pays that good and flax, and 0 detected resources pay flax twice (2 x base x policy factor of flax). The flax amount SHALL follow the same base and policy factor. If a method to detect rich soil is found, a region with rich soil SHALL count it and pay flax for it.

#### Scenario: One detected rich resource
- **WHEN** a region has exactly 1 detected rich resource, for example mushrooms
- **THEN** the vassal pays that good and flax, each 100 units for a `fair` vassal
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: No detected rich resource
- **WHEN** a region has 0 detected rich resources
- **THEN** the vassal pays flax twice, 200 units of flax in total for a `fair` vassal
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: More than two rich resources are cut by priority
When a region has more than 2 detected rich resources, the mod SHALL keep 2 by priority and drop the rest. The priority SHALL be (`tribute.rich.priority`): tier 1 the ores iron, stone, salt; tier 2 clay and fish and eel (carp, eel); tier 3 the others (berries, mushrooms). Inside a tier the order of the list in `config.lua` SHALL decide. The mod SHALL log the dropped goods. Flax SHALL NOT be added when 2 goods are kept.

#### Scenario: Four detected resources
- **WHEN** a region has rich clay, salt, iron and berries
- **THEN** the vassal pays iron and salt, and clay and berries are dropped
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: Order inside a tier and between tiers
- **WHEN** a region has rich iron, stone and salt, or rich berries, mushrooms and eel
- **THEN** it pays iron and stone, or eel and berries
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: The rich resources of a region are read once
The mod SHALL read the rich resources of the regions once, at the first tribute tick that needs them, and SHALL keep the result in memory for the session. The mod SHALL NOT save the cache in mod state. After a load (a new game engine object) the mod SHALL read the nodes again. A scan that finds no node SHALL NOT be cached.

#### Scenario: Two ticks read the nodes once
- **WHEN** a vassal pays in two months
- **THEN** the nodes are scanned once
- Checked by `harness/tests/test_fakegame_tribute.py`.

#### Scenario: The same result after a load
- **WHEN** the game engine object is replaced by a load, and the vassal pays again
- **THEN** the nodes are scanned again and the paid goods are the same as before the load
- Checked by `harness/tests/test_fakegame_tribute.py`. The real game gives the same goods in separate runs (each run loads the game): `mod/InvasionMod/scenarios/tribute/tribute_rich.py`.

## REMOVED Requirements

### Requirement: Vassals also pay finite goods
**Reason**: Iron and salt are paid only when they are rich in the region (requirement "Only rich resources are paid"). There is no fixed iron and salt for each family any more.
**Migration**: Remove `tribute.finite_goods` and `finite_paid` in `tribute_state`. Change the test scenario `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py` to check the new rule.
