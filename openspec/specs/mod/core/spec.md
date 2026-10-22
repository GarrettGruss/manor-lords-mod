# mod/core Specification

## Purpose
The Invasion Mod is one Lua mod made of separate features. This capability covers the shared parts: the manifest, the feature loader, the feature list, the config and the scheduler.

## Requirements

### Requirement: Features load in dependency order
The mod SHALL load each enabled feature after the features it requires. The order of `feature_list.lua` breaks ties, and requirements load first.

#### Scenario: A feature that requires another
- **WHEN** feature `b` requires `a` and feature `c` requires `b`, and all three are enabled
- **THEN** the loader loads `a`, then `b`, then `c`
- **AND** each feature is loaded as the module `features.<name>.init`
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The loader fails loudly on a bad feature setup
The loader SHALL stop the load with a clear message on a cycle, a duplicate name, a requirement that is not in the list, an enabled feature that requires a disabled feature, a config table for an unknown feature, or a feature that fails to load. The message SHALL name the feature or the cycle.

#### Scenario: A cycle
- **WHEN** feature `a` requires `b` and `b` requires `a`
- **THEN** the load fails with a message that shows the cycle path
- Checked by `harness/tests/test_fakegame_featureloader.py`.

#### Scenario: A requirement is missing or disabled
- **WHEN** an enabled feature requires a feature that is not in the list, or that is disabled in `config.lua`
- **THEN** the load fails and the message names both features
- Checked by `harness/tests/test_fakegame_featureloader.py`.

#### Scenario: A feature raises an error while it loads
- **WHEN** the `init` module of a feature raises an error
- **THEN** the load stops at that feature and the message names the feature and its module path
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: A feature is on only when config enables it
The mod SHALL load a feature only when `config.lua` has a table for it with `enabled = true`. A feature with no config table SHALL count as disabled. A disabled feature SHALL NOT be loaded.

#### Scenario: A disabled feature
- **WHEN** `config.lua` sets `enabled = false` for a feature, or has no table for it
- **THEN** the loader does not load that feature
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The feature list equals the manifest
The mod SHALL keep `Scripts/feature_list.lua` equal to the `features` list in `mod.json`: the same names, in the same order, with the same `requires`.

#### Scenario: The two lists differ
- **WHEN** a feature is in one list and not in the other, or its `requires` differ
- **THEN** the fake game test fails
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: main.lua logs one ready line
The mod SHALL log one line `ready, features: <names>` with tag `InvasionMod` after all enabled features loaded. If the load fails, the mod SHALL log `load failed: <message>` and raise the error again. The mod SHALL NOT start half loaded.

#### Scenario: A normal start
- **WHEN** the game starts the mod with the default config
- **THEN** the log has one `ready, features:` line that lists the enabled features in load order
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: One scheduler timer runs all feature jobs
The mod SHALL run periodic feature work through `scheduler.every(name, every_ms, run)`. The scheduler SHALL use one `LoopAsync` timer with a tick of 100 ms and SHALL run due jobs on the game thread. A job that raises an error SHALL be logged with a stack trace and SHALL NOT stop the other jobs. The tick SHALL NOT be faster than 100 ms, because a 50 ms tick broke the Lua state after about 3 minutes with a menu open (spec 34).

#### Scenario: Two jobs, one fails
- **WHEN** two jobs are registered and one of them raises an error
- **THEN** the error is logged with its job name and the other job still runs at its interval
- Not checked yet.

#### Scenario: A menu stays open
- **WHEN** the tech tree menu stays open for 300 s while the mod state is read twice a second
- **THEN** the Lua state stays alive and the game keeps answering
- Not checked yet. Spec 34 recorded one passing run (`20261018-173614-d910`), but no committed test scenario repeats it.

### Requirement: Tunables live in config.lua
The mod SHALL keep every balance value and every on or off switch in `Scripts/config.lua`, in one table per feature that has the feature name as key and an `enabled` field. The test scenarios SHALL change tunables through named commands, not by editing feature logic.

#### Scenario: A config table without a feature
- **WHEN** `config.lua` has a table whose name is not in the feature list
- **THEN** the load fails with the message `unknown feature`
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The harness finds the mod through its manifest
The mod SHALL declare its name, `display_name`, version, shared modules, pak and features in `mod.json`. Harness code SHALL NOT contain the mod name, so the harness finds the mod only through `mod/<Name>/` paths and `mod.json`.

#### Scenario: Harness code names the mod
- **WHEN** any `.py`, `.lua` or `.ps1` file under `harness/` contains the mod name
- **THEN** the boundary test fails
- Checked by `harness/tests/test_boundary.py`.

