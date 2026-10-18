# Spec Delta

## Purpose

Named harness commands to start raids, kill units and give them loot, take a share of the player village away, track loot on the ground, and steer the AI lords and the ownership of regions. Tests of raid and invasion features use them to cause and measure events.

## ADDED Requirements

### Requirement: Raid state is read only
The harness SHALL answer `raid_state` with the raid timer, the game setup values for raids, the default and elite raid id lists and the sizes of the player message lists. `raid_state` SHALL NOT change the game.

#### Scenario: Read the raid state
- **WHEN** a client sends `raid_state`
- **THEN** the reply is ok and has `timer`, `setup`, `raid_ids` and `lists`
- Not checked yet.

### Requirement: Raids and camps are spawned with the game calls
The harness SHALL start raiders on `spawn_raiders` with `squads` from 1 to 20 at the point `x`, `y`, `z`, or at the player pawn when no point is given. It SHALL start an elite raid on `spawn_elite_raiders` and a bandit camp on `spawn_bandit_camp`. Each reply SHALL give the unit counts before and after. The harness SHALL refuse a `squads` value outside 1 to 20 and a request with no point and no player pawn.

#### Scenario: Raiders at a point
- **WHEN** a client sends `spawn_raiders` with `squads` 2, `x` 5 and `y` 6
- **THEN** the game call receives 2 squads and the point (5, 6)
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

#### Scenario: Too many squads
- **WHEN** a client sends `spawn_raiders` with `squads` 99
- **THEN** the reply is not ok and no raid starts
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

#### Scenario: A raid in the game
- **WHEN** a client sends `spawn_raiders` with `squads` 1, `spawn_elite_raiders` or `spawn_bandit_camp` in a running game
- **THEN** the bandit unit count rises by a whole number of squads
- Not checked yet.

### Requirement: Units can be killed and given loot
The harness SHALL kill up to `count` living units of one side on `kill_units`, with `side` `player`, `ai`, `bandit` or `civil` (default `bandit`) and `count` from 1 to 400. With `with_loot` 1 it SHALL take only units that carry loot. With `actors` 1 it SHALL report the actor classes whose count changed. It SHALL write the loot amount on units of a side on `set_unit_loot` and read it back. The harness SHALL refuse a side or count outside these ranges.

#### Scenario: Kill units
- **WHEN** a client sends `kill_units` with `side` bandit and `count` 2
- **THEN** 2 bandit units are dead and the reply gives the counts before and after
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

#### Scenario: Set loot
- **WHEN** a client sends `set_unit_loot` with `count` 2 and `amount` 7, and then `units_census`
- **THEN** the loot total is 14 and the reply of `set_unit_loot` counts 2 changed units
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

#### Scenario: Bad side or count
- **WHEN** a client sends `kill_units` with an unknown side or with `count` 9999
- **THEN** the reply is not ok and no unit is killed
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

### Requirement: Loot on the ground is a ledger
The harness SHALL kill up to `count` looters of a side on `drop_loot` with a `good`, and record one pile with place, amount and good for each looter killed. `loot_piles` SHALL list the piles. `recover_loot` SHALL add the goods of the pile `pile` to the stock and remove the pile, so a pile is recovered once. The harness SHALL keep at most 50 piles and SHALL refuse a good outside 1 to 1000, a count outside 1 to 50, an unknown pile and a missing cheat manager.

#### Scenario: A pile for each looter
- **WHEN** a client sends `drop_loot` with `count` 2 and `good` 15
- **THEN** a pile is recorded at the place of each dead looter that carried loot
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: Recover once
- **WHEN** a client sends `recover_loot` for a pile twice
- **THEN** the first reply adds the goods to the stock and the second reply is not ok
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: Bad loot input
- **WHEN** a client sends `drop_loot` or `recover_loot` with a bad good, count or pile
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: Loot is dropped and recovered in the game
- **WHEN** looters die and a pile is recovered
- **THEN** the stock of the good rises by the pile amount
- Checked by `harness/scenarios/loot_drop_recovery.py`.

### Requirement: The village state can be censused for a sack
The harness SHALL answer `sack_census` with the buildings by state (standing, rubble and others), the stock by good, the stores that hold goods and the families and people of the player village. The village SHALL be found by its owner, not by position. `sack_census` SHALL NOT change the game. The harness SHALL answer with an error when no player region exists or a named region is not owned by the player.

#### Scenario: Census counts
- **WHEN** a client sends `sack_census`
- **THEN** the reply counts buildings, stock, stores and people
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: A region the player does not own
- **WHEN** a client sends `sack_census` with a region that the player does not own, or no player region exists
- **THEN** the reply is not ok with a message
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

### Requirement: A share of the village can be burned, taken and killed
The harness SHALL burn or collapse standing buildings on `sack_buildings`, remove goods on `sack_goods`, and kill whole families on `sack_people`, each by count or by percent. `sack_village` SHALL do all three. Every reply SHALL give the census before and after. One call SHALL NOT remove more than 5000 units of goods.

