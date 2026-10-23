# mod/vassals Specification

## Purpose
The player rules vassal regions that a friendly AI lord runs in the player name. The player controls them only through policies and orders. A Hussite sack can wipe a vassal (80 percent ruins, all villagers deleted). The player can pay silver to restore a wiped village.

## Requirements

### Requirement: The game goal stays Endless
The mod SHALL set the game goal to Endless (`vassals.goal`, value 2) at every start and every load. When the game changes the goal, the mod SHALL write it back at the next poll (`poll_ms`, default 2000 ms). A claim of a region SHALL NOT end the game.

#### Scenario: The goal is written at boot
- **WHEN** the game boots with the mod, on a fixture or on a new game
- **THEN** the goal is 2 within 15 s of real time
- **AND** a claim of a free region leaves the victory status at 0 and the player owns the region
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`.

#### Scenario: The goal is written back
- **WHEN** a test sets the goal to 3 with `InvasionMod.vassals_set_goal`
- **THEN** the mod writes 2 back at the next poll
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: A settled region is handed to an AI lord
The mod SHALL scan the regions on every `scan_every` poll (default 3). A region that the player owns, is not the home region and is settled SHALL join the registry and SHALL be handed to a new friendly AI lord from `lord_names`. The home region SHALL be the owned region with the most buildings at the first scan. The handover SHALL run once for each slot and SHALL stop after `handover_attempts` failures (default 3).

#### Scenario: The player settles a region
- **WHEN** the player settles a claimed region
- **THEN** the region owner is the vassal lord within 40 s of real time and the slot has the lord name
- **AND** the home region keeps its owner and loses at most 10 percent of its families
- **AND** the game runs 20 game days without a crash
- Checked by `mod/InvasionMod/scenarios/vassals/settled_vassal.py`.

#### Scenario: Two regions get two lords
- **WHEN** two settled regions are scanned in the fake game
- **THEN** each gets its own lord and slot
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The mod keeps peace and flags a stalled lord
The mod SHALL declare peace again when a vassal lord is at war with the player and `keep_peace` is true (default). The mod SHALL flag a vassal as `stalled` when the lord adds fewer than `growth_min_buildings` buildings (default 3) in `growth_check_days` game days (default 10).

#### Scenario: A lord declares war
- **WHEN** a vassal lord declares war on the player after the handover
- **THEN** the mod declares peace and the player stays at peace for 20 game days
- Checked by `mod/InvasionMod/scenarios/vassals/settled_vassal.py`.

#### Scenario: A lord that does not build
- **WHEN** 10 game days pass after the handover and the lord added fewer than 3 buildings
- **THEN** the vassal is flagged `stalled`
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: A lost vassal frees its slot
The mod SHALL free the slot of a lost vassal (region, lord and flags cleared, `vassals_lost` +1) and SHALL tell listeners the slot, region, families and reason. The mod SHALL detect a loss when the owner of a handed-over region is not the pawn of its lord (reason `taken`), and when a sack wipes the vassal (reason `wiped`). The command `InvasionMod.vassals_lose` SHALL run the loss path without a capture. The land SHALL stay a village of rubble. The mod SHALL NOT give the land to another lord.

#### Scenario: A vassal is lost
- **WHEN** the command `vassals_lose` runs on a handed-over vassal
- **THEN** the slot is free, the land stays as it is, and a refugee wave starts
- **AND** the game runs 4 game days without a crash
- Checked by `mod/InvasionMod/scenarios/vassals/loss_and_submission.py`.

#### Scenario: Taken region detection
- **WHEN** another pawn owns a handed-over region in the fake game
- **THEN** the mod detects the loss with the reason `taken`
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.vassals_state`, `vassals_claim`, `vassals_set_keep_peace`, `vassals_set_policy`, `vassals_lose`, `vassals_sack`, `vassals_restore`, `vassals_region_census` and `vassals_set_goal`. The command `vassals_set_loss_region` SHALL NOT exist. Scenarios SHALL use these commands and not eval.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.vassals_state`
- **THEN** the answer holds the goal, the slots with region, lord, policy and the flag `rebuilding`, the wiped regions, the running sacks and the counters
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py` and `harness/tests/test_fakegame_vassals.py`.

### Requirement: Vassals live in a registry
The mod SHALL keep up to `max_vassals` slots (default 3). A slot SHALL hold region, lord name, policy and start day in ModState. A fourth vassal SHALL be refused. The registry SHALL survive a save and load. The mod SHALL ignore a `loyalty` field in an old registry. A vassal SHALL survive or be lost; it has no loyalty value.

#### Scenario: A claim registers slot 1
- **WHEN** the command `InvasionMod.vassals_claim` claims a free region
- **THEN** slot 1 holds the region name and the policy `fair`, and the count is 1
- **AND** the game runs 10 more game days without a crash
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`, updated).

#### Scenario: Registry rules without the game
- **WHEN** the same region is claimed twice, a region with an owner is claimed, or a fourth vassal is claimed
- **THEN** each claim is refused
- **AND** the registry is stored in the pawn tags
- Checked by `harness/tests/test_fakegame_vassals.py`.

#### Scenario: An old registry
- **WHEN** the mod loads a registry that holds `loyalty` and `submitted` fields
- **THEN** it loads without error and the vassal is a normal vassal
- Checked by `harness/tests/test_fakegame_vassals.py` (`OldSaveTests`).

### Requirement: Policies change the tribute
Each slot SHALL have a policy: `light`, `fair` (default) or `heavy`. The tribute factor SHALL be 0.5, 1.0 or 1.5. An unknown policy SHALL be refused. The policy SHALL be kept in ModState. A policy SHALL change nothing else.

#### Scenario: A season change
- **WHEN** the season changes with each of the three policies
- **THEN** the tribute is 0.5, 1.0 and 1.5 times the `fair` tribute
- **AND** the first poll after a load makes no tick
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals/policies_and_orders.py`, updated).

