## MODIFIED Requirements
<!-- Issue: #295 -->

### Requirement: Boot walks fixed states
HarnessBoot SHALL write `boot.json` atomically with its state and the history of state changes. For a save it SHALL walk `WAITING_FOR_MENU`, `LOADING_SAVE`, `WAITING_FOR_READY`, `DISABLING_AUTOSAVE`, `PAUSING` and `READY`. Any wait SHALL be able to end in `FAILED` with a reason.

#### Scenario: A save loads
- **WHEN** the menu appears and the wanted slot is in the save list
- **THEN** the state reaches `READY` and the file `ready.marker` is written once
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: The slot appears late
- **WHEN** the save list fills slowly and the wanted slot appears after other slots
- **THEN** the state still reaches `READY`
- Checked by `harness/tests/boot_state_machine.py` (mode `slotlate`).

#### Scenario: The slot is missing
- **WHEN** the wanted slot is not in the save list, or its file does not exist
- **THEN** the state is `FAILED` and the reason says the slot did not appear or does not exist
- Checked by `harness/tests/boot_state_machine.py`.

#### Scenario: A real boot walks the states in order
- **WHEN** a real run boots from a save
- **THEN** the `boot.json` history holds the six states in the fixed order, each once, and ends in `READY`
- Checked by `harness/scenarios/boot_timing.py`.

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

#### Scenario: The intro cinematic plays
- **WHEN** the intro cinematic ends after the clock started
- **THEN** `pauseGame` is called once, after the cinematic, and the state reaches `READY`
- Checked by `harness/tests/boot_state_machine.py` (mode `cinematic`).

#### Scenario: The intro cinematic never ends
- **WHEN** the cinematic is still playing after the wait limit
- **THEN** `pauseGame` is called anyway and the state reaches `READY`
- Checked by `harness/tests/boot_state_machine.py` (mode `cinematicstuck`).

## ADDED Requirements

### Requirement: Boot timing is checked in the real game
The harness SHALL have a real-game test scenario that checks boot timing after `READY`. It SHALL check that the clock stays still, that the boot took a time in range, and that the number of pause calls is in range. A suite SHALL run it several times in a row.

#### Scenario: The clock stays still after READY
- **WHEN** a real run reaches `READY` and the test scenario waits between 20 and 40 real seconds
- **THEN** the game clock moved between 0 and 0.001 game seconds
- Checked by `harness/scenarios/boot_timing.py`.

#### Scenario: Boot time and pause calls are in range
- **WHEN** a real run reaches `READY` from a save
- **THEN** the boot took between 20 and 120 seconds, and `pauseGame` was called between 1 and 3 times
- Checked by `harness/scenarios/boot_timing.py`.

#### Scenario: A series of boots
- **WHEN** the suite `boot-timing` runs the test scenario 5 times
- **THEN** at least 4 of the 5 runs pass, and each failure has a boot reason or a failed check in its summary
- Checked by `harness/suites/boot-timing.json`.
