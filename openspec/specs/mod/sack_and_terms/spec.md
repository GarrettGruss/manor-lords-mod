# mod/sack_and_terms Specification

## Purpose
A lost battle sacks the town and the game goes on. The invader offers terms while a raid is on the map, but not after a sack of the player region.

## Requirements

### Requirement: A lost battle sacks the town
The mod SHALL sack the town once when a role raid (a lord army) begins to leave for a reason in `sack.lost_reasons` (default `loot` and `time`). A raid that leaves for the reason `losses` or `terms`, and a native raid, SHALL NOT sack the town.

#### Scenario: A raid leaves with its loot
- **WHEN** a forced role raid begins to leave for the reason `loot`
- **THEN** the sack count rises by 1
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/raid_sack.py`.

#### Scenario: A raid that lost its raiders
- **WHEN** a raid leaves for the reason `losses`, or the raid is native
- **THEN** no sack happens
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: Sack size grows with difficulty
The mod SHALL take a share of standing buildings and families. The share in percent SHALL be `share_min + (share_max - share_min) x (difficulty - 1) / 2` (defaults 20 and 50, so 20, 35 and 50). Every count SHALL round up. A normal sack SHALL keep at least `min_families_left` families (default 1). The sack SHALL NOT take a share of the stock.

#### Scenario: A forced sack at each difficulty
- **WHEN** the command `InvasionMod.sack_now` runs at difficulty 1, 2 and 3
- **THEN** the standing buildings fall by about 20, 35 and 50 percent (plus or minus 1 building)
- **AND** the mod takes no goods from the stores
- **AND** at least 1 family stays and the population stays above 0
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.

#### Scenario: The share rule without the game
- **WHEN** the share is computed for difficulty 1 to 3
- **THEN** it is 20, 35 and 50, a normal sack keeps one family and the plan holds no goods
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: Repeated sacks can end the game
The mod SHALL count sacks in a window of `window_days` game days (default 360) that starts at the first sack. The sack that brings the count to `limit` (default 2) SHALL be fatal and SHALL remove all families. The switch `fatal.enabled` set to false SHALL only flag the limit. A sack after the window ends SHALL start a new window. The counter SHALL be kept in ModState.

#### Scenario: The second sack in the window
- **WHEN** two sacks happen inside the window with the fatal switch on
- **THEN** the second sack is fatal and takes every family
- **AND** with the switch off, the limit is flagged and people stay
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

#### Scenario: Two sacks in the real game with the switch off
- **WHEN** the command `InvasionMod.sack_set_fatal` turns the switch off and a second sack runs
- **THEN** the village still has people after the second sack
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.

### Requirement: The sack hits the right region
The mod SHALL sack the raid target when the player owns it. Else it SHALL sack the home region (`vassals_home_region`) when the player owns it. Else it SHALL sack the first region of the player. A manual sack SHALL use the home region. The sack result SHALL name the region.

#### Scenario: A sack after a fallback capital move
- **WHEN** a fallback capital exists and `sack_now` runs with no raid target
- **THEN** the sack result names the home region
- **AND** the capital loses no family
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack_region.py`.

#### Scenario: Region choice rule
- **WHEN** the raid targets a player region, a foreign region, or no known region
- **THEN** the sack hits that region, the home region, or the first player region
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: The invader offers terms
The mod SHALL open an offer and show a banner when a lord raid spawns (`terms.offer_on_spawn`, default true). The one-time payment SHALL be `payment_base x difficulty` silver (default 100, 200, 300). The yearly tribute SHALL be `tribute_base x difficulty` silver (default 30, 60, 90). The command `InvasionMod.terms_offer` SHALL open an offer by hand when a role raid is active.

#### Scenario: Offer amounts
- **WHEN** an offer opens at difficulty 1, 2 and 3
- **THEN** the payment is 100, 200 and 300 and the yearly tribute is 30, 60 and 90
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: Accepting terms ends the raid
The command `InvasionMod.terms_accept` SHALL end the raid early with the reason `terms`. With `kind=payment` it SHALL take the payment from the silver. With `kind=vassalage` it SHALL cost no silver now and set the next tribute day to the day plus `tribute_days` (default 360). The command `InvasionMod.terms_decline` SHALL close the offer and leave the raid alone.

