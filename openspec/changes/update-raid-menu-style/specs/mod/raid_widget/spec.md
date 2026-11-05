## ADDED Requirements
<!-- Issue: #562 -->

### Requirement: The menu follows the approved look
The raid menu SHALL follow the game-menu style of the mockup `raid-menu-game-style.html` (in `openspec/changes/update-raid-menu-style/mockups/`; after the archive, in `openspec/specs/mod/raid_widget/mockups/`). All text SHALL use the game font `/Game/UWG/fonts/CombinedFont_Mikadan`. The layout is: a near-black background, a flat dark grey panel, a centred title "RAIDS" in capitals with a thin gold rule, and the five raid lines as rows. Each row has a diamond marker, a label, a value and a thin separator. The accent colour is gold #e8c87a, used for the values. The only Close SHALL be the framework's game-style bottom Close: the widget SHALL NOT have a close bar or button of its own. A line that is empty (a switched-off raid type) SHALL show no row. If the font or the widget class cannot be loaded, the mod SHALL log a clear message and SHALL NOT raise an error. The content and the behavior of the menu do not change.

#### Scenario: The look matches the mockup
- **WHEN** the menu is open with a planned raid
- **THEN** a screenshot shows the game font, the dark grey panel, the title with the gold rule, and the rows with diamond marker, label, gold value and separator, in the mockup style
- **AND** only one Close shows, the framework's bottom Close
- Checked by review of the picture evidence (`ctx.screenshot`) in `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

#### Scenario: A switched-off raid type shows no row
- **WHEN** "Great raids" is Off and the menu is open
- **THEN** the great raid row is not visible, and the other rows keep their order
- Checked by `harness/tests/test_fakegame_raid_widget.py` (the row is collapsed) and picture evidence.

#### Scenario: The state keeps the full lines
- **WHEN** a test calls `raid_widget_state` with the menu open
- **THEN** the shown lines and the wanted lines are the full texts, for example `Next raid: in 12 days`, as before the restyle
- Checked by `harness/tests/test_fakegame_raid_widget.py`.
