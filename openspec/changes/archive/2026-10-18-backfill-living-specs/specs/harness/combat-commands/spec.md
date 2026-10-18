# Spec Delta

## Purpose

Named harness commands that spawn units of a chosen type, count them, change their stats, hire mercenaries and steer the battle place. Fights in tests and A/B suites use them to set up and measure combat.

## ADDED Requirements

### Requirement: Units are counted by side and state
The harness SHALL answer `units_census` with the number of units by side (`player`, `ai`, `bandit`, `civil`), role, squad type and state, the loot carried and the squads. The sample rows SHALL NOT exceed 30 whatever `sample` asks, the squad rows SHALL NOT exceed 16, and the sample SHALL NOT list civil units. A unit with no squad SHALL count as `civil`. `units_census` SHALL NOT change the game.

#### Scenario: Counts by side and loot
- **WHEN** a client sends `units_census` with `sample` 2
- **THEN** the reply gives units by side, the loot total and carriers, the squad sizes and 2 sample rows
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

#### Scenario: A large sample is bounded
- **WHEN** a client sends `units_census` with `sample` 9999
- **THEN** the sample has at most 30 rows
- Checked by `harness/tests/test_fakegame_harnessunits.py`.

### Requirement: Units of a chosen template are spawned and registered
The harness SHALL spawn squads of a unit template on `spawn_units` for the side `player` or `bandit`, with `count` of squads from 1 to 6 and offsets `dx` and `dy` from the player pawn within 20000. It SHALL register each squad with its side, template and start size, and refuse bad input without spawning.

#### Scenario: A squad of the row size
- **WHEN** a client sends `spawn_units` for a template whose row has a squad size
- **THEN** the squad has that many units and is registered with its side and template
- **AND** a smaller row size gives a smaller squad
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: The side follows the owner pawn
- **WHEN** a client sends `spawn_units` with `side` player and then with `side` bandit
- **THEN** the first squad belongs to the player pawn and the second to the bandit pawn
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Bad input
- **WHEN** a client sends `spawn_units` with an unknown side, an unknown template, a count of 0 or 7, or an offset beyond 20000
- **THEN** the reply is not ok and nothing is spawned
- **AND** a failing game call is reported as an error
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

### Requirement: The state of spawned squads can be read and cleared
The harness SHALL answer `battle_state` for the registered squads (start size, living units, experience), kill registered squads on `clear_battle`, and write experience from 0 to 1000 on `set_squad_experience`. Casualties are the start size minus the living units. The harness SHALL touch only registered squads.

#### Scenario: Casualties and experience
- **WHEN** units of a registered squad die and a client sends `battle_state` with `detail` 1
- **THEN** the squad shows the start size, the living count and the experience per squad and per unit
- **AND** the unit rows are capped at 64
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Clear one side
- **WHEN** a client sends `clear_battle` with `side` bandit
- **THEN** the bandit squads die and are forgotten and the player squads stay
- **AND** units that this module did not spawn are not touched
- **AND** a bad side is refused
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Set experience
- **WHEN** a client sends `set_squad_experience` with a registered squad and `value` 20
- **THEN** every living unit of the squad reads 20 back
- **AND** an unknown squad or a value above 1000 is refused
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

### Requirement: Combat stats can be read, written and observed
The harness SHALL read the mean combat stats of registered squads on `unit_stats`, write one stat on all living units of a side on `set_unit_stat` (value 0 to 1000, read back), and count combat hits on `combat_hook` with `mode` `start`, `stop` or `read`. The stat fields are `att`, `def`, `block`, `armorPierce`, `morale`, `baseDefence`, `baseBlock` and `charge`.

#### Scenario: A live stat write
- **WHEN** a client sends `set_unit_stat` with `side` bandit, `field` def and `value` 0
- **THEN** the reply gives the number of living units and the number that read 0 back
- Not checked yet.

#### Scenario: Bad stat input
- **WHEN** a client sends `set_unit_stat` with a field outside the list, or a value above 1000, or a bad side
- **THEN** the reply is not ok and no unit is changed
- Not checked yet.

