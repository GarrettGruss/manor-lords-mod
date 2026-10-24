# mod/bandits Specification

## Purpose
The bandits feature turns low approval into low Public Order, and low Public Order into bandits. The player fights the bandits or pays silver to bring the families back.

## Requirements

### Requirement: A conversion removes two families and spawns a bandit squad
When the banditry timer expires, the mod SHALL remove `leavers` (default 18) villagers, as families, and SHALL spawn one bandit camp (`RTSMultiEngineCPP:spawnBanditCamp()`, a camp with 18 Brigands) for the leave event. The mod SHALL NOT spawn squads at the homes. The number of squads does not depend on the number of families (the rule "one squad per 5 families" is removed). When the game has no bandit pawn, the same call SHALL make the bandit pawn, and the mod SHALL then call `addPawnRelations` for it, so villager banditry works with the game setting bandit camps 0. The game picks the camp place; the mod SHALL log the camp place. A villager here is a family. The village SHALL keep at least `min_families_left` (default 1) families, so fewer than 18 may leave. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** the banditry timer expires (a test forces it) with enough villagers
- **THEN** the villagers that leave are between 1 and 18, and the village keeps at least 1 family
- **AND** one bandit camp exists and the bandit units grow by 18
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the timer expires
- **THEN** no family leaves and no camp spawns
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: One squad for every 5 families
- **WHEN** 18 families leave (the old rule gave 3 squads)
- **THEN** exactly one camp spawns, whatever the number of families, and no squad spawns at the homes
- Checked by `harness/tests/test_fakegame_bandits.py` and `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: No bandit pawn
- **WHEN** villagers leave and the game has no bandit pawn (bandit camps 0)
- **THEN** the mod makes the bandit pawn with the camp (one `spawnBanditCamp` call) and calls `addPawnRelations`
- **AND** the bandit pawn exists afterward
- Checked by `harness/tests/test_fakegame_bandits.py` and a real run on fixture `playtest-noai` (proposed).

#### Scenario: The conversion banner
- **WHEN** villagers leave for banditry
- **THEN** the banner `Families have turned to banditry` shows
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.

### Requirement: The player can buy families back
`InvasionMod.bandits_buy_back` SHALL send the native settle letter. The price SHALL be `ceil(min(outstanding families, free home slots) x silver_per_family x price_multiplier)` (default 10 silver a family). The mod SHALL refuse, with a reason and no change, when no family is outstanding, no bandit unit is on the map, no home slot is free, the silver is below the price, or another buy-back is running.

#### Scenario: A buy-back with enough silver
- **WHEN** 2 families are outstanding, a home slot is free, and the silver covers the price
- **THEN** the silver falls by exactly the price and the bandit units go down to 0
- **AND** the families that return are between 1 and the free slots, and the outstanding families fall by that number
- Checked by `mod/InvasionMod/scenarios/bandits/buy_back.py`.

#### Scenario: A refused buy-back
- **WHEN** the silver is below the price, or nothing is outstanding
- **THEN** the answer has `accepted = false` and a reason, and silver, families and bandit units do not change
- Checked by `mod/InvasionMod/scenarios/bandits/buy_back.py`.

#### Scenario: No free home slot
- **WHEN** no home slot is free
- **THEN** the buy-back is refused
- Checked by `harness/tests/test_fakegame_bandits.py`.

### Requirement: A failed buy-back gives the silver back
If no family returns within `give_up_game_seconds` (default 120 game seconds), the mod SHALL refund the silver that the game took, at most the price. The families SHALL stay outstanding for a later buy-back, and the result SHALL show the refunded amount.

#### Scenario: The deal fails
- **WHEN** the letter takes the silver and no family returns
- **THEN** the silver is back to its value before the letter and the outstanding families are unchanged
- **AND** the result `refunded` equals the price
- Checked by `mod/InvasionMod/scenarios/bandits/buy_back.py`.

### Requirement: The tech tree can change the bandit rules
The mod SHALL accept the modifiers `order_bonus` (added to the manor term of each tick) and `buy_back_multiplier` (a factor on the price) from the tech tree, and SHALL apply them at once.

#### Scenario: Price multipliers
- **WHEN** the multiplier is 1.25 or 0.5
- **THEN** the price is 13 or 5 for 1 family, and 25 or 10 for 2 families
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: Order bonus
- **WHEN** `order_bonus` is 5 and a tick runs
- **THEN** the manor term is 15
- Checked by `harness/tests/test_bandits_rules.py`.

### Requirement: Named commands show and drive the feature
The mod SHALL offer `InvasionMod.bandits_state`, `bandits_tick_now`, `bandits_set_order`, `bandits_buy_back` and the test commands `bandits_leave_now` and `bandits_set_timer_days_left`. `bandits_tick_now` SHALL run one order tick at once. `bandits_state` SHALL return the mod order, the game order, the homeless count, the last tick, the timer (start day and days left), families, outstanding and returned families.

#### Scenario: A forced tick
- **WHEN** a test calls `bandits_tick_now`
- **THEN** the answer is the new state, and the last tick has day, order before, manor term, homeless count, homeless term and order after
- Checked by `mod/InvasionMod/scenarios/bandits/order_tick.py`.

### Requirement: The mod keeps its own public order
The mod SHALL keep a mod order value, kept between 0 and 100, in ModState. The value SHALL start at 100 in a new game. It SHALL write `Region.publicOrder = mod order` for the home region at every tick. Game factors SHALL NOT change the mod order.

#### Scenario: The game value is overwritten
- **WHEN** the game writes its own order after the mod wrote
- **THEN** the mod writes the mod order again at the next tick
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: A reload
- **WHEN** the feature loads again
- **THEN** the mod order and the tick day come from ModState
- Checked by `harness/tests/test_fakegame_bandits.py`.

### Requirement: Public order ticks every 30 game days
Every `tick_days` (default 30) game days, the mod SHALL set `order = clamp(order + manor_term - homeless_term)`, with `manor_term = 10` (plus `order_bonus`) and `homeless_term = 5 x homeless villagers`, where a homeless villager is a homeless family (`getNumHomelessFamilies`). Each tick SHALL be logged in the telemetry with day, order before, manor term, homeless count, homeless term and order after, and in one `HarnessLog` line.

#### Scenario: A tick with homeless villagers
- **WHEN** the order is 50 and 4 villagers are homeless
- **THEN** the tick gives 40 (50 + 10 - 20) and the telemetry record holds all six fields
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: The tick interval
- **WHEN** the game runs 65 game days
- **THEN** between 2 and 3 ticks ran
- Checked by `mod/InvasionMod/scenarios/bandits/order_tick.py`.

### Requirement: Low order starts a banditry timer
When the order drops below `threshold` (default 25), the mod SHALL start a timer of `timer_days` (default 90) game days. When the timer expires, villagers SHALL leave to become bandits. When the order is 25 or more before the timer expires, the timer SHALL reset. After the villagers leave, the timer SHALL restart if the order is still below 25.

#### Scenario: Timer start and expiry
- **WHEN** a tick leaves the order at 20
- **THEN** the timer starts, and the leave happens between 85 and 95 game days later if the order stays under 25
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: The timer resets
- **WHEN** the order rises to 25 or more before the timer expires
- **THEN** the timer stops and no villager leaves
- Checked by `harness/tests/test_bandits_rules.py`.

### Requirement: Leaving for banditry raises public order
When villagers leave for banditry, the mod SHALL add `order_gain` (default 25) to the mod order, kept at 100 or less.

#### Scenario: The order after the leave
- **WHEN** villagers leave and the order was 20
- **THEN** the order is 45 and the timer restarts only if the order is under 25
- Checked by `harness/tests/test_bandits_rules.py`.
