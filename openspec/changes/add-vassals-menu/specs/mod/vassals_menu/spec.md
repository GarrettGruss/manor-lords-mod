## ADDED Requirements
<!-- Issue: #564 -->

### Requirement: The Vassals menu opens from the bottom bar
The mod SHALL register the menu `vassals` with the label "Vassals". The player SHALL open it from the game's bottom bar with one click, with no hotkey. The only Close SHALL be the framework's bottom-centre Close. The menu SHALL be a pak widget in the game-menu style of the mockup `vassals-menu.html` (in `mockups/` of this change; after the archive, in `openspec/specs/mod/vassals_menu/mockups/`).

#### Scenario: Opens in one click
- **WHEN** the player is in the normal game view with no mod menu open
- **THEN** one click on the "Vassals" button of the bottom bar opens the menu, and Close closes it
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals_menu/window.py`).

#### Scenario: The style
- **WHEN** the menu is open
- **THEN** the style matches the mockup: near-black background, centred title, three cards, white serif text, gold numbers, no Close inside the widget
- Not checked yet (planned: picture evidence and `mod/InvasionMod/scenarios/vassals_menu/window.py`).

### Requirement: The header shows count, tribute and silver
The header SHALL show "Vassals: N / 3" (N is the number of registered vassals, the maximum is `vassals.max_vassals`), "Tribute each month: <goods>" and "Treasury: <n> silver". The tribute total SHALL sum, for each good, the monthly amount of every vassal that pays. A vassal that is `rebuilding` SHALL add nothing. The header SHALL update after a policy change or a restore while the menu is open.

#### Scenario: The header values
- **WHEN** two vassals with policies `fair` and `heavy` pay the same 2 goods
- **THEN** the count is 2 / 3, the tribute line shows 250 units of each of those goods, and the silver is the treasury value
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

#### Scenario: The header after a click
- **WHEN** the player sets a vassal to `light` while the menu is open
- **THEN** the tribute line shows the new total within 2 s of real time
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals_menu/window.py`).

### Requirement: Each card shows one vassal
The menu SHALL show 3 cards, one for each slot (`vassals.max_vassals`). A card for a registered vassal SHALL show the region, the lord, the status, the rich resources, the tribute each month, the families, the buildings, the days as vassal (from the handover), one note line and the policy buttons. The tribute SHALL be `tribute.base x policy factor` for each paid good, as the tribute tick computes it. A slot that was never claimed SHALL show a dim card "Free slot" with the text "Claim and settle a region to gain a vassal." and no buttons. Wiped villages SHALL fill the free cards, oldest first, and the cards SHALL stay in slot order. The days as vassal SHALL count from the handover, also after a restore. The rich resources SHALL show the names of the paid goods (a region with rich soil shows "flax"). A vassal that is registered but not yet handed over to a lord SHALL show the status "Claimed" and no tribute.

#### Scenario: A thriving vassal
- **WHEN** a handed-over vassal with policy `fair` is shown
- **THEN** the card shows its region, lord, the status "Thriving", 2 rich resources, a tribute of 100 for each of 2 goods, and the counts of families and buildings
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

#### Scenario: A rebuilding vassal
- **WHEN** a restored vassal has the flag `rebuilding`
- **THEN** the card shows the status "Rebuilding", the tribute "none", and a note that the tribute waits until the village is rebuilt (no progress numbers)
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

### Requirement: The status comes from the vassal state
The status SHALL be derived from existing state only. "Thriving" SHALL mean a handed-over vassal that is not `stalled` and not `rebuilding`. "Stalled" SHALL mean the flag `stalled`. "Rebuilding" SHALL mean the flag `rebuilding`. "Wiped" SHALL mean a record of a wiped region (a region outside the slots, see `mod/vassals`). The menu SHALL NOT add a new status or a new rule for a status.

#### Scenario: Status mapping
- **WHEN** vassals with each of the flags and a wiped record are shown in the fake game
- **THEN** the cards show Thriving, Stalled, Rebuilding and Wiped
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

### Requirement: The player sets the policy with three buttons
Each card of a registered vassal SHALL have the buttons Light, Fair and Heavy. The current policy SHALL look selected. A click SHALL call `InvasionMod.vassals_set_policy` for the slot. A hint line SHALL say what the policy pays, for example "Tribute x1: 100 of each rich resource" (x0.5: 50, x1.5: 150). A refused command SHALL leave the selection as it was and SHALL show the reason in the note line.

#### Scenario: A policy click
- **WHEN** the player clicks Heavy on a vassal with policy `fair`
- **THEN** the policy of that slot is `heavy`, the hint reads "Tribute x1.5: 150 of each rich resource", and the next tribute is 1.5 times the `fair` tribute
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals_menu/window.py` and `harness/tests/test_fakegame_vassals_menu.py`).

#### Scenario: A refused policy
- **WHEN** the command refuses the policy
- **THEN** the selection does not change and the note line shows the reason
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

### Requirement: A wiped village can be restored from its card
The card of a wiped village SHALL show the status "Wiped", "No lord", no policy buttons, and the button "Restore the village" with its cost as the hint "Costs 100 silver." (`vassals.restore.silver`, 100; the hint does not describe the effect). The button SHALL be disabled, with the hint in muted red, when the silver is lower. A click SHALL call the existing `InvasionMod.vassals_restore` with the region and nothing else, and SHALL show a refusal reason. Cost and effect stay as in `mod/vassals`.

#### Scenario: A restore click
- **WHEN** the player clicks "Restore the village" with at least 100 silver
- **THEN** the command runs once, the silver falls by 100, and the card shows the status "Rebuilding"
- Not checked yet (planned: `mod/InvasionMod/scenarios/vassals_menu/window.py` and `harness/tests/test_fakegame_vassals_menu.py`).

#### Scenario: Not enough silver
- **WHEN** the silver is lower than 100
- **THEN** the button is disabled and no command runs on a click
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

### Requirement: The menu reads state through the existing logic
The menu SHALL read the same data as `InvasionMod.vassals_state` and `InvasionMod.tribute_state`, and SHALL change state only through `vassals_set_policy` and `vassals_restore`. It SHALL NOT call a save function. The command `InvasionMod.vassals_menu_view` SHALL return the values that the widget shows. The menu SHALL refresh while open and SHALL NOT call a game function when closed.

#### Scenario: The view command
- **WHEN** a test sends `InvasionMod.vassals_menu_view`
- **THEN** the answer holds the header values and one card model for each slot
- Not checked yet (planned: `harness/tests/test_fakegame_vassals_menu.py`).

#### Scenario: No save call
- **WHEN** the repo is checked for save calls
- **THEN** the feature `vassals_menu` has none
- Checked by `harness/tests/test_save_call_sites.py`.
