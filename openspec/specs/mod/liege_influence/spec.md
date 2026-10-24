# mod/liege_influence Specification

## Purpose
The player is sworn to an off-screen liege. This feature lets the player pay silver from the lord treasury as tribute to the liege and earn influence. It keeps the influence value in ModState across saves and gives a custom tribute menu, because the game has no liege of its own.

## Requirements

### Requirement: Influence is a saved value
The mod SHALL keep an influence value for the player in ModState. The value SHALL start at 0 on a new game. It SHALL come back after a save and a load. The command `InvasionMod.liege_state` SHALL show it. The value SHALL NOT decay over time and SHALL NOT have a cap.

#### Scenario: Influence survives a load
- **WHEN** the influence is above 0, the game is saved with the harness action `save_game`, and the slot is loaded
- **THEN** `liege_state` shows the same influence
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`.

#### Scenario: A new game
- **WHEN** a new game starts with the feature on
- **THEN** `liege_state` shows an influence of 0
- Checked by `mod/InvasionMod/scenarios/liege_influence/influence_roundtrip.py`.

#### Scenario: No decay
- **WHEN** the influence is above 0 and several game days pass without tribute
- **THEN** the influence is unchanged
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: No cap
- **WHEN** the player sends tribute many times so that the influence is above 1000
- **THEN** each tribute still raises the influence
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

### Requirement: Tribute is silver from the lord's treasury
The command `InvasionMod.liege_send_tribute` SHALL take the amount in silver from the lord's treasury. It SHALL NOT take goods and SHALL NOT take silver from the regional treasury. It SHALL raise the influence by the amount times `influence_per_unit`. A request that the lord's treasury cannot pay SHALL be refused with a message and SHALL not change the influence or the treasury.

#### Scenario: A paid tribute
- **WHEN** the lord's treasury holds enough silver and the player sends a tribute of 100 silver
- **THEN** the lord's treasury falls by 100
- **AND** the influence rises by 10
- Checked by `mod/InvasionMod/scenarios/liege_influence/send_tribute.py`.

#### Scenario: The ratio is configurable
- **WHEN** `influence_per_unit` is set to 0.2 in the config and the player sends 100 silver
- **THEN** the influence rises by 20
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: The regional treasury and goods stay unchanged
- **WHEN** the player sends a tribute
- **THEN** the regional treasury and the stock of goods are unchanged
- Checked by `mod/InvasionMod/scenarios/liege_influence/send_tribute.py`.

#### Scenario: A tribute the player cannot pay
- **WHEN** the player sends more silver than the lord's treasury holds
- **THEN** the command is refused with a message
- **AND** the influence and the lord's treasury are unchanged
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

### Requirement: The tribute ratio is configurable
The value `influence_per_unit` SHALL be set in the feature `config.lua`. Its default SHALL be 0.1 (10 tribute gives 1 influence).

#### Scenario: The default ratio
- **WHEN** the config is not changed and the player sends 10 silver
- **THEN** the influence rises by 1
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

### Requirement: The command name
The tribute action SHALL be available as the named command `InvasionMod.liege_send_tribute`. The menu SHALL call the same code as the command. Tests SHALL use the command.

#### Scenario: Command and menu give the same result
- **WHEN** the same amount is sent once by the command and once by the menu
- **THEN** the treasury and the influence change by the same values
- Checked by `mod/InvasionMod/scenarios/liege_influence/send_tribute.py`.

### Requirement: Tribute menu
The mod SHALL provide a pak widget menu in which the player sends silver to the liege. The menu SHALL show the influence and the silver of the lord's treasury. The menu SHALL update both values after a tribute. The player SHALL open the root of the menu from the game UI with the mouse, in at most 2 clicks. Opening it SHALL NOT need a hotkey. The rule covers only the root menu, not the submenus inside it.

#### Scenario: Sending tribute in the menu
- **WHEN** the player opens the menu and sends a tribute
- **THEN** the lord's treasury falls, the influence rises, and the menu shows the new values
- Checked by `mod/InvasionMod/scenarios/liege_influence/tribute_menu.py`.

#### Scenario: The menu is visible
- **WHEN** the menu is open in the game
- **THEN** a screenshot shows the menu with the influence and the silver values
- Checked by picture evidence in `openspec/changes/add-liege-influence/evidence/`.

#### Scenario: The menu opens in at most 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open
- **THEN** the player opens the tribute menu with at most 2 clicks on game UI elements, and no key press
- Checked by `mod/InvasionMod/scenarios/liege_influence/tribute_menu.py`.

### Requirement: One tribute button
The tribute menu SHALL have one tribute button. A click SHALL send `tribute_button_amount` silver (default 200) through the tribute command. The influence SHALL show in the same menu.

#### Scenario: One click on the tribute button
- **WHEN** the lord's treasury has at least 200 silver and the player clicks the tribute button once
- **THEN** the lord's treasury falls by 200 and the influence rises by 20
- Checked by `mod/InvasionMod/scenarios/liege_influence/tribute_menu.py`.

### Requirement: The liege screen has a button to request an arms shipment
The liege screen SHALL have a button "Request arms shipment". A click SHALL cost 200 silver and SHALL deliver 30 large shields and 30 spears to the manor store at once. The amounts and the cost SHALL come from config values. The mod SHALL take the silver only when the delivery succeeded.

#### Scenario: Buy a shipment
- **WHEN** the player has 200 or more silver, no cooldown runs, and the player clicks the button
- **THEN** the manor store holds 30 more large shields and 30 more spears
- **AND** the silver is 200 lower
- **AND** the button is disabled and shows the days left
- Checked by `mod/InvasionMod/scenarios/liege_influence/arms_shipment.py` and `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: A failed delivery costs nothing
- **WHEN** the delivery to the manor store fails
- **THEN** the silver and the cooldown day do not change and a log line says why
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

### Requirement: The arms shipment has a cooldown
After a shipment the button SHALL be disabled for 180 game days (a config value). The button SHALL also be disabled, with the reason shown, when the silver is below 200. While it is disabled for the cooldown, it SHALL show the days left. The mod SHALL store the day of the last shipment in the mod state, so the cooldown is kept over a save and load.

#### Scenario: Not enough silver
- **WHEN** the player has less than 200 silver
- **THEN** the button is disabled and the reason names the missing silver
- **AND** a click delivers nothing and takes no silver
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: Cooldown
- **WHEN** a shipment came 100 game days ago
- **THEN** the button is disabled and shows 80 days left
- **AND** after 180 game days it is enabled again if the silver is enough
- Checked by `harness/tests/test_fakegame_liege_influence.py`.

#### Scenario: The cooldown is saved
- **WHEN** a shipment was bought, the game is saved and loads in a new run
- **THEN** the cooldown day is the same and the button shows the days left
- Checked by `harness/tests/test_fakegame_liege_influence.py` (the mod state entry `arms_last_day`). A real save and load is not run (needs the guarded `save_game`).
