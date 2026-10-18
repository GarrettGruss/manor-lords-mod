# Spec Delta

## Purpose

The bandits feature turns low approval into low Public Order, and low Public Order into bandits. The player fights the bandits or pays silver to bring the families back.

## ADDED Requirements

### Requirement: Low approval lowers Public Order
The mod SHALL write `Region.publicOrder = natural - debuff` for the home region, with `debuff = ceil((100 - approval) x difficulty)` and the result kept between 0 and 100. The natural order is the value the game itself writes. The mod SHALL take a value that differs from its last write as the new natural value, so the debuff never stacks. At approval 100 the order SHALL equal the natural order. The difficulty is the one picked in the invasion feature.

#### Scenario: Approval 71 at difficulty 1
- **WHEN** the approval is about 71 at difficulty 1
- **THEN** the order read after 2 game days is the natural order minus 29, within plus or minus 5
- **AND** after 5 more game days the order is within 10 of that value, is 0 or more, and did not stack
- Checked by `mod/InvasionMod/scenarios/bandits/order_debuff.py`.

#### Scenario: Approval 100 and difficulty 2
- **WHEN** the approval is set to 100, and later the difficulty is 2 with a low approval
- **THEN** the order equals the natural order at once at approval 100
- **AND** at difficulty 2 the debuff doubles and the order is 0 or more
- Checked by `mod/InvasionMod/scenarios/bandits/order_debuff.py`.

#### Scenario: The picked difficulty is used
- **WHEN** the player picks difficulty 2 or 3
- **THEN** `bandits_state` reports the picked difficulty
- Checked by `mod/InvasionMod/scenarios/invasion/difficulty_pick.py`.

#### Scenario: The game rewrites the order
- **WHEN** the game writes its own Public Order after the mod wrote
- **THEN** the mod takes the game value as natural and writes `natural - debuff` again
- Checked by `harness/tests/test_fakegame_bandits.py`.

### Requirement: Conversion chance depends on Public Order
At each roll the mod SHALL use the chance of the lowest matching band of `bands` (default: below 75 is 10 percent, below 50 is 25 percent, below 25 is 50 percent). At Public Order 75 or above the chance SHALL be 0. A roll under the chance SHALL convert families.

#### Scenario: The band rates
- **WHEN** 20000 rolls are made at Public Order 80, 60, 40 and 10
- **THEN** the conversion rate is 0 and within 0.015 of 0.10, 0.25 and 0.50
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: Forced rolls
- **WHEN** Public Order is 80 or more and the roll is 0, or Public Order is under 25 and the roll is 0.99
- **THEN** no family is removed and no bandit appears
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.

### Requirement: A conversion removes two families and spawns a bandit squad
A successful roll SHALL remove `families_per_conversion` (default 2) families through `homeless_rebel` and SHALL spawn one Brigands squad of 18 units for each `families_per_squad` (default 2) families. The village SHALL keep at least `min_families_left` (default 1) families. The mod SHALL show the banner `Families have turned to banditry`.

#### Scenario: A forced conversion
- **WHEN** Public Order is under 25 and the roll is 0
- **THEN** 2 families are removed and 18 bandit units appear
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.

#### Scenario: The last family stays
- **WHEN** the village has only 1 family and the roll wins
- **THEN** no family is converted
- Checked by `harness/tests/test_fakegame_bandits.py`.

#### Scenario: The conversion banner
- **WHEN** a conversion succeeds
- **THEN** the banner `Families have turned to banditry` shows
- Not checked yet.

### Requirement: The roll runs once per season change
The mod SHALL make one roll for the home region at each season change. It SHALL NOT roll on the first poll, and SHALL NOT roll again in the same season. The last season SHALL be kept in ModState, so a load in the same season does not roll.

#### Scenario: Three season changes
- **WHEN** the game crosses three season changes
- **THEN** `rolls` grows by exactly 1 for each change and stays 0 before the first change and during 3 game days in one season
- **AND** the game runs 10 more game days with no crash
- Checked by `mod/InvasionMod/scenarios/bandits/season_tick.py`.

#### Scenario: A reload in the same season
- **WHEN** the feature loads again with the saved season equal to the current season
- **THEN** no roll is made
- Checked by `harness/tests/test_fakegame_bandits.py`.

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
The mod SHALL accept the modifiers `order_bonus` (added to the natural order), `approval_bonus` (added to approval for the debuff, up to 100) and `buy_back_multiplier` (a factor on the price) from the tech tree, and SHALL apply them at once.

#### Scenario: Price multipliers
- **WHEN** the multiplier is 1.25 or 0.5
- **THEN** the price is 13 or 5 for 1 family, and 25 or 10 for 2 families
- Checked by `harness/tests/test_bandits_rules.py`.

### Requirement: Named commands show and drive the feature
The mod SHALL offer `InvasionMod.bandits_state`, `bandits_set_approval`, `bandits_tick_now` and `bandits_buy_back`. `bandits_tick_now` SHALL accept an optional roll from 0 to 1. `bandits_state` SHALL return the order, natural order, approval, debuff, families, outstanding and returned families, rolls and the last ticks.

#### Scenario: A forced tick
- **WHEN** a test calls `bandits_tick_now` with a roll
- **THEN** the answer is the new state, and the tick used that roll
- Checked by `mod/InvasionMod/scenarios/bandits/convert_families.py`.
