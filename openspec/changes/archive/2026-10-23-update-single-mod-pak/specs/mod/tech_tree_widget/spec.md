## MODIFIED Requirements
<!-- Issue: #471 -->

### Requirement: The menu needs the pak
The menu SHALL be a Widget Blueprint from the pak `InvasionMod_P.pak`. Without the pak the open call SHALL fail with a clear message and SHALL NOT crash the game.

#### Scenario: No pak loaded
- **WHEN** the menu is opened and the pak is not loaded
- **THEN** the answer has `ok` false and a message that names the pak
- Checked by `harness/tests/test_fakegame_tech_tree.py`.
