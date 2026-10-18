# Spec Delta

## Purpose

Makes armor matter in battle. The feature `unit_balance` changes unit values (armor, weapon, reach, experience), and raids spawn Hussite roles from existing foot units.

## ADDED Requirements

### Requirement: Unarmored units lose defence
The mod SHALL cut `def` and `block` of every new living unit whose `def` is below `armored_def_min` (default 10) by the factors `unarmored_def_factor` and `unarmored_block_factor` (default 0 and 0). The rule SHALL hold for all sides. A unit with `def` 0 and `block` 0 SHALL be skipped.

#### Scenario: Unarmored militia and bandits are changed
- **WHEN** a squad of `spearMilitia` and a squad of `Brigands` spawn and one pass runs
- **THEN** the mean `def` and `block` of the units that the rule counts as unarmored equal the base value times the factor (0 with the default factors)
- **AND** every unit counted as unarmored is changed
- Checked by `mod/InvasionMod/scenarios/unit_balance/armored_kept.py`.

#### Scenario: Unarmored units lose more of their group
- **WHEN** 32 `spearMilitia` fight 2 squads of `Brigands` with the rule on and with the rule off
- **THEN** the mean militia loss rate with the rule on is 1.5 to 3.5 times the mean with the rule off
- Checked by `mod/InvasionMod/scenarios/unit_balance/lethality.py`.

#### Scenario: Classification and writes without the game
- **WHEN** units with `def` below, equal to and above the limit are classified in the fake game
- **THEN** only the units below the limit are changed, a dead unit is left alone, and a unit is changed once
- Checked by `harness/tests/test_fakegame_unit_balance.py`.

### Requirement: Armored units are not weakened
The mod SHALL leave `def` and `block` unchanged for a unit whose `def` is at or above `armored_def_min`. The mod SHALL leave att and armorPierce unchanged for a heavy unit (`def` at or above `heavy_def_min`, default 40).

#### Scenario: A retinue squad keeps its values
- **WHEN** a `retinue_tier3` squad (`def` about 62) spawns and the rule runs
- **THEN** its `def`, `block`, `att` and `armorPierce` keep the original values
- Checked by `mod/InvasionMod/scenarios/unit_balance/armored_kept.py`.

### Requirement: New units are found by a poll
The mod SHALL poll for new units every `poll_ms` (default 4000 ms) and apply the rules to a unit that spawns later, without a command. A known unit SHALL cost no read of `def`, except every `recheck_every` pass (default 10) or when the unit count changes.

#### Scenario: A later squad is changed
- **WHEN** a second squad spawns after the first pass and no command is sent
- **THEN** the unit values of the second squad are changed within a few polls
- Checked by `mod/InvasionMod/scenarios/unit_balance/armored_kept.py`.

#### Scenario: The poll in the fake game
- **WHEN** a unit is added to the fake game after the first poll
- **THEN** the next poll changes it
- Checked by `harness/tests/test_fakegame_unit_balance.py`.

### Requirement: Armored units get a weapon bonus
The mod SHALL multiply `att` by `armored_att_factor` (default 1.5) and add `armored_pierce_add` (default 2) to `armorPierce` for a unit with `def` from `armored_def_min` up to `heavy_def_min`. The bonus SHALL be written once for each unit.

#### Scenario: Armored militia beat a larger bandit group
- **WHEN** 32 armored `spearMilitia` (`def` about 17) fight 4 squads of `Brigands` (2.25 times their size) with the weapon bonus on
- **THEN** the militia win in most runs
- **AND** the militia loss rate is lower than with the bonus off
- Checked by `mod/InvasionMod/scenarios/unit_balance/armored_fight.py`.

#### Scenario: Weapon values in the fake game
- **WHEN** an armored, a heavy and an unarmored unit are classified
- **THEN** only the armored unit gets the weapon values
- Checked by `harness/tests/test_fakegame_unit_balance.py`.

### Requirement: Pike units get a reach bonus
The mod SHALL add `reach_att_add` (default 1.0) to `att` of a unit whose weapon reach is between `reach_min` and `reach_max` (default 110 to 125). A value of 0 SHALL switch the bonus off.

#### Scenario: Pikes against swords
- **WHEN** `spearMilitia` fight `militiaFoot` with the reach bonus on and off
- **THEN** the spear group wins more often with the bonus on
- Checked by `mod/InvasionMod/scenarios/unit_balance/matchup.py`.

#### Scenario: Reach bands in the fake game
- **WHEN** units with reach 65, 100, 120 and 130 are classified
- **THEN** only the unit with reach 120 gets the bonus
- Checked by `harness/tests/test_fakegame_unit_balance.py`.

### Requirement: Experience makes veterans
The mod SHALL scale `att` and `def` of a unit by `1 + tier x per_tier` (default `per_tier` 0.1). The tier SHALL be `floor(combatExperience / step)` (default `step` 1.0), at most `max_tier` (default 5). The mod SHALL read experience on every `veterancy.every` pass (default 5).

#### Scenario: Veterans lose fewer units
- **WHEN** militia with experience 5 and militia with experience 0 fight the same enemy
- **THEN** the veteran group has the lower loss rate in most runs
- Checked by `mod/InvasionMod/scenarios/unit_balance/matchup.py`.

#### Scenario: Tiers in the fake game
- **WHEN** the experience of a unit rises, passes the cap or is 0
- **THEN** the scale follows the tier, stops at `max_tier`, and a unit without experience is unchanged
- Checked by `harness/tests/test_fakegame_unit_balance.py`.

### Requirement: The rules can be tuned and switched off
The mod SHALL offer the named commands `InvasionMod.unit_balance_state`, `InvasionMod.unit_balance_set` and `InvasionMod.unit_balance_apply`. Setting `enabled` to false SHALL put the original values back on every unit that the rules changed. A factor outside its range SHALL be refused.

#### Scenario: Switch off restores the values
- **WHEN** a scenario sends `unit_balance_set` with `enabled=false` after units were changed
- **THEN** the units have their original values
- Checked by `mod/InvasionMod/scenarios/unit_balance/armored_kept.py`.

#### Scenario: A bad factor
- **WHEN** `unit_balance_set` gets a factor above 1 for `def_factor`
- **THEN** the command is refused with a clear error
- Checked by `harness/tests/test_fakegame_unit_balance.py`.
