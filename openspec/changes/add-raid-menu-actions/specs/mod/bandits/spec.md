## ADDED Requirements
<!-- Issue: #340 -->

### Requirement: A mod menu has a button for the buy-back
A mod menu built on `core/menu.lua` SHALL show a buy-back button with the current price (see "The player can buy families back"). A click SHALL call the same function as `InvasionMod.bandits_buy_back`. The button SHALL be disabled, with the refusal reason as text, when the buy-back would be refused.

#### Scenario: A click buys families back
- **WHEN** families are outstanding, enough silver exists and the player clicks the button
- **THEN** the silver falls by the shown price and the families return
- Not checked yet (planned: a menu test scenario with picture evidence).

#### Scenario: A disabled button
- **WHEN** no family is outstanding
- **THEN** the button is disabled and shows the reason
- Checked by `harness/tests/test_fakegame_bandits.py` (planned).
