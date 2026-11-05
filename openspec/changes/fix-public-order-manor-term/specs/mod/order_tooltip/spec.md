## MODIFIED Requirements
<!-- Issue: #557 -->

### Requirement: The Public Order tooltip lists the mod order terms
Each time the player opens the Public Order tooltip, the mod SHALL add one row for each term of the last order tick of the mod order: `Manor +<n>` (green, only when the manor term is not 0), `Homeless families -<n>` (red, only when the term is above 0) and, from a leave until the next tick, `Left for banditry +<n>` (green). The values SHALL be the values of the last tick and of the last leave, in order points. A row with a positive value SHALL show a green up arrow, and a row with a negative value SHALL show a red down arrow.

#### Scenario: Rows match the last tick
- **WHEN** a tick ran with a built manor (manor term 10) and 2 homeless families, and the player opens the tooltip
- **THEN** the rows `Manor +10` and `Homeless families -10` are in the tooltip, with the colours green and red
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py` and `harness/tests/test_fakegame_order_tooltip.py`.

#### Scenario: No built manor
- **WHEN** the last tick ran with no built manor and no tech bonus (manor term 0)
- **THEN** there is no `Manor` row
- Checked by `harness/tests/test_fakegame_order_tooltip.py`.

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

#### Scenario: A positive row shows an up arrow
- **WHEN** the tooltip shows `Manor +10` and `Homeless families -10`
- **THEN** the Manor row shows a green up arrow and the Homeless row shows a red down arrow
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and a picture from `mod/InvasionMod/scenarios/order_tooltip/rows.py`.
