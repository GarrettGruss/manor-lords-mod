# Spec Delta

## Purpose

The manor stronghold feature makes the manor the safest store and lets the tech tree grow its storage and its retinue. Both tech paths can use these upgrades.

## ADDED Requirements

### Requirement: Manor storage has a base capacity
The mod SHALL limit the goods in one manor module to a capacity. The base capacity is 200 units (config `manor_stronghold.storage_base_capacity`). A put of goods above the capacity SHALL be refused. The store is kept by the mod, because the base game does not use the Keep as a store.

#### Scenario: The base capacity is full
- **WHEN** the player has a built manor module and no upgrade
- **THEN** `InvasionMod.manor_state` shows the capacity 200
- **AND** a put of one more unit above 200 is refused
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/manor_storage.py`.

#### Scenario: Without a manor a put is refused
- **WHEN** no manor module is built
- **THEN** `InvasionMod.manor_put` is refused with a message
- Checked by `harness/tests/test_fakegame_manor_stronghold.py`.

### Requirement: Tech tree nodes raise the storage capacity
The capacity SHALL rise by the sum of the `manor_storage` effects of the unlocked tech tree nodes. The nodes Iron Hand (Oppression) and Amnesty (Prosperity) each give +200 units. The capacity changes at once when the node is unlocked.

#### Scenario: A Prosperity node doubles the capacity
- **WHEN** the player unlocks Amnesty
- **THEN** the capacity is 400
- **AND** a put of 150 more units works and a put above 400 is refused
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/manor_storage.py`.

#### Scenario: Both paths can upgrade
- **WHEN** the player unlocks Iron Hand on the Oppression path
- **THEN** the capacity rises by 200
- Checked by `harness/tests/test_fakegame_manor_stronghold.py`.

### Requirement: Goods in the manor stay and count in the region stock
The mod SHALL keep goods that are put in the manor until they are taken out. A put raises the region stock and a take lowers it by the same number. A take of more than the manor holds SHALL be refused.

#### Scenario: Put, take and wait
- **WHEN** the player puts 150 units, takes 50 units and waits 2 game days
- **THEN** the region stock follows the put (+150) and the take (-50)
- **AND** the manor total is unchanged after the wait
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/manor_storage.py`.

#### Scenario: A take of too much
- **WHEN** a take asks for more than the manor holds
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_manor_stronghold.py`.

### Requirement: Tech tree nodes raise the retinue limit that scripts read
The mod SHALL add the retinue bonus of the tech tree to the retinue limit of manor modules, and SHALL open the hire gate while the bound retinue is below the raised limit. The nodes Veteran Levies and Militia Rights each give +12. The native hire of the game still stops at its own limit of 12.

#### Scenario: The limit reads the bonus
- **WHEN** the player unlocks Militia Rights
- **THEN** `InvasionMod.retinue_state` shows the limit 24 and `can_hire` true
- **AND** `InvasionMod.retinue_hire` adds no man above the native limit of 12
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/retinue_capacity.py`.

#### Scenario: No bonus before the node
- **WHEN** the player has not unlocked a retinue node
- **THEN** the retinue bonus is 0 and the limit is 12
- Checked by `harness/tests/test_fakegame_manor_stronghold.py`.

### Requirement: Extra retinue squads
The mod SHALL let the player hire extra retinue squads above the native limit. Each 12 points of retinue bonus (config `bonus_per_squad`) allow one squad. A squad has 36 men (config `squad_men`, template `retinue_tier1`). The mod charges silver for the squad. It refuses a hire when the bonus allows no more squads or when the silver is too low.

#### Scenario: A squad needs the bonus
- **WHEN** the player calls `InvasionMod.retinue_squad_hire` with no retinue bonus
- **THEN** the call is refused and `squads_allowed` is 0
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/retinue_squads.py`.

#### Scenario: A squad of 36 men
- **WHEN** the player has Militia Rights and hires one squad
- **THEN** one squad exists with 36 living men owned by the player
- **AND** a second hire is refused
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/retinue_squads.py`.

#### Scenario: The squad fights
- **WHEN** a bandit raid of 18 men attacks
- **THEN** some bandits die
- **AND** at least 20 of the 36 men survive
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/retinue_squads.py`.

### Requirement: Named commands for the manor
The mod SHALL register the named commands `InvasionMod.manor_state`, `manor_put`, `manor_take`, `retinue_state`, `retinue_hire`, `retinue_squad_hire` and `retinue_squad_state`. Scenarios use them instead of eval.

#### Scenario: The manor commands exist
- **WHEN** a test scenario calls `manor_state`, `manor_put` and `manor_take`
- **THEN** each answers with the manor state
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/manor_storage.py`.

#### Scenario: The retinue commands exist
- **WHEN** a test scenario calls `retinue_state`, `retinue_hire`, `retinue_squad_hire` and `retinue_squad_state`
- **THEN** each answers with the retinue state
- Checked by `mod/InvasionMod/scenarios/manor_stronghold/retinue_squads.py`.
