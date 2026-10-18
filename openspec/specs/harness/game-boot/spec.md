# harness/game-boot Specification

## Purpose
HarnessBoot takes the game from the main menu to a loaded, paused game and tells the launcher when it is ready. It also moves the game autosave timer away so a run cannot write into the real save folder.

## Requirements

### Requirement: Boot runs only when the harness asks
The mod `HarnessBoot` SHALL do nothing unless the environment variable `HARNESS_AUTOBOOT` is `1` or the file `ue4ss/harness/autoboot.enable` exists. This keeps normal play safe.

#### Scenario: Normal play
- **WHEN** the game starts with no switch set
- **THEN** HarnessBoot loads no save and pauses nothing
- Not checked yet.

### Requirement: Boot walks fixed states
HarnessBoot SHALL write `boot.json` atomically with its state and the history of state changes. For a save it SHALL walk `WAITING_FOR_MENU`, `LOADING_SAVE`, `WAITING_FOR_READY`, `DISABLING_AUTOSAVE`, `PAUSING` and `READY`. Any wait SHALL be able to end in `FAILED` with a reason.

#### Scenario: A save loads
- **WHEN** the menu appears and the wanted slot is in the save list
- **THEN** the state reaches `READY` and the file `ready.marker` is written once
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: The slot is missing
- **WHEN** the wanted slot is not in the save list, or its file does not exist
- **THEN** the state is `FAILED` and the reason says the slot did not appear or does not exist
- Checked by `harness/tests/boot_state_machine.py`.

### Requirement: READY means the clock stands still
HarnessBoot SHALL reach `READY` only after the game clock moved less than 0.001 game seconds for 8 seconds in a row. It SHALL not call `pauseGame` while the intro cinematic plays, and SHALL pause anyway after 25 seconds.

#### Scenario: The pause does not hold
- **WHEN** the clock keeps running after the pause calls
- **THEN** the state is `FAILED` and the reason says the clock did not stop
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: The clock never starts
- **WHEN** the clock does not start after the load
- **THEN** the state is `FAILED` and the reason says the clock never started
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: The game restarts its clock after our pause
- **WHEN** the game restarts the clock once after the first pause
- **THEN** HarnessBoot pauses again and still ends in `READY`
- Checked by `harness/tests/boot_state_machine.py`.

### Requirement: The loaded slot is checked
HarnessBoot SHALL load the slot named in `HARNESS_TEST_SAVE` through the menu and SHALL fail if the loaded slot is another one.

#### Scenario: Another slot loads
- **WHEN** the game loads a slot other than the wanted one
- **THEN** the state is `FAILED` and the reason says the wanted slot did not load
- Checked by `harness/tests/boot_state_machine.py`.

### Requirement: A new game can replace the load
When `HARNESS_NEW_GAME` is `1`, HarnessBoot SHALL open the map named by `HARNESS_NEW_GAME_MAP` (default `Jagged_Cliffs`) and load no save. It SHALL refuse a map name that is not allowed, and SHALL fail if a save was loaded.

#### Scenario: A fresh start
- **WHEN** the new game mode is on and the map opens
- **THEN** the state reaches `READY` with no `LoadGame` call
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: A bad map name
- **WHEN** the map name is not allowed
- **THEN** the state is `FAILED` and the reason says the map is not allowed
- Checked by `harness/tests/boot_state_machine.py`.

### Requirement: The autosave timer is pushed away before READY
HarnessBoot SHALL restart the pawn autosave timer with a period of one year through `MLGameInstance:SetAutosavePeriodOnPawn` before it reaches `READY`. It SHALL fail the boot if the timer is not pushed away. The module `HarnessAutosave` SHALL NOT call a save function or the native `SetAutosavePeriod`.

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
