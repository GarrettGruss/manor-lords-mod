## ADDED Requirements

<!-- Issue: #563 -->

### Requirement: A Laws menu opens from the bottom bar
The mod SHALL register the menu `laws` with label "Laws" through `core/menu.lua`. A button on the bottom bar SHALL open and close it, like the other mod menus. The menu needs its pak widget `WBP_Laws` and SHALL show a clear message when the pak is missing. The Esc key SHALL close an open confirmation dialog first; the menu stays open, and the next Esc closes it.

#### Scenario: The menu opens and closes
- **WHEN** the harness opens the menu `laws` and then closes it, once with the command and once with Esc
- **THEN** the menu state shows it open, then closed, and the bar has a "Laws" button
- Checked by `mod/InvasionMod/scenarios/laws_menu/open_close.py` and `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: Esc closes the dialog first
- **WHEN** a confirmation dialog is open and the Esc key is pressed
- **THEN** the dialog closes, nothing changes and the menu stays open
- Checked by `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py` and `harness/tests/test_fakegame_menu.py`.

### Requirement: The header shows slots, yearly actions and the unlocked count
The header SHALL show "Laws in force: N / S (max 5)" (S = the law slots, 1 base slot plus extra slots, at most 5), "Enact this year: N / 1", "Revoke this year: N / 1", the count of unlocked laws out of 9, the line "Enact and revoke actions refresh in spring, in N days.", and a filter All, Unlocked, Locked. A used counter SHALL show in red. The filter SHALL show only the cards of that status. A law in force counts as unlocked.

#### Scenario: Header values
- **WHEN** no law is in force and no law is unlocked
- **THEN** the header shows "0 / 1", "(max 5)", "1 / 1", "1 / 1" and "0 of 9"
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/open_close.py`.

#### Scenario: Filter
- **WHEN** 3 laws are unlocked and the filter Locked is chosen
- **THEN** 6 cards show; the filter Unlocked shows the 3 unlocked cards
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/layout.py`.

### Requirement: One card for each law
The menu SHALL show one card for each of the nine laws of `tree.json`. A card SHALL show the name, the status (In force, Unlocked or Locked), the line "Unlocked by: ..." (the tech tree node with its path, or the contract source text), every effect with its value and a sign colour (a gain in green, a loss in red, a neutral effect in grey), a hint line and one button. A locked card SHALL say how to unlock the law.

#### Scenario: Card content
- **WHEN** the law Conscription is in force
- **THEN** its card shows "Conscription", "In force", "Unlocked by: Tech tree: Oppression, Martial Law", the effects "Militia attack +10%" (green) and "Approval -5" (red), and a Revoke button
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: A locked law
- **WHEN** the node Martial Law is not unlocked
- **THEN** the card of Conscription has the status Locked and the hint "Unlock Martial Law on the Oppression path, or win it from a contract."
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: Enact and revoke use a yearly action and ask for a confirmation
The Laws menu SHALL be the place where the player enacts and revokes laws, through the tech tree functions. The player has 1 enact action and 1 revoke action for each game year. They SHALL come back at the start of spring (the clock of the tech picks) and SHALL be saved in mod state. A click on Enact or Revoke SHALL open a dialog with the title "Enact law" or "Revoke law", the question "Enact <name>?" or "Revoke <name>?", the effects of the law, the line "This uses your 1 enact action of this year. The law takes effect at once." (revoke: "This uses your 1 revoke action of this year. The effects end at once."), and the buttons Cancel and Enact or Revoke. Nothing SHALL change until the player confirms. Cancel and Esc SHALL close the dialog. A used action SHALL disable its buttons with "No enact action left this year." or "No revoke action left this year.". When all slots are used, Enact SHALL be disabled with "All law slots are used. Revoke a law first.". The yearly action is checked before the slots.

#### Scenario: Enact and revoke with a confirmation
- **WHEN** the player presses Enact on an unlocked law, sees the dialog, and confirms
- **THEN** nothing changed while the dialog was open, and after Confirm the law is in force with its effects and the enact action is used; Revoke works the same way with the revoke action
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py`.

#### Scenario: Cancel changes nothing
- **WHEN** the dialog is open and the player presses Cancel
- **THEN** the dialog closes, no law changed and no action is used
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py`.

#### Scenario: One enact and one revoke a year
- **WHEN** the player enacted a law this year and tries a second enact, or revoked a law and tries a second revoke
- **THEN** the button is disabled with the text of the used action, the press is refused, and nothing changes; the other action is still free
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py`.

