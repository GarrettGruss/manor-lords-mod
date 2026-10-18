# Spec Delta

## Purpose

The finite resources feature makes home deposits of iron, salt and clay run out. Vassal tribute is the permanent supply of iron and salt.

## ADDED Requirements

### Requirement: Three home deposits with a stock
The mod SHALL keep one mod-owned stock for each home deposit: iron, salt and clay. The default sizes are 400, 300 and 500 units (config `finite_resources.resources`). A new game starts with every deposit full and no production limit.

#### Scenario: A new game starts with full deposits
- **WHEN** the mod has loaded in a game with no mined units
- **THEN** the command `InvasionMod.finite_resources_state` lists the deposits clay, iron and salt
- **AND** each deposit has `remaining` equal to `size`, `mined` equal to 0 and no production limit
- Checked by `mod/InvasionMod/scenarios/finite_resources/iron_deposit.py`.

#### Scenario: Salt and clay are deposits too
- **WHEN** the fake game reads the state of the feature
- **THEN** the three deposits exist and an empty salt deposit limits only salt
- Checked by `harness/tests/test_fakegame_finite_resources.py`.

### Requirement: Production counts the stock down
The mod SHALL count the units that the buildings of the player produce, and SHALL reduce the stock of the matching deposit by that number. The mod looks at the production total every `poll_ms` (default 5000 ms real time). Units produced before the first look and a fall of the total (a lost building) count as 0.

#### Scenario: Production reduces the stock
- **WHEN** the buildings of the player produce units of the good of a deposit
- **THEN** `mined` rises by the new units
- **AND** `remaining` equals `size` minus `mined`
- Checked by `mod/InvasionMod/scenarios/finite_resources/iron_deposit.py`.

#### Scenario: Old production and falling totals do not count
- **WHEN** the first look finds a production total, or a later total is lower than the last one
- **THEN** `mined` does not change
- Checked by `harness/tests/test_fakegame_finite_resources.py`.

### Requirement: An empty deposit stops the production
The mod SHALL set the production limit of the good to 0 for the player region when a deposit is empty. The good is then no longer produced, except for a work cycle that has already begun.

#### Scenario: A deposit runs out
- **WHEN** `mined` reaches `size` of a deposit
- **THEN** the production limit of its good is 0
- **AND** the production total of the good rises by at most 2 units in the next 3 game days
- Checked by `mod/InvasionMod/scenarios/finite_resources/iron_deposit.py`.

#### Scenario: Only the empty deposit is limited
- **WHEN** the salt deposit is empty and the iron deposit is not
- **THEN** only salt has a production limit
- Checked by `harness/tests/test_fakegame_finite_resources.py`.

### Requirement: The stock is saved with the game
The mod SHALL keep the mined units and the last production total of each deposit in mod state (the player pawn tags), so a loaded game keeps the stock. The mod SHALL NOT call a save function.

#### Scenario: The stock is kept in the pawn tags
- **WHEN** units are mined
- **THEN** the mod state keys `fin_<name>_mined` and `fin_<name>_last` hold the values
- Checked by `harness/tests/test_fakegame_finite_resources.py`.

### Requirement: Vassals pay iron and salt as the permanent supply
The tribute of a vassal SHALL include iron and salt next to the main goods (config `tribute.finite_goods`: iron 10 and salt 6 units for each family at full share). The share follows loyalty, vassal policy and laws like the main goods. Tribute goods are not production, so they do not reduce a home deposit.

#### Scenario: One vassal pays at a season change
- **WHEN** one vassal with 5 families and loyalty 50 pays at a season change
- **THEN** the tribute paid is 10 iron and 6 salt
- **AND** the home stores rise by at least 10 iron and 6 salt
- **AND** the `mined` count of iron and salt stays 0
- Checked by `mod/InvasionMod/scenarios/finite_resources/vassal_supply.py`.

#### Scenario: A policy scales the finite goods
- **WHEN** a vassal policy or a law changes the tribute share
- **THEN** the paid iron and salt change with the share
- Checked by `harness/tests/test_fakegame_tribute.py`.

### Requirement: Scenarios can read and change the deposits
The mod SHALL register the named commands `InvasionMod.finite_resources_state`, `InvasionMod.finite_resources_test_set` and `InvasionMod.finite_resources_test_clear`. The state lists each deposit with `good`, `size`, `mined`, `remaining`, `empty` and `limit`. The two test commands change a deposit for the session only.

#### Scenario: A test lends a deposit to another good
- **WHEN** `finite_resources_test_set` gives the deposit iron another good and a size of 4
- **THEN** the deposit counts down with the production of that good
- **AND** `finite_resources_test_clear` lifts the production limit again
- Checked by `mod/InvasionMod/scenarios/finite_resources/iron_deposit.py`.
