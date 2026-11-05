## MODIFIED Requirements
<!-- Issue: #557 -->

### Requirement: Public order ticks every 30 game days
Every `tick_days` (default 30) game days, the mod SHALL set `order = clamp(order + manor_term - homeless_term)`. The manor term SHALL be `10` plus `order_bonus` when the player's manor is built, and only `order_bonus` when it is not built. A manor that is still a construction site SHALL count as not built. `homeless_term` is `5 x homeless villagers`, where a homeless villager is a homeless family (`getNumHomelessFamilies`). Each tick SHALL be logged in the telemetry with day, order before, manor built, manor term, homeless count, homeless term and order after, and in one `HarnessLog` line.

#### Scenario: A tick with homeless villagers
- **WHEN** the manor is built, the order is 50 and 4 villagers are homeless
- **THEN** the tick gives 40 (50 + 10 - 20) and the telemetry record holds all seven fields
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: A tick without a built manor
- **WHEN** no manor is built, the order is 50 and no villager is homeless
- **THEN** the manor term is 0 and the tick leaves the order at 50
- Checked by `harness/tests/test_bandits_rules.py` and `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The tech bonus without a manor
- **WHEN** no manor is built and `order_bonus` is 10
- **THEN** the manor term is 10
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: The tick interval
- **WHEN** the game runs 65 game days
- **THEN** between 2 and 3 ticks ran
- Checked by `mod/InvasionMod/scenarios/bandits/order_tick.py`.
