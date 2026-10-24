## ADDED Requirements
<!-- Issue: #454 -->

### Requirement: The Public Order tooltip lists the mod order terms
Each time the player opens the Public Order tooltip, the mod SHALL add one row for each term of the last order tick of the mod order: `Manor +<n>` (green), `Homeless families -<n>` (red, only when the term is above 0) and, from a leave until the next tick, `Left for banditry +<n>` (green). The values SHALL be the values of the last tick and of the last leave, in order points.

#### Scenario: Rows match the last tick
- **WHEN** a tick ran with manor term 10 and 2 homeless families, and the player opens the tooltip
- **THEN** the rows `Manor +10` and `Homeless families -10` are in the tooltip, with the colours green and red
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py` and `harness/tests/test_fakegame_order_tooltip.py`.

#### Scenario: No homeless family
- **WHEN** the last tick had 0 homeless families
- **THEN** there is no `Homeless families` row
- Checked by `harness/tests/test_fakegame_order_tooltip.py`.

#### Scenario: Left for banditry
- **WHEN** families left for banditry and no tick ran since
- **THEN** the row `Left for banditry +25` shows, and it is gone after the next tick
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

#### Scenario: One set of rows for each open
- **WHEN** the player opens the tooltip twice
- **THEN** each open shows one row for each term, with no duplicates
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

### Requirement: The tooltip header shows the mod order
While the mod order is active, the header sum of the tooltip SHALL show the mod order (for example `77%`), and the native rows SHALL be hidden (default; owner decision open).

#### Scenario: Header equals the mod order
- **WHEN** the tooltip is open
- **THEN** the header text equals the mod order of `InvasionMod.bandits_state`, as a percentage
- **AND** no native factor row is in the list
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

### Requirement: The tooltip works while the game is paused and fails safe
The rows SHALL show with the game paused. If the hook does not fire or a widget call fails, the tooltip SHALL stay native, the mod SHALL log the problem once, and no error SHALL be raised.

#### Scenario: Paused game
- **WHEN** the game is paused and the player opens the tooltip
- **THEN** the mod rows and the header show
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

#### Scenario: A failing widget call
- **WHEN** adding a row raises an error
- **THEN** the call raises to the caller, which logs it once and does not pass it to the game
- The log-once is Not checked yet (the raise is checked by `harness/tests/test_fakegame_order_tooltip.py`).
