## MODIFIED Requirements
<!-- Issue: #341 -->

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

## ADDED Requirements

### Requirement: A Hussite sack wipes a vassal at 80 percent ruins
The mod SHALL sack the houses of a vassal region when a subjugation raid takes it. The sack is complete when at least `sack_wipe.ruin_share` (default 0.80) of the buildings of the region at the start of the sack are ruins. At that point the mod SHALL delete all villagers of the region, SHALL lose the vassal with the reason `wiped`, and SHALL start a refugee wave.

#### Scenario: The sack completes
- **WHEN** a sack of a vassal region of 20 buildings reaches 16 ruins
- **THEN** the region has 0 villagers
- **AND** the slot is free with the reason `wiped`
- **AND** a refugee wave starts
- Checked by `mod/InvasionMod/scenarios/vassals/vassal_wipe.py` (real game) and `harness/tests/test_fakegame_vassals.py`.

#### Scenario: The sack is not complete
- **WHEN** a sack of the same region reaches 15 ruins
- **THEN** the vassal stays and no villager is deleted
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The mod only sacks houses in an AI village
The mod SHALL control only the sacking of houses in an AI village (owner, 2026-10-20). It SHALL NOT change the owner, the lord or other buildings of a vassal region.

#### Scenario: No other change
- **WHEN** a sack of a vassal region completes
- **THEN** the owner and the lord of the region are as before
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: The player can restore a wiped vassal
The command `InvasionMod.vassals_restore` SHALL take 100 silver (flat, owner 2026-10-21), raise the villager count of a wiped region to 5, and spawn 100 logs, 200 planks and 100 rubble stone in the village. It SHALL be refused, at no cost, when the region is not wiped, the silver is too low, no vassal slot is free, or the villager call fails. The AI does the rebuild.

#### Scenario: A restore
- **WHEN** the player restores a wiped region with enough silver
- **THEN** the silver falls by 100 and the region has 5 villagers
- **AND** the goods are in the village and the tribute waits (flag `rebuilding`) until the village is rebuilt
- Checked by `mod/InvasionMod/scenarios/vassals/vassal_wipe.py` (real game) and `harness/tests/test_fakegame_vassals.py`.

#### Scenario: A refused restore
- **WHEN** the region is not wiped, or the silver is too low
- **THEN** the command is refused and no silver is taken
- Checked by `harness/tests/test_fakegame_vassals.py`.

### Requirement: A restored vassal pays tribute after the rebuild
A restored vassal SHALL get a slot again with the flag `rebuilding`. Its tribute SHALL wait while the flag is set. The flag SHALL end when `vassals.restore.rebuilt_share` (default 0.50) of the buildings before the wipe stand again and at least `min_new_buildings` (default 3) buildings stand above the count right after the restore.

#### Scenario: The tribute waits
- **WHEN** a restored vassal is rebuilding at a season change
- **THEN** it pays no tribute
- **AND** after enough buildings stand again it pays at the next season change
- Checked by `harness/tests/test_fakegame_tribute.py` and `harness/tests/test_fakegame_vassals.py`.
