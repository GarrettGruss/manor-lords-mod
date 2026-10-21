## MODIFIED Requirements
<!-- Issue: #325 -->

### Requirement: Sack size grows with difficulty
The mod SHALL take a share of standing buildings and families. The share in percent SHALL be `share_min + (share_max - share_min) x (difficulty - 1) / 2` (defaults 20 and 50, so 20, 35 and 50). Every count SHALL round up. A normal sack SHALL keep at least `min_families_left` families (default 1). The sack SHALL NOT take a share of the stock.

#### Scenario: A forced sack at each difficulty
- **WHEN** the command `InvasionMod.sack_now` runs at difficulty 1, 2 and 3
- **THEN** the standing buildings fall by about 20, 35 and 50 percent (plus or minus 1 building)
- **AND** the mod takes no goods from the stores
- **AND** at least 1 family stays and the population stays above 0
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.

#### Scenario: The share rule without the game
- **WHEN** the share is computed for difficulty 1 to 3
- **THEN** it is 20, 35 and 50, a normal sack keeps one family and the plan holds no goods
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

## ADDED Requirements

### Requirement: The mod destroys no goods in a sack
The mod SHALL NOT remove goods from a sacked building. A fire that burns a store MAY destroy part of its goods (owner decision 2026-10-21: accept the loss); the mod SHALL NOT add them back. Only the plunder tick of a raid SHALL remove goods on purpose.

#### Scenario: The mod takes no goods
- **WHEN** a sack runs
- **THEN** the sack result reports 0 goods removed by the mod
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

#### Scenario: A burned store may lose goods in the fire
- **WHEN** a sack with method `fire` turns a store into rubble
- **THEN** the ruin holds the goods that the fire left, and the scenario records the loss without failing
- Checked by `harness/scenarios/sack_ruins.py`.

### Requirement: Sacked buildings become rubble
Each building the sack hits SHALL be rubble when the sack ends or within a time limit. The default method `collapse` makes rubble at once. The method `fire` makes rubble only when villagers do not fight the fire, which is the case when enemy soldiers are in the village.

#### Scenario: A sack makes rubble
- **WHEN** a sack runs
- **THEN** every building the sack hit is rubble and stays in the building list
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.
