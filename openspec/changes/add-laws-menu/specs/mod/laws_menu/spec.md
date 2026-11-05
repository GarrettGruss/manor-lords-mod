## ADDED Requirements

<!-- Issue: #563 -->

### Requirement: A Laws menu opens from the bottom bar
The mod SHALL register the menu `laws` with label "Laws" through `core/menu.lua`. A button on the bottom bar SHALL open and close it, like the other mod menus. The menu needs its pak widget `WBP_Laws` and SHALL show a clear message when the pak is missing.

#### Scenario: The menu opens and closes
- **WHEN** the harness opens the menu `laws` and then closes it
- **THEN** the menu state shows it open, then closed, and the bar has a "Laws" button
- Not checked yet. Planned: `mod/InvasionMod/scenarios/laws_menu/open_close.py`.

### Requirement: The header shows slots and the unlocked count
The header SHALL show "Laws in force N of S" (S = `max_active_laws` plus extra slots), the count of unlocked laws out of 9, and a filter All, Unlocked, Locked. The filter SHALL show only the cards of that status. A law in force counts as unlocked.

#### Scenario: Header values
- **WHEN** 1 law is in force, 3 laws are unlocked and no extra slot exists
- **THEN** the header shows "1 of 2" and "3 of 9 unlocked", and the filter Locked shows 6 cards
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: One card for each law
The menu SHALL show one card for each of the nine laws of `tree.json`. A card SHALL show the name, the status (In force, Unlocked or Locked), the line "Unlocked by" (the name of the tech tree node or common tech, or the contract source text), every effect with its value and a sign colour (a gain in green, a loss in red, a neutral effect in grey), and one button. A locked card SHALL say how to unlock the law (the node to unlock, and the path when it is a path law).

#### Scenario: Card content
- **WHEN** the law Conscription is in force
- **THEN** its card shows "Conscription", "In force", "Unlocked by Martial Law", the effects "Militia attack +10%" (green) and "Approval -5" (red), and a Revoke button
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: A locked law
- **WHEN** the node Martial Law is not unlocked
- **THEN** the card of Conscription has the status Locked and a line that says to unlock Martial Law on the Oppression path
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: Enact and Revoke act at once
An Enact button SHALL enact the law at once, and a Revoke button SHALL revoke it at once, through the tech tree functions. The effects SHALL start or stop with no delay. The Enact button SHALL be disabled with the text "All law slots are used. Revoke a law first." when all slots are used. A law of the other path SHALL show with the reason and no Enact button.

#### Scenario: Enact and revoke
- **WHEN** the player enacts an unlocked law and then revokes it
- **THEN** the law is in force with its effects after the first press, and is gone with its effects removed after the second
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py`.

#### Scenario: Slots are full
- **WHEN** 2 of 2 slots are used and a third law is unlocked
- **THEN** its Enact button is disabled with "All law slots are used. Revoke a law first."; after one revoke it is enabled
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: Contracts can unlock laws and add slots
The mod SHALL provide the function and the command `laws_unlock(id, source)` (`InvasionMod.laws_unlock`) and `laws_add_slot()` (`InvasionMod.laws_add_slot`). `laws_unlock` SHALL mark the law as unlocked with the `source` text, show that text in "Unlocked by", and refuse an unknown id. A second call for the same law SHALL change nothing. `laws_add_slot` SHALL add one slot and return the new slot total. The contracts change calls them.

#### Scenario: A contract unlocks a law
- **WHEN** `laws_unlock("curfew", "Contract: Night Watch")` runs before the tech Night Watch is unlocked
- **THEN** the Curfew card shows Unlocked and "Unlocked by Contract: Night Watch", the law can be enacted, and an unknown id is refused
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: An extra slot
- **WHEN** `laws_add_slot()` runs once
- **THEN** it returns 3, the header shows "of 3", and a third law can be enacted
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: The law state survives save and load
The laws in force keep the mod state key `tech_laws`. The mod SHALL save the contract unlocks and the extra slots in mod state (keys `laws_unlocked`, `laws_sources`, `law_extra_slots`). After a load, the menu SHALL show the same laws in force, the same unlocks and the same slots. A save without the new keys SHALL load with no extra slot and no contract unlock.

#### Scenario: Save and load
- **WHEN** a law is in force, one law is unlocked by a contract, one extra slot exists, and the game is saved and loaded
- **THEN** the menu state shows the same law in force, the same unlock with its source text, and "of 3"
- Not checked yet. Planned: `mod/InvasionMod/scenarios/laws_menu/roundtrip.py`.

### Requirement: The window follows the game-menu style
The menu SHALL use the font `/Game/UWG/fonts/CombinedFont_Mikadan`, a flat dark grey panel, and the layout of `mockups/laws-menu.html`. The only Close SHALL be the framework's bottom Close. The fonts and the exact sizes MAY differ from the mockup.

#### Scenario: Picture evidence
- **WHEN** screenshots are taken with no law in force, with two laws in force, and with the filter Locked
- **THEN** each matches the mockup layout, with the header, the cards and the bottom Close
- Not checked yet. Planned: picture evidence (owner review) made by `mod/InvasionMod/scenarios/laws_menu/layout.py`.

### Requirement: Named commands for the menu
The mod SHALL register `InvasionMod.laws_menu_state` (header, filter and cards) and `InvasionMod.laws_menu_press` (arguments `action`: filter, enact or revoke, and `id` or `filter`). The press command calls the click handlers without the mouse and needs an open menu.

#### Scenario: Press without the mouse
- **WHEN** the harness presses enact for a law, then the filter Locked
- **THEN** the state shows the law in force and only locked cards
- Not checked yet. Planned: `harness/tests/test_fakegame_laws_menu.py`.
