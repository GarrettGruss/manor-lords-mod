# mod/tribute Specification

## Purpose
Handed-over vassals send goods to the player each season. A raid on a vassal region changes the loyalty of that vassal, and a long siege can take the vassal.

## Requirements

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

### Requirement: Tribute is paid once for each season change
The mod SHALL pay at most one tribute for each season change and none while the season stays. The mod SHALL NOT pay on the first poll after a load. A season change with no handed-over vassal SHALL pay nothing.

#### Scenario: Two polls in one season
- **WHEN** the season changes once and the poll runs several times
- **THEN** exactly one payment happens
- **AND** a season change with no vassal pays 0
- Checked by `mod/InvasionMod/scenarios/tribute/tribute_payout.py`.

#### Scenario: The first poll
- **WHEN** the mod loads and polls for the first time
- **THEN** no tribute is paid
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: A refused deposit is counted
The mod SHALL try each store until one takes the full amount of a good. When no store takes it, the mod SHALL log the refusal, count it in `failed_deposits` and SHALL NOT count the amount as paid.

#### Scenario: No store takes the goods
- **WHEN** every store refuses a deposit
- **THEN** `failed_deposits` rises and the paid amount stays 0
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: Vassals also pay finite goods
The mod SHALL pay iron and salt next to the main goods, with the same share, as `families x units_per_family` of each good in `tribute.finite_goods` (default iron 10, salt 6). The policy factor SHALL scale these goods too.

#### Scenario: Iron and salt
- **WHEN** a vassal with 5 families pays at a season change
- **THEN** the stock gains 10 iron and 6 salt
- Checked by `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py`.

### Requirement: A long siege takes a vassal
The mod SHALL take a vassal (loss reason `taken`) when a subjugation raid on its region has been active for `siege.days` game days (default 8) with at least `siege.min_living` of its units alive (default 0.5). A vassal SHALL be lost once for each raid. A younger raid, a beaten raid, a plunder raid and a raid on the home region SHALL take nothing.

#### Scenario: A subjugation raid holds for 8 days
- **WHEN** a subjugation raid targets a vassal region and stays active for 8 game days
- **THEN** the vassal is lost with the reason `taken`
- Checked by `mod/InvasionMod/scenarios/invasion/vassal_targets.py`.

#### Scenario: Siege rules in the fake game
- **WHEN** the raid is younger than 8 days, beaten, a plunder raid, or targets home
- **THEN** the vassal stays
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.tribute_state` and `tribute_tick_now`. `tribute_tick_now` SHALL pay at once. Scenarios SHALL use these commands and not eval.

#### Scenario: A forced tick
- **WHEN** a scenario sends `InvasionMod.tribute_tick_now`
- **THEN** the tribute is paid at once and `tribute_state` shows the history
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: The policy factor scales the tribute
The mod SHALL multiply the share by the tribute factor of the vassal policy (0.5 `light`, 1.0 `fair`, 1.5 `heavy`).

#### Scenario: Heavy and light policies
- **WHEN** a season changes with a `heavy` vassal and with a `light` vassal
- **THEN** the share is 1.5 times and 0.5 times the `fair` share
- Checked by `harness/tests/test_fakegame_tribute.py`.
