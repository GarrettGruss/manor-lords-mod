# mod/tech_tree_widget Specification

## Purpose
The tech tree widget is the menu of the tech tree. It shows the path, the node slots, the effects, the nodes and the laws, and takes the choices of the player.

## Requirements

### Requirement: F9 opens and closes the menu
The mod SHALL open the tech tree menu with the key F9 (config `tech_tree_widget.toggle_key`) and close it with the same key. The key callback SHALL only set a flag. The scheduler tick on the game thread SHALL do the toggle, so the game keeps answering.

#### Scenario: The real F9 key
- **WHEN** the player presses F9 three times and a fourth time
- **THEN** the menu opens, closes, opens and closes
- **AND** the bridge still answers after each press
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_key.py`.

### Requirement: The menu needs the pak
The menu SHALL be a Widget Blueprint from the pak `InvasionMod_P.pak`. Without the pak the open call SHALL fail with a clear message and SHALL NOT crash the game.

#### Scenario: No pak loaded
- **WHEN** the menu is opened and the pak is not loaded
- **THEN** the answer has `ok` false and a message that names the pak
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: Three header lines
The menu SHALL show three lines: the path ("Path: <name> (final)" or "Path: not chosen yet"), the free node slots with the settlement level, and the effects of the unlocked nodes and laws.

#### Scenario: The lines follow the tree
- **WHEN** the menu is open
- **THEN** the shown lines equal the lines wanted from the tech tree state
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget.py`.

#### Scenario: The wanted lines at the start and after a node
- **WHEN** no path is chosen, and then Oppression and Martial Law are chosen
- **THEN** the wanted lines are "Path: not chosen yet" with "Effects: none", then "Path: Oppression (final)" with "Effects: Public Order +10"
- Checked by `harness/tests/test_fakegame_tech_tree.py`.

### Requirement: The tree is drawn from the data
The menu SHALL show one button for each node of the tree data (at most 16) and hide the other buttons. It SHALL place each button at the `layout` x and y of the node times `step_x` and `step_y` (default 180 and 60 pixels). It SHALL colour a button by status: unlocked, available, locked or other path. An unlocked node has the mark "[x]". A tree with more than 16 nodes SHALL fail loudly when the menu opens.

#### Scenario: Buttons follow the nodes
- **WHEN** the menu is open with the shipped tree
- **THEN** 8 node buttons are visible
- **AND** each stands at its layout position
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget.py`.

### Requirement: Two path buttons until a path is chosen
The menu SHALL show a "Choose <path>" button for each path while no path is chosen, and SHALL hide them after the choice. A click on a path button SHALL call the same function as the command `tech_tree_choose_path`.

#### Scenario: A press chooses a path
- **WHEN** the harness presses the path button of Prosperity through `InvasionMod.tech_tree_widget_press`
- **THEN** the path of the tech tree is Prosperity
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_laws.py`.

### Requirement: The menu lists the laws
The menu SHALL show the line "Laws: N of 2 in force" (or "Laws: choose a path first") and up to 3 law buttons for the chosen path. A button says "Enact <law>", "[in force] <law> (repeal)" or "<law> (closed)". A click enacts or repeals the law through the same functions as the commands. A refused click is logged and shown in `last_error`.

#### Scenario: Presses enact, repeal and refuse
- **WHEN** the harness presses the law buttons through the command
- **THEN** the laws line and the labels equal the tech tree state before and after each press
- **AND** a press on a closed law is refused
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_laws.py`.

#### Scenario: Labels say what a click does
- **WHEN** a law is in force, open or closed
- **THEN** its label is the repeal, enact or closed text
- Checked by `harness/tests/test_fakegame_laws.py`.

### Requirement: Mouse clicks on the buttons
Each menu button SHALL be a click button of the shared module `HarnessClickHooks` inside a `Border` of the pak widget. A click SHALL be the `OnClicked` hook event of that button, not a polled press. The hook SHALL only queue the click, and the feature SHALL handle the queued clicks on its next scheduler tick. Each real click SHALL be handled exactly once.

#### Scenario: A real mouse click chooses a path and unlocks a node
- **WHEN** the player clicks a path button and then the first node button with the real mouse
- **THEN** the path is chosen and the node is unlocked with the mark "[x]"
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget.py`.

#### Scenario: Ten single clicks count ten times
- **WHEN** the player clicks one law button with the real mouse 10 times, one click each second
- **THEN** the click handler counts exactly 10 clicks
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_clicks.py`.

### Requirement: Named commands for the menu
The mod SHALL register `InvasionMod.tech_tree_widget_open`, `tech_tree_widget_close`, `tech_tree_widget_state` and `tech_tree_widget_press` (arguments `kind` path, node or law, and `index`). The press command calls the click handlers without the mouse and needs an open menu.

#### Scenario: Press without an open menu
- **WHEN** `tech_tree_widget_press` is called while the menu is closed
- **THEN** the call is refused with the message "the widget is not open"
- Checked by `harness/tests/test_fakegame_laws.py`.

### Requirement: A tooltip lists the numerical effects of a tech
Mouse over a node button or a law button of the tech tree menu SHALL show a tooltip. The tooltip SHALL list the numerical effects of the tech, each with its value. A percent effect SHALL show as a signed percent ("+10%"). A flat effect SHALL show as a signed number ("Public Order +10"). The tooltip MAY also show other information, for example a condition of an effect or a vassal policy that the node opens.

#### Scenario: A percent effect
- **WHEN** the mouse is over a tech with the effect militia attack 0.10
- **THEN** the tooltip has the line "Militia attack +10%"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A flat effect
- **WHEN** the mouse is over a tech with the effect public order 10
- **THEN** the tooltip has the line "Public Order +10"
- Checked by `harness/tests/test_fakegame_tech_tooltip.py`.

#### Scenario: A tech with several effects
- **WHEN** the mouse is over a tech with 2 or more numerical effects
- **THEN** the tooltip lists each of them with its value
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_tooltip.py` (the tooltip property) and by the picture evidence of the implementation pull request (the real hover, owner needed).
