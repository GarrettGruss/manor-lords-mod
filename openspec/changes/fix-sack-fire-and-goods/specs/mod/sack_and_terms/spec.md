## MODIFIED Requirements
<!-- Issue: #325 -->

### Requirement: Sack size grows with difficulty
The mod SHALL take a share of standing buildings and families. The share in percent SHALL be `share_min + (share_max - share_min) x (difficulty - 1) / 2` (defaults 20 and 50, so 20, 35 and 50). Every count SHALL round up. A normal sack SHALL keep at least `min_families_left` families (default 1). The sack SHALL NOT take a share of the stock.

#### Scenario: A forced sack at each difficulty
- **WHEN** the command `InvasionMod.sack_now` runs at difficulty 1, 2 and 3
- **THEN** the standing buildings fall by about 20, 35 and 50 percent (plus or minus 1 building)
- **AND** the stock of each good does not fall because of the sack
- **AND** at least 1 family stays and the population stays above 0
- Not checked yet (planned: `mod/InvasionMod/scenarios/sack_and_terms/sack.py`, updated).

#### Scenario: The share rule without the game
- **WHEN** the share is computed for difficulty 1 to 3
- **THEN** it is 20, 35 and 50, and a normal sack keeps one family
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

## ADDED Requirements

### Requirement: A sack destroys no goods
A sack SHALL NOT destroy goods. Goods in a sacked building SHALL stay in the village stock. Only the plunder tick of a raid SHALL remove goods from the village.

#### Scenario: A burned store keeps its goods in the stock
- **WHEN** a sack turns a store that holds goods into rubble
- **THEN** the village stock of each good is the same before and after the sack, within 1 unit
- Not checked yet (planned: `mod/InvasionMod/scenarios/sack_and_terms/sack_ruins.py`, updated).

### Requirement: Sacked buildings become rubble
Each building the sack hits SHALL be rubble by the end of the sack, within a time limit from the feature config. The sack SHALL run while the raiders of the raid are still in the village, so the villagers flee and do not fight a fire.

#### Scenario: Fires during a raid make rubble
- **WHEN** a sack runs while the raiders are in the village
- **THEN** every building the sack hit is rubble within the time limit
- Not checked yet (planned: `mod/InvasionMod/scenarios/sack_and_terms/sack_ruins.py`, updated).