#### Scenario: The combat hook counts hits
- **WHEN** a client sends `combat_hook` with `mode` start, a fight runs, and the client sends `mode` read
- **THEN** the reply gives a call count above 0 and a count by side pair
- Not checked yet.

### Requirement: Mercenaries can be listed and hired
The harness SHALL list the offered companies on `mercenary_offers` and hire one on `hire_mercenaries`. It SHALL refuse a company that costs more than the silver, because the game does not check the cost, and a company that is unknown or missing.

#### Scenario: List and hire
- **WHEN** a client sends `mercenary_offers` and then `hire_mercenaries` for an offered company
- **THEN** the silver falls by the cost and one squad is made for each unit name
- **AND** the company is no longer offered
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Too little silver
- **WHEN** a client sends `hire_mercenaries` and the silver is below the cost
- **THEN** the reply is not ok and the silver and units are unchanged
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

#### Scenario: Unknown company
- **WHEN** a client sends `hire_mercenaries` with an unknown company or no company
- **THEN** the reply is not ok
- Checked by `harness/tests/test_fakegame_harnessbattle.py`.

### Requirement: The battle place of a challenge can be anchored
The harness SHALL move all battlefield actors to one anchor on `battlefield_anchor` and put them back after `delay_ms` (default 500, at most 30000). The anchor is the point `x`, `y`, or the manor of a `region` or of the `target`. With `lord` it SHALL start a challenge in the same step. `battlefield_state` SHALL read the positions and the anchor without moving anything.

#### Scenario: The challenge keeps the anchor
- **WHEN** a client sends `battlefield_anchor` with a `lord` and the village has a manor
- **THEN** the manor is the anchor and the challenge uses it
- **AND** without an anchor the challenge uses the first battlefield
- Checked by `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: The actors return
- **WHEN** the delay has passed after `battlefield_anchor`
- **THEN** every battlefield actor is back at its first position
- Checked by `harness/tests/test_fakegame_harnessbattlefield.py`.

#### Scenario: State and bad input
- **WHEN** a client sends `battlefield_state`, a second `battlefield_anchor` while one is active, or `battlefield_anchor` with bad numbers
- **THEN** the state names the anchor and moves nothing
- **AND** the second anchor and the bad numbers are refused
- Checked by `harness/tests/test_fakegame_harnessbattlefield.py`.

### Requirement: Spike probes for units and props are limited to a fixed list
The harness SHALL call only `equipTradeWagon`, `isWagonEquipped` or `getEquippedWagon` on a unit of a registered squad on `unit_probe`. It SHALL spawn at most 12 prop actors of the classes `Resource_BigCart_C`, `Resource_TimberCart_C`, `Resource_Handcart_C` and `Obstacle` near the player on `prop_spawn`, and destroy only its own props on `prop_clear`. `squad_positions` SHALL read the positions of the living units of a registered squad, at most 64.

#### Scenario: A call outside the list
- **WHEN** a client sends `unit_probe` with a `call` that is not in the list, or with a squad that is not registered
- **THEN** the reply is not ok and no function is called
- Not checked yet.

#### Scenario: Too many props
- **WHEN** a client sends `prop_spawn` and the total would pass 12, or with an unknown prop name
- **THEN** the reply is not ok and nothing is spawned
- Not checked yet.

### Requirement: A fight can run as one scenario with levers
The scenario `combat-levers` SHALL spawn a player group and a bandit group, apply the levers from the variant options (live stat writes, item writes, hook count), run the fight, and report casualties, loss rates, the winner and the fight time as metrics.

#### Scenario: Battle scenarios in the fake game
- **WHEN** the scenarios `unit-data`, `mercenary-hire`, `veterancy` and `counters-ab` run against the real Lua files in the fake game
- **THEN** they pass with the rules of the real game
- **AND** they fail when the game forgets experience, charges more than the listed cost, or has too few unit rows
- Checked by `harness/tests/test_fakegame_battle_scenarios.py`.

#### Scenario: One fight with a lever in the game
- **WHEN** `combat-levers` runs in the real game with `LEVER_SET_BANDIT` set to `def=0`
- **THEN** the metrics include casualties of both sides and the winner
- Not checked yet.
