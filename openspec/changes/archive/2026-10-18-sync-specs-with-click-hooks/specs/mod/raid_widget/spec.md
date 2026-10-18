# Spec Delta

## MODIFIED Requirements

<!-- Issue: #266 -->

### Requirement: A click on a difficulty button picks the difficulty
The menu SHALL show three difficulty buttons only while a pick is allowed: the difficulty is not picked and no raid has spawned. A click on button N SHALL pick difficulty N through the same function as `invasion_pick_difficulty`. A click SHALL be the `OnClicked` hook event of a click button of the shared module `HarnessClickHooks`; the hook only queues it, and the feature handles it on its next scheduler tick.

#### Scenario: The player clicks a button
- **WHEN** the player clicks a difficulty button with the mouse
- **THEN** the difficulty is picked and equals the value of the button
- **AND** the difficulty line shows `Difficulty: <value>`
- Checked by `mod/InvasionMod/scenarios/invasion/raid_widget.py`.

#### Scenario: A pick is made by command
- **WHEN** the difficulty is picked with the command
- **THEN** the wanted difficulty line is `Difficulty: 3` for a pick of 3
- Checked by `harness/tests/test_fakegame_raid_widget.py`.
