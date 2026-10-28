# mod/tech_tree_widget Specification

## Purpose
The tech tree widget is the menu of the tech tree. It shows the tech picks, the paths, the nodes with their effects and laws, the laws in force and the last result, in the layout of the mockup `mockups/tech-tree-layout.html`, and takes the choices of the player.

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

### Requirement: The tree is drawn from the data
The menu SHALL show one button for each node of the tree data, path nodes and common techs together (at most 16), and hide the other buttons. It SHALL place each button at the card origin (`origin_x`, `origin_y`) plus the `layout` x (the order column) and y (the row) of the node times `step_x` and `step_y`. Row 0 holds the Oppression nodes, row 1 the Prosperity nodes and row 2 the common techs. It SHALL colour a button by status: unlocked, available, locked, other path or no free pick. An unlocked node has the mark "[x]". A tree with more than 16 nodes SHALL fail loudly when the menu opens.

#### Scenario: Buttons follow the nodes
- **WHEN** the menu is open with the shipped tree
- **THEN** 11 node buttons are visible (8 path nodes and 3 common techs)
- **AND** each stands at its layout position
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget.py` (U3 and U4).

#### Scenario: A common tech needs no path
- **WHEN** no path is chosen and the player has a free pick and clicks a common tech
- **THEN** the tech is unlocked with the mark "[x]"
- **AND** a click on a path node is refused with the reason "no path is chosen"
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_picks.py`.

#### Scenario: A click without a free pick
- **WHEN** the player has no free pick and clicks an available node
- **THEN** the click is refused with "no free pick", and the message shows in the footer
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_picks.py`.

### Requirement: Two path buttons until a path is chosen
The menu SHALL show a "Swear to this path" button in the row of each path while no path is chosen, and SHALL hide them after the choice. The row of the chosen path SHALL say "Sworn path" and the other row SHALL say "Closed". A click on a path button SHALL call the same function as the command `tech_tree_choose_path`.

#### Scenario: A press chooses a path
- **WHEN** the harness presses the path button of Prosperity through `InvasionMod.tech_tree_widget_press`
- **THEN** the path of the tech tree is Prosperity
- **AND** the path buttons are hidden, and the Prosperity row says "Sworn path"
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_laws.py`.

### Requirement: The menu lists the laws
Each node card whose tech opens a law SHALL show the law name. When the tech is unlocked, the card SHALL show an "Enact" button, or a "Repeal" button while the law is in force. The laws strip SHALL show "N of 2 max" (the `max_active_laws`) and one place for each allowed law, each with the name, the effects and a "Repeal" button, or an empty place. A click SHALL enact or repeal the law through the same functions as the commands. A refused click is logged, shown in `last_error` and shown in the footer.

#### Scenario: Presses enact, repeal and refuse
- **WHEN** the harness presses the law buttons through the command
- **THEN** the strip count and the button labels equal the tech tree state before and after each press
- **AND** a press on a law of a locked tech is refused, and a third enact is refused as a third law
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_laws.py`.

#### Scenario: Labels say what a click does
- **WHEN** a law is in force, open, closed only by the limit of laws, or its tech is not yet unlocked
- **THEN** its button says Repeal, says Enact, says Enact (a click is refused and the footer says why), or is hidden
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

### Requirement: The header shows the title and the tech picks
The menu SHALL show a header at the top with the title, the tech picks counter and a close button. The counter SHALL show the free picks and the picks used of the picks earned ("1 free (0 of 1 used)"), taken from the tech tree state of change `update-tech-tree-yearly-picks`. The menu SHALL NOT show the settlement level or a node slot count. The chosen path and the effects of the unlocked techs and laws SHALL show on the rows and the cards (see the layout requirement), not as header lines.

#### Scenario: The counter follows the picks
- **WHEN** the menu is open with 1 pick earned and no tech unlocked, and then a common tech is unlocked
- **THEN** the counter reads "1 free (0 of 1 used)", and then "0 free (1 of 1 used)"
- Checked by `harness/tests/test_fakegame_tech_tree.py` (the counter text) and `mod/InvasionMod/scenarios/tech_tree/widget.py` and `widget_picks.py` (the shown counter).

#### Scenario: A new spring raises the counter
- **WHEN** a new spring gives one pick while the menu is open
- **THEN** the counter shows one more free pick on the next refresh
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget.py` (U8) and `widget_picks.py` (P5).

### Requirement: The window follows the layout mockup
The tech tree window SHALL follow the layout of `openspec/specs/mod/tech_tree_widget/mockups/tech-tree-layout.html`: a header, column heads by order, one row for each path (Oppression above Prosperity) and a Common row below, node cards with links, a laws strip and a footer. The fonts, textures and exact sizes of the game MAY differ.

#### Scenario: The parts and their order
- **WHEN** the menu is open
- **THEN** from top to bottom: the header (title at the left, picks counter, close button at the right end); the column heads I to IV ("First tech" to "Fourth tech", not settlement levels); the rows; the laws strip; the footer
- **AND** each row has a label at its left edge (path name and status line, and "Swear to this path" while no path is chosen, not on the Common row)
- **AND** the cards stand in the order columns from left to right, a link joins each path node to the node it requires (lit when that node is unlocked), and the common techs have no links
- **AND** the footer has the last message at the left and "One tech pick each spring. The path you swear to is final." at the right
- Checked by: picture evidence (owner review), in `evidence/` of the change, made by `mod/InvasionMod/scenarios/tech_tree/widget_layout.py` (`ctx.screenshot`). The scenario also checks the text of the parts and the card positions.

#### Scenario: The rows and the cards
- **WHEN** the menu is open
- **THEN** the Oppression row is above the Prosperity row, and the Common row is below both
- **AND** a node card shows the name, the status, the numerical effects ("No standing effect" when none) and the law of the tech with its Enact or Repeal button ("No law" when none)
- Checked by: picture evidence (owner review), made by `mod/InvasionMod/scenarios/tech_tree/widget_layout.py`. The scenario also checks the rows, the cards and the law buttons.

#### Scenario: The states of the window
- **WHEN** screenshots are taken with no path chosen, with a path and two unlocked techs, and with two laws in force
- **THEN** each one matches the matching state of the mockup: the path buttons, the lit links and the two filled law places
- Checked by: picture evidence (owner review), made by `mod/InvasionMod/scenarios/tech_tree/widget_layout.py`.

### Requirement: The footer shows the last result
The footer SHALL show the message of the last click: the name of the tech or law and what happened, or the reason of a refusal ("no free pick", "no path is chosen", "2 of 2 laws are in force"). It SHALL also show the fixed text "One tech pick each spring. The path you swear to is final."

#### Scenario: A refusal shows in the footer
- **WHEN** the player clicks a tech with no free pick
- **THEN** the footer message names the tech and says "no free pick"
- Checked by `mod/InvasionMod/scenarios/tech_tree/widget_picks.py`.
