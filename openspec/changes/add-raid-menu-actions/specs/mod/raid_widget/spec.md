## ADDED Requirements
<!-- Issue: #340 -->

### Requirement: The raid menu has buttons for the terms
While a terms offer is open, the raid menu SHALL show a Pay button and a Fight button with the amounts of the offer. A click on Pay SHALL accept the payment terms through the same function as `InvasionMod.terms_accept`. A click on Fight SHALL decline the offer through the same function as `InvasionMod.terms_decline`. The buttons SHALL be hidden when no offer is open. The raid menu SHALL be built on the base menu `core/menu.lua`, and the buttons SHALL be content of that menu.

#### Scenario: The player pays
- **WHEN** an offer is open and the player clicks Pay with enough silver
- **THEN** the silver falls by the payment and the raid leaves with the reason `terms`
- Not checked yet (planned: a menu test scenario with picture evidence).

#### Scenario: The player fights
- **WHEN** an offer is open and the player clicks Fight
- **THEN** the offer closes, the silver does not change and the raid goes on
- Checked by `harness/tests/test_fakegame_raid_widget.py` (planned).

#### Scenario: No offer
- **WHEN** no offer is open
- **THEN** the raid menu shows no Pay and no Fight button
- Checked by `harness/tests/test_fakegame_raid_widget.py` (planned).

### Requirement: The raid menu has a button to start the raid
The raid menu SHALL show a Start raid button while a raid is planned and not spawned. A click SHALL spawn the planned raid at the next check through the same function as `InvasionMod.invasion_force_next`. The button SHALL be hidden when no raid is planned or the raid has spawned.

#### Scenario: The player starts the raid
- **WHEN** a raid is planned and the player clicks Start raid
- **THEN** the raid spawns at the next check and the button is hidden
- Not checked yet (planned: a menu test scenario with picture evidence).