#### Scenario: The actions refresh in spring
- **WHEN** both actions are used and the next spring starts
- **THEN** both are free again; the same spring refreshes only once, and a load gives no action back
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: Slots are full
- **WHEN** all slots are used and another law is unlocked
- **THEN** its Enact button is disabled with "All law slots are used. Revoke a law first."; after a revoke it is enabled
- Checked by `harness/tests/test_fakegame_laws_menu.py` and `mod/InvasionMod/scenarios/laws_menu/enact_revoke.py`.

#### Scenario: A save over the slot cap
- **WHEN** a save holds 2 laws in force and the base is 1 slot
- **THEN** both laws stay in force, the header shows "2 / 1", no new law can be enacted, and one revoke gives "1 / 1"
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: Contracts can unlock laws and add slots
The mod SHALL provide the function and the command `laws_unlock(id, source)` (`InvasionMod.laws_unlock`) and `laws_add_slot()` (`InvasionMod.laws_add_slot`). `laws_unlock` SHALL mark the law as unlocked with the `source` text, show that text in "Unlocked by", and refuse an unknown id. A second call for the same law SHALL change nothing. A law that a contract unlocked SHALL be enactable whatever the tech path and the tech nodes. `laws_add_slot` SHALL add one slot and return `slots` (the new total) and `added`. At 5 slots it SHALL change nothing and return `added` false with a `reason`. The contracts change calls them.

#### Scenario: A contract unlocks a law
- **WHEN** `laws_unlock("curfew", "Contract: Night Watch")` runs before the tech Night Watch is unlocked
- **THEN** the Curfew card shows Unlocked and "Unlocked by: Contract: Night Watch", the law can be enacted, and an unknown id is refused
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: A contract law ignores the path
- **WHEN** the path is Oppression and a contract unlocks Trade Pacts (Prosperity)
- **THEN** the player can enact it; the tech tree still refuses to unlock a node of the other path
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

#### Scenario: Extra slots and the cap
- **WHEN** `laws_add_slot()` runs 5 times
- **THEN** the results are 2, 3, 4, 5 and 5 slots, the fifth with `added` false and a reason
- Checked by `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: The law state survives save and load
The laws in force keep the mod state key `tech_laws`. The mod SHALL save the contract unlocks, their texts and the extra slots in mod state (keys `laws_unlocked`, `laws_sources`, `law_extra_slots`), and the yearly actions (keys `laws_year_no`, `laws_enact_used`, `laws_revoke_used`). After a load, the menu SHALL show the same laws in force, the same unlocks, the same slots and the same used actions. A save without the new keys SHALL load with no extra slot and no contract unlock.

#### Scenario: Save and load
- **WHEN** a law is in force, one law is unlocked by a contract, one extra slot exists, and the game is saved and loaded
- **THEN** the menu state shows the same law in force, the same unlock with its source text, "1 / 2" and the enact action still used
- Checked by `mod/InvasionMod/scenarios/laws_menu/roundtrip.py` and `harness/tests/test_fakegame_laws_menu.py`.

### Requirement: The window follows the game-menu style
The menu SHALL use the font `/Game/UWG/fonts/CombinedFont_Mikadan`, a flat dark grey panel, and the layout of `mockups/laws-menu.html`. The only Close SHALL be the framework's bottom Close. The fonts and the exact sizes MAY differ from the mockup.

#### Scenario: Picture evidence
- **WHEN** screenshots are taken with no law in force, with two laws in force, with the filter Locked, with full slots and with the dialog
- **THEN** each matches the mockup layout, with the header, the cards and the dialog
- Checked by picture evidence (owner review) made by `mod/InvasionMod/scenarios/laws_menu/layout.py` and `enact_revoke.py`.

### Requirement: Named commands for the menu
The mod SHALL register `InvasionMod.laws_menu_state` (header, filter, cards, dialog and the shown texts) and `InvasionMod.laws_menu_press` (arguments `action`: filter, enact, revoke, confirm or cancel, and `id` or `filter`). The press command calls the click handlers without the mouse and needs an open menu.

#### Scenario: Press without the mouse
- **WHEN** the harness presses enact for a law, then confirm, then the filter Locked
- **THEN** the state shows the law in force and only locked cards
- Checked by `harness/tests/test_fakegame_laws_menu.py`.
