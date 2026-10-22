# mod/raid_behavior Specification

## Purpose
The raid_behavior feature steers the larger Hussite raids into the player's region, because the game has no native way to raid a player region with units other than Brigands. A Hussite raid runs under the baron AI, not the native plunder AI, so that a raid can bring a mix of units (archers, spearmen, retinue) that a native raid cannot. It also tracks each raid that the invasion feature spawns, keeps the loot of Hussite raids under a cap, lets role raids leave, and guards the player's region.

## Requirements

### Requirement: Every spawned raid is tracked
The mod SHALL start a raid record when the invasion feature spawns a raid. The record SHALL hold the units that are new since the spawn. The count of living raiders SHALL equal the unit count read from the game. A raid SHALL end as `left` when raiders walked off the map or the native leave line was seen, or as `destroyed` when all raiders died.

#### Scenario: A one-squad native raid
- **WHEN** a raid of 1 squad (18 raiders) runs under the native plunder AI
- **THEN** the tracker count of living raiders equals the game unit count at every sample
- **AND** the raid ends within 20 game days (30 for larger raids) with the native leave line in the log
- Checked by `mod/InvasionMod/scenarios/raid_behavior/native_plunder.py`.

#### Scenario: Units that existed before the spawn
- **WHEN** a raid spawns and other bandit units already exist
- **THEN** only the new units are raiders
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A native raid is left alone
The mod SHALL NOT steer or rout a raid that runs under the native plunder AI, and SHALL NOT remove its units. The raid SHALL loot goods, burn buildings and leave under the game's own rules.

#### Scenario: Native plunder
- **WHEN** a native raid ends
- **THEN** the looted goods are more than 0 and the burned buildings are between 0 and 10
- **AND** the village population is more than 0
- Checked by `mod/InvasionMod/scenarios/raid_behavior/native_plunder.py`.

#### Scenario: No removal of native raiders
- **WHEN** a native raid runs
- **THEN** the mod removes no raider
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

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

### Requirement: The loot of a dead raider goes to the nearest store
When a raider dies in the village, the mod SHALL add its loot to the store that is nearest to the place of death, in the good that the store holds most of (`fallback_good` if the store is empty). If there is no store, the loot SHALL be counted as lost. A raider that walks off the map at or below `exit_y` (default -85000) SHALL keep its loot and count as a departure.

#### Scenario: Eighteen raiders die with loot
- **WHEN** 18 raiders that carry loot are killed
- **THEN** the tracker counts 18 deaths and the returned goods equal the carried loot
- **AND** the village stock rises by the same amount and nothing is lost
- Checked by `mod/InvasionMod/scenarios/raid_behavior/loot_return.py`.

#### Scenario: A death near a far store
- **WHEN** a raider dies nearer to a far store than to a near store
- **THEN** the loot goes to the far store
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A role raid leaves for loot, losses or time
An active role raid (`roles = true`) SHALL leave when its goods taken reach its loot goal per starting raider (`carry_cap`, default 10, for a Hussite raid; `leave.loot_per_raider`, default 4, otherwise), when dead raiders reach `leave.loss_share` (default 0.5), or after `leave.max_days` (default 25) game days. The reason SHALL be `loot`, `losses` or `time`. A lord raid SHALL leave by peace with its lord. No raider SHALL stay on the map after the raid left.

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

### Requirement: A lord raid plunders the stores while it stands at the manor
Once each game day, the mod SHALL take `plunder.per_unit_day` (default 1) goods from the village stores for each raider of a lord raid that stands within `plunder.battle_radius` (default 4000 units) of the manor. The tick SHALL stop at the loot goal of the leave rule. A native raid SHALL have no plunder tick.

#### Scenario: The plunder of a lord raid
- **WHEN** a lord raid runs until it leaves by loot
- **THEN** the plundered goods are more than 0
- Checked by `mod/InvasionMod/scenarios/raid_behavior/role_leave.py`.

#### Scenario: Radius, once a day, and the goal
- **WHEN** raiders stand inside and outside the radius
- **THEN** only the raiders inside count, once each day, and the tick stops at the goal
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Subjugation and great raids never plunder or leave
The mod SHALL NOT run the plunder tick or a leave rule for a subjugation raid or a great raid army. These raids SHALL stay until they are beaten.

#### Scenario: A subjugation raid for 12 game days
- **WHEN** a subjugation raid runs for 12 game days
- **THEN** its plundered goods are 0, it has no leave reason, and it is not leaving
- Checked by `mod/InvasionMod/scenarios/invasion/subjugation_raid.py`.

### Requirement: The mod gives back a region that the raid lord wins
The mod SHALL give a home region back to the player when the raid lord becomes its owner, within one slow look (under 5 s), and SHALL log `region <name> was taken by the lord, given back=true`.

#### Scenario: The lord takes the region
- **WHEN** a test makes the raid lord the owner of the home region
- **THEN** the log has the given back line and the player owns the region again
- **AND** the village still has people
- Checked by `mod/InvasionMod/scenarios/raid_behavior/region_guard.py`.

### Requirement: Bandit squads leave only in a quiet spot
When a bandit-squad raid (no lord) must leave, the mod SHALL declare peace and SHALL remove a raider only at least `leave.quiet_distance` (default 40000 units) from the player pawn or at the map edge, never in view. The loot SHALL leave with the unit. The mod SHALL restore the war when the raid has ended.

#### Scenario: A leaving raid with raiders near the village
- **WHEN** a raid is leaving and raiders stand near the village
- **THEN** only raiders in a quiet spot are removed
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: The raid state is kept and shown by command
The mod SHALL keep `raid_count`, `raid_start_day`, `raid_state`, `raid_returned`, `raid_lost` and `raid_burned` in ModState, writing a key only when its value changes. `InvasionMod.raid_behavior_state` SHALL return the summary of each raid: living, deaths, loot, looted total, returned, burned, state, leave reason and kind (`plunder`, `subjugation` or `great`).

#### Scenario: The numbers in the Tags
- **WHEN** a raid has run and the tracker saved its summary
- **THEN** the raid state keys are entries in the pawn Tags
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.
