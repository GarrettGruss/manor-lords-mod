## MODIFIED Requirements
<!-- Issue: #344 -->

### Requirement: Vassals pay goods each season
At each season change the mod SHALL pay goods into a player store for each handed-over vassal. No goods SHALL move between regions. The production SHALL be `families x units_per_family` (default 20). The share SHALL be fixed (`tribute.share`, default 0.20). The amount SHALL be `round(production x share)`, split equally over the goods in `tribute.goods` (default fish and timber), and the remainder SHALL go to the first good.

#### Scenario: A season change with one vassal
- **WHEN** one vassal with 5 families is registered and the season changes
- **THEN** the home stores gain 20 goods (10 fish and 10 timber)
- **AND** the game runs without a crash
- Not checked yet (planned: `mod/InvasionMod/scenarios/tribute/tribute_payout.py`, updated).

#### Scenario: Payout rules without the game
- **WHEN** the share, the amount and the split are computed for several family counts
- **THEN** they follow the formulas above
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: Vassals also pay finite goods
The mod SHALL pay iron and salt next to the main goods, with the same share, as `families x units_per_family` of each good in `tribute.finite_goods` (default iron 10, salt 6). The policy factor SHALL scale these goods too.

#### Scenario: Iron and salt
- **WHEN** a vassal with 5 families pays at a season change
- **THEN** the stock gains 10 iron and 6 salt
- Checked by `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.tribute_state` and `tribute_tick_now`. `tribute_tick_now` SHALL pay at once. Scenarios SHALL use these commands and not eval.

#### Scenario: A forced tick
- **WHEN** a scenario sends `InvasionMod.tribute_tick_now`
- **THEN** the tribute is paid at once and `tribute_state` shows the history
- Checked by `harness/tests/test_fakegame_tribute.py`.

## ADDED Requirements

### Requirement: The policy factor scales the tribute
The mod SHALL multiply the share by the tribute factor of the vassal policy (0.5 `light`, 1.0 `fair`, 1.5 `heavy`).

#### Scenario: Heavy and light policies
- **WHEN** a season changes with a `heavy` vassal and with a `light` vassal
- **THEN** the share is 1.5 times and 0.5 times the `fair` share
- Checked by `harness/tests/test_fakegame_tribute.py`.

## REMOVED Requirements

### Requirement: The vassal policy scales the tribute
**Reason**: Renamed to "The policy factor scales the tribute" because its scenario about a submitted vassal is dropped (submission is removed).
**Migration**: Use the ADDED requirement "The policy factor scales the tribute".

### Requirement: A raid on a vassal changes its loyalty
**Reason**: Loyalty is removed (owner, 2026-10-20, item 10). A vassal survives or dies.
**Migration**: None. Remove `InvasionMod.tribute_test_raid_result`, the config `protection` and the test scenario `protection_and_loyalty.py`. The siege rule (requirement "A long siege takes a vassal") stays.
