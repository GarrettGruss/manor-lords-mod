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
