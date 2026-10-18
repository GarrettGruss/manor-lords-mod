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

### Requirement: Vassals live in a registry with loyalty
The mod SHALL keep up to `max_vassals` slots (default 3). A slot SHALL hold region, lord name, loyalty and start day in ModState. A new vassal SHALL start with `loyalty_start` (default 50). Loyalty SHALL stay between 0 and 100. A fourth vassal SHALL be refused. The registry SHALL survive a save and load.

#### Scenario: A claim registers slot 1
- **WHEN** the command `InvasionMod.vassals_claim` claims a free region
- **THEN** slot 1 holds the region name, loyalty 50, and the count is 1
- **AND** setting loyalty to 150 gives 100 and setting it to -5 gives 0
- **AND** the game runs 10 more game days without a crash
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`.

#### Scenario: Registry rules without the game
- **WHEN** the same region is claimed twice, a region with an owner is claimed, or a fourth vassal is claimed
- **THEN** each claim is refused
- **AND** the registry is stored in the pawn tags
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

### Requirement: Policies change tribute and loyalty
Each slot SHALL have a policy: `light`, `fair` (default) or `heavy`. At each season change the loyalty SHALL change by +3 (`light`), 0 (`fair`) or -5 (`heavy`), once for each change. The tribute factor SHALL be 0.5, 1.0 or 1.5. An unknown policy SHALL be refused. The policy SHALL be kept in ModState.

#### Scenario: A season change
- **WHEN** the season changes with each of the three policies
- **THEN** loyalty rises by 3 with `light`, stays with `fair`, and falls by 5 with `heavy`
- **AND** the first poll after a load makes no tick
- Checked by `mod/InvasionMod/scenarios/vassals/policies_and_orders.py`.

#### Scenario: Policy rules without the game
- **WHEN** an unknown policy or an empty slot is set
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The gift order raises loyalty
The command `InvasionMod.vassals_order_gift` SHALL take `gift.cost` silver (default 50) and add `gift.loyalty` (default 10) to the loyalty of the slot, up to 100. It SHALL be refused without enough silver or without a handed-over vassal.

#### Scenario: A gift
- **WHEN** a gift is ordered with enough silver
- **THEN** the silver falls by exactly 50 and the loyalty rises by 10
- Checked by `mod/InvasionMod/scenarios/vassals/policies_and_orders.py`.

#### Scenario: A gift without silver
- **WHEN** a gift is ordered with too little silver
- **THEN** the command is refused and the loyalty is unchanged
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

### Requirement: A vassal with low loyalty submits
At each season change, after the loyalty tick, a vassal at loyalty `submit_at` (default 10) or lower SHALL submit to the invader. Its lord SHALL declare war on the player, the mod SHALL not make peace for it, and it SHALL pay no tribute. A submitted vassal at loyalty `return_at` (default 40) or higher SHALL return and its lord SHALL get peace.

#### Scenario: Submission and return
- **WHEN** a vassal has loyalty 5 at a season change, then loyalty 45 at a later one
- **THEN** it submits and its lord is at war with the player, then it returns and the lord is at peace
- **AND** it pays no tribute while it is submitted
- Checked by `mod/InvasionMod/scenarios/vassals/loss_and_submission.py`.

#### Scenario: A healthy vassal
- **WHEN** a vassal has loyalty above `submit_at` at a season change
- **THEN** it does not submit
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.vassals_state`, `vassals_claim`, `vassals_set_loyalty`, `vassals_set_keep_peace`, `vassals_set_policy`, `vassals_order_gift`, `vassals_loyalty_tick_now`, `vassals_lose`, `vassals_set_loss_region`, `vassals_submission_tick_now` and `vassals_set_goal`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.vassals_state`
- **THEN** the answer holds the goal, the slots with region, lord, loyalty and policy, and the counters
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`.
