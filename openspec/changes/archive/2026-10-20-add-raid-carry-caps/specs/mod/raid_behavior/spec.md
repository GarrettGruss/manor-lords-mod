## MODIFIED Requirements
<!-- Issue: #275 -->

### Requirement: Loot is capped per raider
The mod SHALL manage plundered quantities only for Hussite raids. The Hussite AI has raiding disabled, so the game does not manage the raid natively. The plundered goods of a Hussite raid SHALL NOT exceed `carry_cap` (default 10) for each raider at the start of the raid. The mod SHALL NOT change the loot (`ItemsLooted`) of a native raid; the game manages it.

#### Scenario: A Hussite raid reaches its carry cap
- **WHEN** a Hussite raid of 12 raiders plunders and the cap is 10
- **THEN** its plundered goods stop at 120 or less
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A raider carries 25
- **WHEN** a raider of a native raid carries 25
- **THEN** the mod does not write its loot and `capped` stays 0
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A real Hussite raid under the cap
- **WHEN** a Hussite raid runs until it leaves
- **THEN** its plundered goods are at most `carry_cap` times its raiders at the start
- **AND** the tracker state shows the cap that was used
- Checked by `mod/InvasionMod/scenarios/raid_behavior/carry_caps.py`.

### Requirement: A role raid leaves for loot, losses or time
The mod SHALL make an active role raid (a plunder raid with `roles = true`) leave when the goods it took reach its loot goal per raider at the start, or the share of dead raiders reaches `leave.loss_share` (default 0.5), or `leave.max_days` (default 25) game days passed since the spawn. The loot goal of a Hussite raid SHALL be `carry_cap` (default 10). The loot goal of any other role raid SHALL be `leave.loot_per_raider` (default 4). The leave reason SHALL be `loot`, `losses` or `time`. A lord raid SHALL leave by peace with its lord, and the game removes the army. No raider SHALL stay on the map after the raid has left.

#### Scenario: A forced role raid at difficulty 1
- **WHEN** a role raid runs until it leaves
- **THEN** its state is `left` and the leave reason is `loot`, `losses` or `time`
- **AND** no raider of the raid stays on the map
- **AND** the player still owns a region and the village still has people
- Checked by `mod/InvasionMod/scenarios/raid_behavior/role_leave.py`.

#### Scenario: Leave by losses or by time
- **WHEN** the loss share is reached, or `max_days` is reached with the loot rule off
- **THEN** the leave reason is `losses` or `time` and the rule fires once
- Checked by `mod/InvasionMod/scenarios/raid_behavior/lord_leave_reason.py`.

#### Scenario: A Hussite raid leaves when it is full
- **WHEN** a Hussite raid of 12 raiders has plundered 120 goods and the cap is 10
- **THEN** the leave reason is `loot`
- **AND** it does not leave by loot at 48 goods (4 per raider)
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
