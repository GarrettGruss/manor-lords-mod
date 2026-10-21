## ADDED Requirements
<!-- Issue: #308 -->

### Requirement: Mod menus open from the game UI
The root of every mod menu SHALL open from the game UI with the mouse, in at most 2 clicks from the normal game view with no mod menu open. Opening a root menu SHALL NOT need a hotkey. A hotkey MAY stay as an extra shortcut. Submenus inside a root menu are exempt from the click limit.

#### Scenario: A root menu opens in at most 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open, and clicks the mod entry point in the game UI
- **THEN** each mod root menu is on screen after at most 2 clicks, and no key was pressed
- Not checked yet (planned: a test scenario per menu, with picture evidence).

#### Scenario: A submenu needs more clicks
- **WHEN** a root menu has a submenu that needs a third click, for example a branch in the tech menu
- **THEN** the rule is still met, because it covers only the root menu
- Not checked yet.

### Requirement: Each mod menu has a button in the game's bottom bar
Each mod root menu SHALL have its own button in the game's bottom bar, after the game's own buttons. One click on the button SHALL open its menu. The button SHALL match the format of the game's own bottom bar buttons: size, frame, icon or label style, and hover and pressed states. The player SHALL NOT be able to hide the buttons.

#### Scenario: The buttons sit after the game's buttons
- **WHEN** the player is in the normal game view
- **THEN** the bottom bar shows one button for each mod root menu, after the game's own buttons
- **AND** one click on a button opens its menu
- Not checked yet (planned: a test scenario per menu, with picture evidence).

#### Scenario: The buttons look like the game's buttons
- **WHEN** a picture of the bottom bar is taken
- **THEN** the mod buttons have the same size and frame as the game's buttons next to them
- Not checked yet (planned: picture evidence, reviewed by the owner).
