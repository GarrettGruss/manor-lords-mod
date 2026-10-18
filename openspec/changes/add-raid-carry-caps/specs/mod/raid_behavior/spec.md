## MODIFIED Requirements
<!-- Issue: #275 -->

### Requirement: Loot is capped per raider
The mod SHALL cut the loot (`ItemsLooted`) of a raider to the carry cap of its raid type and write the cut value back to the game. The default cap of a Hussite plunder raid SHALL be 10 (`carry_cap`). The default cap of a bandit plunder raid SHALL be 5. A raid with no known type SHALL use `carry_cap`.

#### Scenario: A raider carries 25
- **WHEN** a raider carries more than the cap
- **THEN** the loot is cut to the cap and the cut is counted in `capped`
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A bandit raider carries 8
- **WHEN** a raider of a bandit plunder raid carries 8
- **THEN** the loot is cut to a value between 1 and 5
- **AND** the cut is counted in `capped`
- Not checked yet (planned: `harness/tests/test_fakegame_raid_behavior.py`).

#### Scenario: A real raid under the cap by type
- **WHEN** a Hussite plunder raid and a bandit plunder raid each run until they leave
- **THEN** no living raider carries more than its cap at any sample
- **AND** the tracker state shows the cap that was used for each raid
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/carry_caps.py`).
