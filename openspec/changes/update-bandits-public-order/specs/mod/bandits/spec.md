## MODIFIED Requirements
<!-- Issue: #424 -->

### Requirement: A conversion removes two families and spawns a bandit squad
When the banditry timer expires, the mod SHALL remove `leavers` (default 18) villagers, as families, through `homeless_rebel` (`ManorCore.remove_families`), and SHALL spawn bandits for them only when the game's bandit pawn exists. Otherwise it SHALL log that no bandits spawned. The village SHALL keep at least `min_families_left` (default 1) families, so fewer than 18 may leave. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** the banditry timer expires (a test forces it) with enough villagers
- **THEN** the villagers that leave are between 1 and 18, and the village keeps at least 1 family
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the timer expires
- **THEN** no family leaves
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: No bandit pawn
- **WHEN** villagers leave and the game has no bandit pawn
- **THEN** no bandit spawns, the mod logs it, and no error is raised
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The conversion banner
- **WHEN** villagers leave for banditry
- **THEN** the banner `Families have turned to banditry` shows
- Not checked yet.

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
The mod SHALL offer `InvasionMod.bandits_state`, `bandits_tick_now`, `bandits_set_order` and `bandits_buy_back`. `bandits_tick_now` SHALL run one order tick at once. `bandits_state` SHALL return the mod order, the game order, the homeless count, the last tick, the timer (start day and days left), families, outstanding and returned families.

#### Scenario: A forced tick
- **WHEN** a test calls `bandits_tick_now`
- **THEN** the answer is the new state, and the last tick has day, order before, manor term, homeless count, homeless term and order after
- Checked by `mod/InvasionMod/scenarios/bandits/order_tick.py`.

## ADDED Requirements

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
Every `tick_days` (default 30) game days, the mod SHALL set `order = clamp(order + manor_term - homeless_term)`, with `manor_term = 10` (plus `order_bonus`) and `homeless_term = 5 x homeless villagers`. Each tick SHALL be logged in the telemetry with day, order before, manor term, homeless count, homeless term and order after, and in one `HarnessLog` line.

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

## REMOVED Requirements

### Requirement: Low approval lowers Public Order
**Reason**: The owner replaced the approval debuff with the mod order tick (2026-10-23). The debuff held the order at 0.
**Migration**: Use "The mod keeps its own public order" and "Public order ticks every 30 game days".

### Requirement: Conversion chance depends on Public Order
**Reason**: The order bands and the roll are replaced by the banditry timer.
**Migration**: Use "Low order starts a banditry timer".

### Requirement: The roll runs once per season change
**Reason**: The season-change roll is replaced by the 30 game day tick and the 90 game day timer.
**Migration**: Use "Public order ticks every 30 game days".

### Requirement: The player is warned about banditry
The mod SHALL show a banner (`core.show_banner`) at three moments: when the banditry timer starts, 30 game days before the villagers leave, and when they leave. The banners SHALL NOT repeat for the same timer.

#### Scenario: The timer starts
- **WHEN** a tick drops the order below 25 and the timer starts
- **THEN** one banner about growing unrest shows
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.

#### Scenario: The warning 30 game days before
- **WHEN** 30 game days (plus or minus 2) remain on the timer
- **THEN** one warning banner shows, once
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.

#### Scenario: The leave banner
- **WHEN** the villagers leave
- **THEN** one banner `Families have turned to banditry` shows
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_banners.py`.