#### Scenario: Policy rules without the game
- **WHEN** an unknown policy or an empty slot is set
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: A Hussite sack wipes a vassal at 80 percent ruins
The mod SHALL sack the houses of a vassal region when a subjugation raid takes it. The sack is complete when at least `sack_wipe.ruin_share` (default 0.80) of the buildings of the region at the start of the sack are ruins. At that point the mod SHALL delete all villagers of the region in three polls (all families but one; the last family when the family count was stable for one poll; then, when the count was stable again, lose the vassal with the reason `wiped` and start a refugee wave).

#### Scenario: The sack completes
- **WHEN** a sack of a vassal region of 20 buildings reaches 16 ruins
- **THEN** the region has 0 villagers
- **AND** the slot is free with the reason `wiped`
- **AND** a refugee wave starts
- Checked by `mod/InvasionMod/scenarios/vassals/vassal_wipe.py` (real game) and `harness/tests/test_fakegame_vassals.py`.

#### Scenario: The wipe takes three polls
- **WHEN** a sack of a region of 5 families is complete
- **THEN** the first poll removes 4 families, the second removes the last one, and the slot is freed in a later poll
- Checked by `harness/tests/test_fakegame_vassals.py`.

#### Scenario: The sack is not complete
- **WHEN** a sack of the same region reaches 15 ruins
- **THEN** the vassal stays and no villager is deleted
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The mod only sacks houses in an AI village
The mod SHALL control only the sacking of houses in an AI village (owner, 2026-10-20) and the rebuild of its ruins (owner, 2026-10-22). While a sack runs it SHALL NOT change the owner, the lord or other buildings of a vassal region.

#### Scenario: No other change
- **WHEN** a sack of a vassal region completes
- **THEN** the owner and the lord of the region are as before
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The player can restore a wiped vassal
The command `InvasionMod.vassals_restore` SHALL take 100 silver (flat, owner 2026-10-21), give the region back to an AI lord (the handover of a new vassal), raise the villager count of the region to 5, spawn 100 logs, 200 planks and 100 rubble stone in the village, and give the rebuild order to every ruin of the region (owner, 2026-10-22). It SHALL be refused, at no cost, when the region is not wiped, the silver is too low, no vassal slot is free, or the handover or the villager call fails.

#### Scenario: A restore
- **WHEN** the player restores a wiped region with enough silver
- **THEN** the silver falls by 100 and the region has 5 villagers and an AI lord
- **AND** the goods are in the village, every ruin is a construction site, and the tribute waits (flag `rebuilding`) until the village is rebuilt
- Checked by `mod/InvasionMod/scenarios/vassals/vassal_wipe.py` (real game) and `harness/tests/test_fakegame_vassals.py`.

#### Scenario: A refused restore
- **WHEN** the region is not wiped, or the silver is too low
- **THEN** the command is refused and no silver is taken
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: A restored vassal pays tribute after the rebuild
A restored vassal SHALL get a slot again with the flag `rebuilding`. Its tribute SHALL wait while the flag is set. The flag SHALL end when `vassals.restore.rebuilt_share` (default 0.50) of the ruins that the restore ordered are built, counted above the buildings that are built right after the order. A construction site is not built.

#### Scenario: The tribute waits
- **WHEN** a restored vassal is rebuilding at a season change
- **THEN** it pays no tribute
- **AND** after enough buildings stand again it pays at the next season change
- Checked by `harness/tests/test_fakegame_tribute.py` and `harness/tests/test_fakegame_vassals.py`.

### Requirement: A sack removes the wood and a sack that ends without a wipe orders the rebuild
When a sack of a vassal region starts, the mod SHALL remove all logs (good 16) and planks (good 17) from the buildings of the region. When a sack ends and the village is not wiped, the mod SHALL give 50 logs and 100 planks to the region and SHALL give the rebuild order to every ruin of the region at once.

#### Scenario: The sack starts
- **WHEN** a sack of a vassal region starts
- **THEN** the logs and planks of the region are removed
- Checked by `harness/tests/test_fakegame_vassals.py` and `mod/InvasionMod/scenarios/vassals/vassal_sack_end.py` (real game).

#### Scenario: The sack ends without a wipe
- **WHEN** a sack ends with fewer ruins than needed
- **THEN** the region gets 50 logs and 100 planks and every ruin with an old type other than 0 and 75 becomes a construction site
- Checked by `harness/tests/test_fakegame_vassals.py` and `mod/InvasionMod/scenarios/vassals/vassal_sack_end.py` (real game).

### Requirement: A sack ends when its raid ends
A sack that has not started its wipe SHALL end without a wipe when the raid that sacks the region has no living raider left (all dead or gone), or when it gives up. The command `InvasionMod.vassals_end_sack` SHALL end a running sack this way for tests.

#### Scenario: The raid ends
- **WHEN** the raid that sacks a vassal region has no living raider left and the wipe has not started
- **THEN** the sack ends without a wipe, with the wood and the rebuild order
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The rebuild order of a ruin
The rebuild order for a ruin SHALL write the building data back with the old building type (`typeBeforeChange`), `constructed` false and `hp` 0, and then call `SetupBuilding`. It SHALL skip a building whose old type is 0 or 75. It SHALL NOT call `convertBlueprintsToBuildings`. Each order SHALL be logged.

#### Scenario: A ruin without a usable old type
- **WHEN** the rebuild order meets a ruin with the old type 0 or 75
- **THEN** the building is skipped
- Checked by `harness/tests/test_fakegame_vassals.py`.