#### Scenario: Collapse and fire
- **WHEN** a client sends `sack_buildings` with `method` collapse, or with `method` fire
- **THEN** a collapse makes rubble at once and the goods stay in the stock
- **AND** a fire sets the fire flag, and the buildings are rubble after the burn
- **AND** only standing buildings are hit
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: Goods
- **WHEN** a client sends `sack_goods` with a `good` and `amount`, or with `percent`, or with `store`
- **THEN** the stock falls by at most the amount that exists, and by the share for each good
- **AND** one call is capped, and a game that refuses to consume does not loop
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: People
- **WHEN** a client sends `sack_people` with `count` or `percent`
- **THEN** whole families are killed and dead members are not killed twice
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: All three shares
- **WHEN** a client sends `sack_village` with `buildings_pct` 50, `stock_pct` 50 and `people_pct` 40
- **THEN** half of the standing buildings are rubble and the families fall by the people share
- **AND** 0 percent changes nothing and 100 percent takes everything
- **AND** the goods are removed first, so a fire does not hide the removal
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: Bad sack input
- **WHEN** a client sends `sack_village` with a percent above 100, `sack_buildings` with `method` bomb, or `sack_goods` with a `good` and no `amount`
- **THEN** the reply is not ok and the error names the problem
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

#### Scenario: A sack in the game
- **WHEN** `sack-village` runs in the real game
- **THEN** the rubble count equals the asked share of the standing buildings
- **AND** the stock lost and the families lost are within the scenario tolerance of the asked percent
- Checked by `harness/scenarios/sack_village.py`.

#### Scenario: Rounding
- **WHEN** a client sends `sack_buildings` with a `percent` that gives a half unit
- **THEN** the share rounds half up
- Checked by `harness/tests/test_fakegame_harnesssack.py`.

### Requirement: AI lords can be read and steered
The harness SHALL name a lord by its number from 1 and the player as target 0. It SHALL read the lords, challenges and AI logs on `lords_state`, and steer a lord with `lord_declare_war`, `lord_declare_peace`, `lord_set_influence`, `lord_challenge`, `lord_claim`, `lord_spawn_army`, `spawn_ai_lord` and `lord_start_ai`. It SHALL refuse an unknown lord or target.

#### Scenario: State of the lords
- **WHEN** a client sends `lords_state` with `log` 5
- **THEN** the lords are listed with traits and their relation to the player, and the logs hold the AI lines
- **AND** `log` 0 leaves the logs out
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: War, influence and challenge
- **WHEN** a client sends `lord_declare_war`, `lord_set_influence` with `value` 2000 and `lord_challenge` for lord 1 and target 0
- **THEN** the relation has the `at_war` tag and the enemy list has 1 entry
- **AND** the influence reads 2000, and the challenge lists the target region
- **AND** an influence of 99999 is refused
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: Army and new lord
- **WHEN** a client sends `lord_spawn_army` with `count` 2, then `spawn_ai_lord` with a name and `lord_start_ai`
- **THEN** the army squads belong to the lord and show position and target, and the lord count rises by 1 and its AI is started
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: Bad lord input
- **WHEN** a client sends a lord command with an unknown lord or target, an unknown template, a count of 9 or no name
- **THEN** the reply is not ok and no game call is made
- **AND** the limits are `count` 1 to 6, offsets within 60000, influence 0 to 10000, a name of 1 to 40 characters and an AI speed above 0 up to 100
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: Peace and claim replies
- **WHEN** a client sends `lord_declare_peace` or `lord_claim`
- **THEN** the peace reply gives the relation tags before and after, and the claim reply gives the claims before and after
- Not checked yet.

### Requirement: Region ownership can be changed and regions settled
The harness SHALL read regions on `regions_state` and change ownership with `lord_relations`, `lord_take_region`, `region_clear_owner`, `claim_region`, `lord_receive_region` and `lord_found_village`. It SHALL settle a region on `settle_region` only when the settling pawn owns it. A command of several steps SHALL stop at the first step that fails and name it.

#### Scenario: Regions state
- **WHEN** a client sends `regions_state`
- **THEN** each region lists its owner and settled flag
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: A lord takes or receives a region
- **WHEN** a client sends `lord_relations` and `lord_take_region` for a new lord, or `lord_receive_region` for a region of the player
- **THEN** the lord gets relation rows and the region owner
- **AND** `lord_receive_region` reports the steps `clear owner` and `claim`, and the region has a new owner claim
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: A lord founds a village
- **WHEN** a client sends `lord_found_village` for a free region
- **THEN** the steps `claim` and `settle` are done and the region is settled with the given type and supply
- **AND** a second founding in that region is refused because it has an owner
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: Settle needs an owner
- **WHEN** a client sends `settle_region` for a region that the pawn does not own
- **THEN** the reply is not ok with `does not own` and no settle call is made
- **AND** a `type` above 5 is refused, and a region that is already settled is allowed
- Checked by `harness/tests/test_fakegame_harnesslords.py`.

#### Scenario: Unknown region
- **WHEN** a client sends `lord_take_region` with a region name that does not exist
- **THEN** the reply is not ok with `no region named`
- Checked by `harness/tests/test_fakegame_harnesslords.py`.
