# mod/order_tooltip Specification

## Purpose
The Public Order tooltip shows the mod order terms as rows and the mod order in its header, so the player sees why the mod order has its value.

## Requirements

### Requirement: The Public Order tooltip lists the mod order terms
Each time the player opens the Public Order tooltip, the mod SHALL add one row for each term of the last order tick of the mod order: `Manor +<n>` (green, only when the manor term is not 0), `Homeless families -<n>` (red, only when the term is above 0) and, from a revolt until the next tick, `Peasants revolted +<n>` (green). The values SHALL be the values of the last tick and of the last revolt, in order points. A row with a positive value SHALL show a green up arrow, and a row with a negative value SHALL show a red down arrow.

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
- **WHEN** peasants revolted and no tick ran since
- **THEN** the row `Peasants revolted +25` shows, and it is gone after the next tick
- **AND** no row is named `Left for banditry`
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

#### Scenario: One set of rows for each open
- **WHEN** the player opens the tooltip twice
- **THEN** each open shows one row for each term, with no duplicates
- Checked by `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

#### Scenario: A positive row shows an up arrow
- **WHEN** the tooltip shows `Manor +10` and `Homeless families -10`
- **THEN** the Manor row shows a green up arrow and the Homeless row shows a red down arrow
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and a picture from `mod/InvasionMod/scenarios/order_tooltip/rows.py`.

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

### Requirement: The tooltip shows a revolt counter while the banditry timer runs
While the banditry timer runs, the tooltip SHALL show the counter `Peasants revolt in <N> days` below the term rows (`1 day` for N = 1, `Peasants revolt today` for N = 0). N is `timer_start + timer_days - today` in game days. When the timer expired and the revolt was blocked, N SHALL be the days to the next order tick (the next try). Without a timer, there SHALL be no counter. The counter and the blocked item keep the game text colour (the label does not take a colour).

#### Scenario: A timer runs
- **WHEN** the order is under the threshold, the timer started 20 game days ago and `timer_days` is 60
- **THEN** the tooltip shows `Peasants revolt in 40 days`
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/revolt_timer.py`.

#### Scenario: No timer
- **WHEN** the order is at the threshold or above, so no timer runs
- **THEN** the tooltip has no counter and no blocked item
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/revolt_timer.py`.

#### Scenario: The revolt was blocked
- **WHEN** the timer expired, the revolt was blocked, and the next order tick is in 12 game days
- **THEN** the counter shows `Peasants revolt in 12 days`
- Checked by `harness/tests/test_fakegame_order_tooltip.py`.

### Requirement: The tooltip shows why a revolt would be blocked
Below the counter, the tooltip SHALL show the text item `Revolt blocked: <V> of <N> armed homes` only while the revolt would be blocked. V is the number of valid armed families, N is the number of families that must revolt. When there is no Outlaws pawn, the item SHALL read `Revolt blocked: no Outlaws pawn`. When the revolt can happen, the item SHALL NOT show. The item SHALL show no value and no arrow if the tooltip can draw a text with no value; if it cannot, it uses the label and value shape of the other rows (`Revolt blocked | V of N armed homes`). The count of armed homes SHALL be cached for `armed_cache_seconds` (default 3) real seconds, so the tooltip does not read every home at each open.

#### Scenario: Too few armed homes
- **WHEN** the timer runs, 3 families are valid and 6 must revolt
- **THEN** the item `Revolt blocked: 3 of 6 armed homes` shows below the counter
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/revolt_timer.py`.

#### Scenario: The revolt can happen
- **WHEN** the timer runs, at least 6 families are valid and the Outlaws pawn exists
- **THEN** the counter shows and the blocked item does not
- Checked by `harness/tests/test_fakegame_order_tooltip.py` and `mod/InvasionMod/scenarios/order_tooltip/revolt_timer.py`.

#### Scenario: No Outlaws pawn
- **WHEN** the timer runs, enough families are valid and the game has no Outlaws pawn
- **THEN** the item `Revolt blocked: no Outlaws pawn` shows
- Checked by `harness/tests/test_fakegame_order_tooltip.py`.

#### Scenario: The count is cached
- **WHEN** the tooltip opens twice within `armed_cache_seconds`
- **THEN** the homes are read once
- Checked by `harness/tests/test_fakegame_bandits.py`.
