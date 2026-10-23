## ADDED Requirements
<!-- Issue: #340 -->

### Requirement: The raid menu has a button for the buy-back
The raid menu (`mod/raid_widget`, built on `core/menu.lua`) SHALL show one buy-back button for the local bandits, with the current price (see "The player can buy families back"). A click SHALL call the same function as `InvasionMod.bandits_buy_back`. The raid menu keeps its other content and its difficulty buttons unchanged.

#### Scenario: A click buys families back
- **WHEN** families are outstanding, enough silver exists and the player clicks the button in the raid menu
- **THEN** the silver falls by the shown price and the families return
- Not checked yet (planned: a menu test scenario with picture evidence).

### Requirement: The buy-back button is disabled when the buy-back is refused
The button SHALL be disabled, with the refusal reason as text, when the buy-back would be refused. When no bandits are on the map, the button SHALL stay in the menu, disabled, and SHALL show that no bandits are present.

#### Scenario: Silver is too low
- **WHEN** families are outstanding and the silver is below the price
- **THEN** the button is disabled and shows the refusal reason, and a click changes nothing
- Checked by `harness/tests/test_fakegame_bandits.py` (planned).

#### Scenario: No bandits on the map
- **WHEN** no family is outstanding and no bandit unit is on the map
- **THEN** the button is disabled and shows that no bandits are present
- Checked by `harness/tests/test_fakegame_bandits.py` (planned).
