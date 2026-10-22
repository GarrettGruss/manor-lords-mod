# mod/vassals Specification

## Purpose
The player rules vassal regions that a friendly AI lord runs in the player name. The player controls them only through policies and orders. A vassal can be lost or can submit to the invader.

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
The mod SHALL free the slot of a lost vassal (region, lord and flags cleared, `vassals_lost` +1) and SHALL tell listeners the slot, region, families and reason. The mod SHALL detect a loss when the owner of a handed-over region is not the pawn of its lord (reason `taken`). The command `InvasionMod.vassals_lose` SHALL run the loss path without a capture. With `loss_region` set to `forget` (default) the lord SHALL keep the land.

#### Scenario: A vassal is lost
- **WHEN** the command `vassals_lose` runs on a handed-over vassal
- **THEN** the slot is free, the land stays with its lord, and a refugee wave starts
- **AND** the game runs 4 game days without a crash
- Checked by `mod/InvasionMod/scenarios/vassals/loss_and_submission.py`.

#### Scenario: Taken region detection
- **WHEN** another pawn owns a handed-over region in the fake game
- **THEN** the mod detects the loss with the reason `taken`
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.vassals_state`, `vassals_claim`, `vassals_set_keep_peace`, `vassals_set_policy`, `vassals_lose`, `vassals_set_loss_region` and `vassals_set_goal`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.vassals_state`
- **THEN** the answer holds the goal, the slots with region, lord and policy, and the counters
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`.

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
