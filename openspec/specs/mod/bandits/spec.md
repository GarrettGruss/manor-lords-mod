# mod/bandits Specification

## Purpose
The bandits feature turns low approval into low Public Order, and low Public Order into bandits. The player fights the bandits or pays silver to bring the families back.

## Requirements

### Requirement: A rebellion removes families and spawns an Outlaws raid
When the banditry timer expires and the rebellion is not blocked (see the selection requirement), the mod SHALL take the goods of the chosen families (see the goods requirement), SHALL remove `rebellion_families` (default 6) families (`ManorCore.remove_families`: `just_die`, bodies hidden, never `K2_DestroyActor`) and SHALL spawn `rebellion_squads` (default 1, one squad is 18 units) squads of the template Brigands for the bandit pawn "Outlaws" at the home of the first removed family (`HarnessBandits.homeless_rebel`, mode `home`, `spawnArmy`). The mod SHALL NOT call `spawnBanditCamp` for a leave event. It SHALL call `ensure_outlaw_pawn()` first (see the Outlaws init requirement). The native Outlaws AI SHALL do the raid: it burns buildings, logs "enough looted" and leaves the map. The mod does not steer it. The village SHALL keep at least `min_families_left` (default 1) families. A villager here is a family. The mod SHALL show the banner `Families have turned to banditry`. If the spawn fails after the removal, the mod SHALL return the goods to the homes they came from and log an error.

