# Spec Delta

## MODIFIED Requirements

<!-- Issue: #266 -->

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
