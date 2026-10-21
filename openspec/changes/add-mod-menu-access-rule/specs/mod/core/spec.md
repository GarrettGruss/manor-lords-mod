## ADDED Requirements
<!-- Issue: #308 -->

### Requirement: Mod menus open from the game UI
The root of every mod menu SHALL open from the game UI with the mouse, in at most 2 clicks from the normal game view with no mod menu open. Opening a root menu SHALL NOT need a hotkey. A hotkey MAY stay as an extra shortcut. Submenus inside a root menu are exempt from the click limit.

#### Scenario: A root menu opens in at most 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open, and clicks the mod entry point in the game UI
- **THEN** each mod root menu is on screen after at most 2 clicks, and no key was pressed
- Not checked yet (planned: the base menu test scenario, with picture evidence).

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
- Not checked yet (planned: the base menu test scenario, with picture evidence).

#### Scenario: The buttons look like the game's buttons
- **WHEN** a picture of the bottom bar is taken
- **THEN** the mod buttons have the same size and frame as the game's buttons next to them
- Not checked yet (planned: picture evidence, reviewed by the owner).

### Requirement: Mod menus are fullscreen and block clicks to the game
Each mod menu SHALL cover the full screen, like the game's developments menu. While a mod menu is open, a mouse click SHALL NOT reach the game world or the game HUD behind the menu. A click on the menu SHALL act only on the menu.

#### Scenario: A click on the menu does not reach the world
- **WHEN** a mod menu is open over a burgage plot, and the player clicks a menu button at the place of the plot
- **THEN** the menu button acts
- **AND** the plot is not selected and no game panel opens
- Not checked yet (planned: the base menu test scenario, with picture evidence).

#### Scenario: A menu covers the full screen
- **WHEN** a mod menu is open
- **THEN** it covers the full screen, like the developments menu
- Not checked yet (planned: picture evidence).

### Requirement: Mod menus use one extensible base menu
Every mod menu SHALL be built on one shared base menu module in the Invasion Mod core (`core/menu.lua`). The base menu SHALL own the parts that are the same for every menu (open and close, fullscreen, click blocking, the bottom bar button). A menu SHALL extend the base menu only by its own parts: an id, a button label or icon, its content and its actions. A new menu SHALL need no change in the base menu.

#### Scenario: A new menu uses the base menu
- **WHEN** a feature registers a menu with an id, a label, content and actions
- **THEN** the menu gets a bottom bar button, opens fullscreen and blocks clicks to the game, with no menu code of its own for these parts
- Not checked yet (planned: fake game tests of `core/menu.lua`).

#### Scenario: No menu makes its own widget
- **WHEN** the feature code is searched for `AddToViewport` and `WidgetBlueprintLibrary`
- **THEN** only `core/menu.lua` calls them for a mod menu, so no menu makes its own widget or bottom bar button
- Not checked yet (planned: a Python test like `test_save_call_sites.py`).

#### Scenario: One real run checks all menus
- **WHEN** the menu smoke test scenario runs in the real game
- **THEN** each registered menu opens from its button, and a picture is taken of each
- Not checked yet (planned: one menu smoke test scenario for all menus).