### Requirement: Commands work without the harness
Each feature that offers named commands SHALL load `HarnessCommands` with `pcall`. The mod SHALL start and run when `HarnessCommands` is not installed.

#### Scenario: A player installs the mod without the harness
- **WHEN** the shared module `HarnessCommands` is missing
- **THEN** the features load and only the named commands are not registered
- Not checked yet.

### Requirement: Mod menus open from the game UI
The root of every mod menu SHALL open from the game UI with the mouse, in at most 2 clicks from the normal game view with no mod menu open. Opening a root menu SHALL NOT need a hotkey. A hotkey MAY stay as an extra shortcut. Submenus inside a root menu are exempt from the click limit.

#### Scenario: A root menu opens in at most 2 clicks
- **WHEN** the player is in the normal game view with no mod menu open, and clicks the mod entry point in the game UI
- **THEN** each mod root menu is on screen after at most 2 clicks, and no key was pressed
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (test scenario `menu-smoke`: one real click per menu, no key) and the pictures in `evidence/`.

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
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (the buttons are found in the bar by a real hover) and `evidence/bar-with-mod-buttons.jpg`.

#### Scenario: The buttons look like the game's buttons
- **WHEN** a picture of the bottom bar is taken
- **THEN** the mod buttons have the same size and frame as the game's buttons next to them
- Checked by picture evidence (`evidence/bar-with-mod-buttons.jpg`, `bar-button-hover.jpg`), reviewed by the owner. The label is a small text under the game's default icon.

### Requirement: Mod menus are fullscreen and block clicks to the game
Each mod menu SHALL cover the full screen, like the game's developments menu. While a mod menu is open, a mouse click SHALL NOT reach the game world or the game HUD behind the menu. A click on the menu SHALL act only on the menu, also a click on the empty background of the menu content. A mod menu SHALL have a Close button that the player can click with the mouse (a click on the backdrop does nothing).

#### Scenario: A click on the menu does not reach the world
- **WHEN** a mod menu is open over a burgage plot, and the player clicks a menu button at the place of the plot
- **THEN** the menu button acts
- **AND** the plot is not selected and no game panel opens
- Checked by `mod/InvasionMod/scenarios/menu/base.py` (test scenario `menu-base`) and `evidence/world-click-blocked-by-menu.jpg` with the control `world-click-control-no-menu.jpg`.

#### Scenario: A click on the menu background does not reach the world
- **WHEN** a mod menu is open over a building, and the player clicks the empty background of the menu content at the place of the building
- **THEN** no game panel opens
- Checked by `mod/InvasionMod/scenarios/menu/base.py` and `evidence/world-click-blocked-by-menu.jpg` (before the fix: `content-click-leaked-before-fix.jpg`).

#### Scenario: The Close button closes the menu
- **WHEN** a mod menu is open and the player clicks its Close button
- **THEN** the menu and its backdrop are gone
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py`.

#### Scenario: A menu covers the full screen
- **WHEN** a mod menu is open
- **THEN** it covers the full screen, like the developments menu
- Checked by picture evidence (`evidence/menu-raid.jpg`, `menu-tech.jpg`, `menu-liege-tribute.jpg`). The dimmed backdrop covers the full screen including the HUD; the menu content keeps the size and place of its pak layout.

### Requirement: Mod menus use one extensible base menu
Every mod menu SHALL be built on one shared base menu module in the Invasion Mod core (`core/menu.lua`). The base menu SHALL own the parts that are the same for every menu (open and close, fullscreen, click blocking, the bottom bar button). A menu SHALL extend the base menu only by its own parts: an id, a button label or icon, its content and its actions. A new menu SHALL need no change in the base menu.

#### Scenario: A new menu uses the base menu
- **WHEN** a feature registers a menu with an id, a label, content and actions
- **THEN** the menu gets a bottom bar button, opens fullscreen and blocks clicks to the game, with no menu code of its own for these parts
- Checked by `harness/tests/test_fakegame_menu.py`.

#### Scenario: No menu makes its own widget
- **WHEN** the feature code is searched for `AddToViewport` and `WidgetBlueprintLibrary`
- **THEN** only `core/menu.lua` calls them for a mod menu, so no menu makes its own widget or bottom bar button
- Checked by `harness/tests/test_menu_widget_sites.py`.

#### Scenario: One real run checks all menus
- **WHEN** the menu smoke test scenario runs in the real game
- **THEN** each registered menu opens from its button, and a picture is taken of each
- Checked by `mod/InvasionMod/scenarios/menu/smoke.py` (test scenario `menu-smoke`).
