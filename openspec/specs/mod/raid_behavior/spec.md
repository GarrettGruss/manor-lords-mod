# mod/raid_behavior Specification

## Purpose
The raid_behavior feature steers the larger Hussite raids into the player's region, because the game has no native way to raid a player region with units other than Brigands. A Hussite raid runs under the baron AI, not the native plunder AI, so that a raid can bring a mix of units (archers, spearmen, retinue) that a native raid cannot. It also tracks each raid that the invasion feature spawns, keeps the loot of Hussite raids under a cap, lets role raids leave, and guards the player's region.

## Requirements

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

### Requirement: The raid state is kept and shown by command
The mod SHALL keep `raid_count`, `raid_start_day`, `raid_state`, `raid_returned`, `raid_lost` and `raid_burned` in ModState, writing a key only when its value changes. `InvasionMod.raid_behavior_state` SHALL return the summary of each raid: living, deaths, loot, looted total, returned, burned, state, leave reason and kind (`plunder`, `subjugation` or `great`).

#### Scenario: The numbers in the Tags
- **WHEN** a raid has run and the tracker saved its summary
- **THEN** the raid state keys are entries in the pawn Tags
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: The mod never steers or removes a native raid
<!-- Issue: #373 -->
The mod SHALL NOT steer or rout a raid that runs under the native plunder AI, and SHALL NOT remove its units.

#### Scenario: No removal of native raiders
- **WHEN** a native raid runs
- **THEN** the mod removes no raider
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Every spawned raid is tracked by the game census
<!-- Issue: #373 -->
The mod SHALL start a raid record when the invasion feature spawns a raid. The record SHALL hold the units that are new since the spawn. The count of living raiders SHALL equal the unit count read from the game census; a unit that the census no longer counts SHALL NOT count as living. A raid SHALL end as `left` when raiders walked off the map or the native leave line was seen, or as `destroyed` when all raiders died.

#### Scenario: A Hussite raid
- **WHEN** a Hussite raid runs under the baron AI
- **THEN** the tracker count of living raiders equals the game census count at every sample
- **AND** the raid ends as `left` or `destroyed`, with no limit on game days
- Checked by `mod/InvasionMod/scenarios/raid_behavior/carry_caps.py`.

#### Scenario: A raider that left the census
- **WHEN** a raider is still in the `SMUnit` list but the census no longer counts it
- **THEN** the tracker does not count it as living
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: Units that existed before the spawn
- **WHEN** a raid spawns and other bandit units already exist
- **THEN** only the new units are raiders
- Checked by `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: Stores have a tier
The mod SHALL give each store type a tier from the feature config. Tier 1 SHALL be the storehouse and the granary. Tier 2 SHALL be the manor storage. The mod SHALL steal only from tier 1 stores. The mod SHALL NOT steal from tier 2. In a game raid the game may rob any store, also the manor store; the mod SHALL NOT protect or restore it.

#### Scenario: A baron AI raid never robs the manor store
- **WHEN** a baron AI raid runs while the manor store and a tier 1 store both hold goods
- **THEN** the goods in the manor store are unchanged at the end of the raid
- Checked by `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`.

### Requirement: The game manages the loss in a game raid
In a game raid, where the game steers the raiders to pillage and steal, the mod SHALL NOT compute or remove stolen goods. The game SHALL manage the stolen goods.

#### Scenario: A game raid has no mod steal
- **WHEN** a game raid runs
- **THEN** the mod removes no goods from any store
- Checked by `mod/InvasionMod/scenarios/raid_behavior/storage_tiers.py`.

### Requirement: Stealing units in a baron AI raid take goods from tier 1 stores
In a baron AI raid, where baron units cannot pillage or steal, the mod SHALL measure the distance of each baron unit to the battle marker. A unit farther than the steal distance threshold (feature config, 200 m for now; the army fights about 140 m from the marker) SHALL be a stealing unit. Each stealing unit SHALL take the steal rate (feature config, 10 goods per in-game day for now) from tier 1 stores only.

#### Scenario: A far unit steals
- **WHEN** a baron unit is farther than the threshold from the battle marker for one in-game day
- **THEN** tier 1 stores lose about the steal rate in total
- **AND** the manor store loses nothing
- Checked by `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py` and `harness/tests/test_fakegame_raid_behavior.py`.

#### Scenario: A near unit does not steal
- **WHEN** a baron unit stays within the threshold of the battle marker
- **THEN** no store loses goods because of that unit
- Checked by `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py` and `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: A baron AI raid has a steal goal
Each baron AI raid SHALL have a total steal goal from the feature config, scaled by game difficulty (for now 100 for a small raid and 300 for a large raid). The mod SHALL stop stealing when the goods taken by the raid reach the goal.

#### Scenario: Stealing stops at the goal
- **WHEN** stealing units of a small raid have taken the goal
- **THEN** no more goods are taken
- **AND** the total taken is not above the goal
- Checked by `mod/InvasionMod/scenarios/raid_behavior/baron_steal.py` and `harness/tests/test_fakegame_raid_behavior.py`.

### Requirement: STRETCH: a Manor tech unlocks storage under the manor
As a stretch goal, the mod SHOULD add a tech "Manor" in a third, common branch of the tech tree. The tech SHALL unlock storage under the manor with the capacity and the job slots of a level 1 storehouse. The mod SHALL add one tech for now.

#### Scenario: Researching the Manor tech
- **WHEN** the player researches the Manor tech
- **THEN** the manor can hold goods up to the capacity of a level 1 storehouse
- **AND** the manor has the job slots of a level 1 storehouse
- Not checked yet (planned: `mod/InvasionMod/scenarios/raid_behavior/manor_storage_tech.py`).
