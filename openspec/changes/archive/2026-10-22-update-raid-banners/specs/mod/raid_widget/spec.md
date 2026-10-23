## ADDED Requirements
<!-- Issue: #400 -->

### Requirement: The raid menu lists the upcoming raids
The raid menu SHALL list the upcoming raids all the time, not only on a banner. For the yearly (plunder) raid and the subjugation raid it SHALL show the type, the target (`you` or `your vassal <name>`), the size estimate and the days left, or `not planned yet`. The line of a raid type that is switched off (the subjugation raid off, or "Great raids" Off) SHALL be empty. The menu SHALL show no difficulty banner text.

#### Scenario: A planned raid is listed
- **WHEN** a subjugation raid is planned and the raid menu is open
- **THEN** its line shows the target, the size and the days left, and it updates when the days pass
- Checked by `harness/tests/test_fakegame_raid_widget.py` and `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

#### Scenario: A switched-off raid type is not listed
- **WHEN** "Great raids" is Off
- **THEN** the great raid line is empty
- Checked by `harness/tests/test_fakegame_scenario_settings.py`.
