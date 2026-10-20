## MODIFIED Requirements
<!-- Issue: #315 -->

### Requirement: The autosave timer is pushed away before READY
HarnessBoot SHALL restart the pawn autosave timer with a period of one year through `MLGameInstance:SetAutosavePeriodOnPawn` before it reaches `READY`. It SHALL fail the boot if the timer is not pushed away. After `READY`, the harness SHALL push the timer away again after every world load in the same game session, and SHALL log an error if that push fails. The module `HarnessAutosave` SHALL NOT call a save function or the native `SetAutosavePeriod`.

#### Scenario: The timer is pushed away
- **WHEN** boot reaches the state `DISABLING_AUTOSAVE`
- **THEN** the timer period is 31536000 seconds and the stored setting stays unchanged
- Checked by `harness/tests/test_fakegame_harnessautosave.py`.

#### Scenario: The timer cannot be pushed away
- **WHEN** the timer still shows its old period after the call
- **THEN** the boot state is `FAILED` and the reason says the autosave timer was not pushed away
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: Autosave stays off in a real run
- **WHEN** a real run stays at `READY` for 60 game seconds
- **THEN** the autosave timer is still far away and the user save folder is unchanged
- Checked by `harness/scenarios/autosave_protection.py`.

#### Scenario: The timer is pushed away after a load
- **WHEN** a world is loaded after `READY` in the same game session
- **THEN** the autosave timer of the new player pawn is far away again, and the log has one push line for that load
- Checked by `harness/tests/test_fakegame_harnessautosave.py` and `harness/scenarios/autosave_after_load.py`.

#### Scenario: The push after a load fails
- **WHEN** the timer still shows the setting period after the push and its retries
- **THEN** the harness log has an error that says the autosave timer was not pushed away after a load
- Checked by `harness/tests/test_fakegame_harnessautosave.py`.
