## MODIFIED Requirements
<!-- Issue: #471 -->

### Requirement: A missing pak gives a clear message
If the widget class cannot be loaded, `raid_widget_open` SHALL return `ok = false` with a message that names the pak `InvasionMod_P.pak`, and SHALL NOT raise an error.

#### Scenario: The pak is not installed
- **WHEN** a test calls `raid_widget_open` without the pak
- **THEN** the answer has `ok = false` and a non-empty error text
- Checked by `harness/tests/test_fakegame_raid_widget.py`.