#### Scenario: Payment
- **WHEN** a payment is accepted with enough silver during a lord raid
- **THEN** the silver falls by exactly the payment amount
- **AND** the raid leaves with the reason `terms` within 3 game days
- **AND** the town is not sacked for this raid
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/pay_terms.py`.

#### Scenario: Not enough silver
- **WHEN** a payment is accepted with less silver than the amount, or with no offer open
- **THEN** the command is refused and nothing changes
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: A term vassal pays a yearly tribute
The mod SHALL charge the yearly tribute once the tribute day is reached after vassalage terms. The charge SHALL be the tribute amount, or all silver if the silver is lower. The next tribute day SHALL move on by `tribute_days`.

#### Scenario: The tribute day
- **WHEN** the game day reaches the tribute day after vassalage terms
- **THEN** the silver falls by the tribute amount, or to 0 when it is lower
- **AND** the next tribute day is `tribute_days` later
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

### Requirement: A fortified vassal becomes the fallback capital
The command `InvasionMod.fallback_move` with a vassal slot SHALL take the region back from its lord, mark the slot as the capital with no lord, take `cost_base x difficulty` silver (default 150), move grain from home, and settle 5 families there. It SHALL be refused, at no cost, when it cannot be done.

#### Scenario: A successful move
- **WHEN** a handed-over vassal with enough buildings becomes the fallback capital
- **THEN** the region owner is the player pawn
- **AND** the silver falls by `150 x difficulty`
- **AND** the grain taken from home (`grain_amount`, default 20, of bread, grain or fish) equals the grain put into the capital
- **AND** the capital gets 5 families and the slot has no lord
- **AND** 5 game days later the region is still the player region and the game has not crashed
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/fallback_capital.py`.

#### Scenario: Refusals
- **WHEN** the slot is empty, a capital exists, the vassal has fewer than `min_buildings` buildings (default 8), or the silver is too low
- **THEN** the command is refused and nothing is paid
- Checked by `harness/tests/test_fakegame_fallback.py`.

### Requirement: The feature offers named commands
The mod SHALL register `InvasionMod.sack_state`, `sack_now`, `sack_set_fatal`, `terms_state`, `terms_offer`, `terms_accept`, `terms_decline`, `fallback_state`, `fallback_move`, `fallback_set_take_back` and `fallback_set_min_buildings`. Scenarios SHALL use these commands and not eval.

#### Scenario: A state command answers
- **WHEN** a scenario sends `InvasionMod.sack_state`
- **THEN** the answer holds the sack count, the window values and the share for the current difficulty
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.

### Requirement: The mod destroys no goods in a sack
The mod SHALL NOT remove goods from a sacked building. A fire that burns a store MAY destroy part of its goods (owner decision 2026-10-21: accept the loss); the mod SHALL NOT add them back. Only the plunder tick of a raid SHALL remove goods on purpose.

#### Scenario: The mod takes no goods
- **WHEN** a sack runs
- **THEN** the sack result reports 0 goods removed by the mod
- Checked by `harness/tests/test_fakegame_sack_and_terms.py`.

#### Scenario: A burned store may lose goods in the fire
- **WHEN** a sack with method `fire` turns a store into rubble
- **THEN** the ruin holds the goods that the fire left, and the scenario records the loss without failing
- Checked by `harness/scenarios/sack_ruins.py`.

### Requirement: Sacked buildings become rubble
Each building the sack hits SHALL be rubble when the sack ends or within a time limit. The default method `collapse` makes rubble at once. The method `fire` makes rubble only when villagers do not fight the fire, which is the case when enemy soldiers are in the village.

#### Scenario: A sack makes rubble
- **WHEN** a sack runs
- **THEN** every building the sack hit is rubble and stays in the building list
- Checked by `mod/InvasionMod/scenarios/sack_and_terms/sack.py`.
