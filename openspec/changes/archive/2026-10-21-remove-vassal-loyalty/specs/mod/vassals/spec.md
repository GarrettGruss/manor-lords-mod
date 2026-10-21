## MODIFIED Requirements
<!-- Issue: #344 -->

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.vassals_state`, `vassals_claim`, `vassals_set_keep_peace`, `vassals_set_policy`, `vassals_lose`, `vassals_set_loss_region` and `vassals_set_goal`.

#### Scenario: State is readable
- **WHEN** a scenario sends `InvasionMod.vassals_state`
- **THEN** the answer holds the goal, the slots with region, lord and policy, and the counters
- Checked by `mod/InvasionMod/scenarios/vassals/claim_without_victory.py`.

## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Vassals live in a registry with loyalty
**Reason**: Vassal loyalty is not a mechanic (owner, 2026-10-20, item 10).
**Migration**: Use the ADDED requirement "Vassals live in a registry". Old saves keep working: the mod ignores the `loyalty` field.

### Requirement: Policies change tribute and loyalty
**Reason**: Loyalty is removed. The policies stay for the tribute factor.
**Migration**: Use the ADDED requirement "Policies change the tribute".

### Requirement: The gift order raises loyalty
**Reason**: Loyalty is removed, and the gift had no other effect.
**Migration**: None. The command `InvasionMod.vassals_order_gift` and the config `gift` are removed. A replacement effect is an open question for the owner (design question 1).

### Requirement: A vassal with low loyalty submits
**Reason**: A vassal survives or dies. Submission depended on loyalty only.
**Migration**: None. Remove the commands `vassals_submission_tick_now` and the config `submission`. A submitted vassal in an old save becomes a normal vassal.