#### Scenario: A forced conversion
- **WHEN** the banditry timer expires (a test forces it) with at least 6 valid families
- **THEN** 6 families leave, and the village keeps at least 1 family
- **AND** the bandit squad spawns within 500 units of a removed home
- **AND** within 400 game seconds at least 1 building burns and the AI logs "enough looted"
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`.

#### Scenario: The last family stays
- **WHEN** the village keeps only `min_families_left` families after the pick and the timer expires
- **THEN** the families above that minimum leave, and the village keeps at least 1 family
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: One squad for every 5 families
- **WHEN** the rebellion happens (defaults: 6 families, 1 squad of 18 units; the config may set other values)
- **THEN** that many families leave and that many squads spawn at the first removed home
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The spawn fails after the removal
- **WHEN** the squad spawn fails after the goods were taken
- **THEN** the goods return to the homes they came from and an error is logged
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: No bandit pawn
- **WHEN** families leave and the game has no Outlaws pawn
- **THEN** `ensure_outlaw_pawn()` creates the pawn first (camp removed), and then the squads spawn at the home
- Checked by `harness/tests/test_fakegame_bandits.py` and `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`.

#### Scenario: No camp call for a leave event
- **WHEN** families leave and the Outlaws pawn exists
- **THEN** `spawnBanditCamp` is not called
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Repeat rebellion
- **WHEN** a second rebellion happens after the first squads raided
- **THEN** the new squad spawns at the new home and raids, or logs "enough looted", with no crash
- Not checked yet.

#### Scenario: Plunder by Outlaws squads
- **WHEN** an Outlaws squad raids
- **THEN** the result records whether goods are looted
- Checked by `mod/InvasionMod/scenarios/bandits/rebellion_raid.py` (metric `stock_change`: the stock fell about 110 to 120 goods; burning also destroys goods, so the metric records but cannot split looting from burning).

#### Scenario: Removal at the map edge
- **WHEN** the squads leave the map after "enough looted"
- **THEN** the bandit units fall to the camp units, or the result records that they stay
- Checked by `mod/InvasionMod/scenarios/bandits/rebellion_raid.py` (metric `bandit_units_after_leave`: the 18 units stay on the map).

#### Scenario: The conversion banner
- **WHEN** families leave for banditry
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
When the order drops below `threshold` (default 25), the mod SHALL start a timer of `timer_days` (default 60) game days. When the timer expires, the rebellion SHALL start. When the order is `threshold` or more before the timer expires, the timer SHALL reset. After the rebellion, the order rises by `order_gain` (default 25), and the timer SHALL restart if the order is still below `threshold`. The values `threshold`, `timer_days`, `order_gain` and `tick_days` (default 30) are config values of the feature.

#### Scenario: Timer start and expiry
- **WHEN** a tick leaves the order at 20
- **THEN** the timer starts, and the rebellion happens between 55 and 65 game days later if the order stays under 25
- Checked by `mod/InvasionMod/scenarios/bandits/banditry_timer.py`.

#### Scenario: The timer resets
- **WHEN** the order rises to 25 or more before the timer expires
- **THEN** the timer stops and no family leaves
- Checked by `harness/tests/test_bandits_rules.py`.

#### Scenario: Config values
- **WHEN** the config sets `threshold`, `timer_days`, `order_gain` or `tick_days`
- **THEN** the rules use those values
- Checked by `harness/tests/test_bandits_rules.py`.

### Requirement: Leaving for banditry raises public order
When villagers leave for banditry, the mod SHALL add `order_gain` (default 25) to the mod order, kept at 100 or less.

#### Scenario: The order after the leave
- **WHEN** villagers leave and the order was 20
- **THEN** the order is 45 and the timer restarts only if the order is under 25
- Checked by `harness/tests/test_bandits_rules.py`.

### Requirement: Only armed families can rebel
A valid family is a family whose home holds at least one weapon or armor item: an id in `rebellion_weapon_ids` (config, default list in `design.md`). The mod SHALL pick `rebellion_families` (default 6) valid families AT RANDOM, not the best armed. If fewer valid families exist, NO rebellion SHALL happen: no family leaves, no squad spawns and the mod removes no good. The timer stays expired, the mod SHALL retry on the next tick and log `rebellion_blocked`.

#### Scenario: Enough valid families
- **WHEN** the timer expires and 9 families hold weapons or armor
- **THEN** 6 of the 9 leave, chosen at random
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Too few valid families
- **WHEN** the timer expires and only 5 families hold weapons or armor
- **THEN** no family leaves, no squad spawns, no good is removed, the timer stays expired, the event `rebellion_blocked` is logged, and the next tick checks again
- Checked by `harness/tests/test_fakegame_bandits.py` and `mod/InvasionMod/scenarios/bandits/rebellion_raid.py`.

#### Scenario: An unarmed village never rebels
- **WHEN** no home holds an id of `rebellion_weapon_ids`
- **THEN** the rebellion is blocked on every tick
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Weapons arrive after a blocked tick
- **WHEN** homes get weapons after a blocked tick and 6 valid families exist
- **THEN** the next tick starts the rebellion
- Checked by `harness/tests/test_fakegame_bandits.py`.

### Requirement: The rebels take the goods of their homes
The mod SHALL take ALL weapon and armor goods (ids in `rebellion_weapon_ids`) from the homes of the chosen families (`consumeGoodNoCheck`, one call per item), and SHALL set them as loot overrides (requirement "A loot override replaces the loot of a unit" of `mod/raid_behavior`) on the spawned brigands, spread over the 18 units. The mod SHALL NOT re-apply gear with `SMUnit:equip` and SHALL take nothing from other homes.

#### Scenario: Goods of the chosen homes only
- **WHEN** 6 of 9 valid families are chosen
- **THEN** all weapon and armor goods of those 6 homes are removed and the other 3 homes keep theirs
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Goods spread over the brigands
- **WHEN** a rebellion spawns 18 brigands after the removal of 30 goods
- **THEN** all 30 goods are in overrides of the 18 brigands, and no good is in two overrides
- Checked by `harness/tests/test_fakegame_bandits.py`.

### Requirement: The Outlaws pawn comes from an init module
A separate module SHALL provide an idempotent `ensure_outlaw_pawn()`. If the Outlaws pawn exists, it SHALL do nothing. Otherwise it SHALL create the pawn with `spawnBanditCamp()` and remove the camp (steps in `design.md`). The game picks the camp place: the mod cannot select a region. The mod SHALL call it at game start, after each load and before each rebellion. A rebellion SHALL NOT start when it fails.

#### Scenario: The pawn exists
- **WHEN** `ensure_outlaw_pawn()` runs and the Outlaws pawn exists
- **THEN** it calls nothing and returns true
- Checked by `harness/tests/test_fakegame_outlaws.py`.

#### Scenario: The pawn is missing
- **WHEN** `ensure_outlaw_pawn()` runs and no Outlaws pawn exists
- **THEN** the pawn exists at once, and a second call does nothing
- **AND** once the camp is built, its 18 brigands are killed and hidden and the camp is demolished (a camp is built by its brigands, so they must not die before it is built)
- Checked by `harness/tests/test_fakegame_outlaws.py` and `mod/InvasionMod/scenarios/bandits/outlaws_init.py`.

#### Scenario: The guard before a rebellion
- **WHEN** the timer expires and the pawn is missing
- **THEN** the mod creates the pawn first, and then selects the families
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The pawn survives a load
- **WHEN** the camp was removed, the game is saved and loaded
- **THEN** the pawn exists, or `ensure_outlaw_pawn()` makes it again
- Checked by `mod/InvasionMod/scenarios/bandits/rebellion_loot_roundtrip.py` (fixture `playtest-noai`, write run and read run).

### Requirement: Rallied militia weapons still count
Weapons that sit on rallied militia men SHALL NOT make the village unarmed: a rally SHALL NOT dodge the rebellion. Rally and disband cannot be driven from Lua, and the weapons stay in the homes in the spike, so the family stays valid. Killing registered militia returns their home weapons to the storehouse, which the mod does not read.

#### Scenario: A rally does not dodge the rebellion
- **WHEN** the player rallies militia and the timer expires
- **THEN** the families with weapons in their homes are still valid and the rebellion is not blocked by the rally
- Manual: owner playtest. Task 2.11.
