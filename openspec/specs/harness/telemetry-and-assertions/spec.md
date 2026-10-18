# harness/telemetry-and-assertions Specification

## Purpose
This capability gives a test scenario its eyes and its checks. The game writes state samples to a file, and the scenario asserts ranges, controls game time and waits for conditions.

## Requirements

### Requirement: The game samples its state
The mod `HarnessTelemetry` SHALL append one JSON line per sample to `telemetry.jsonl` in the run folder. A sample SHALL hold the fields `n`, `t`, `clock`, `paused`, `date`, `player`, `regions`, `custom` and `errors`. The interval SHALL come from `HARNESS_TELEMETRY_INTERVAL_S` (default 5 seconds), and 0 SHALL turn sampling off.

#### Scenario: Samples while the game runs
- **WHEN** the game runs for 40 game seconds
- **THEN** the samples have all fields and the spacing between samples is between 3 and 7 seconds
- Checked by `harness/scenarios/telemetry_sanity.py`.

#### Scenario: The interval is off
- **WHEN** the interval is 0
- **THEN** no sample is written
- Checked by `harness/tests/test_telemetry_mock.py`.

#### Scenario: A field cannot be read
- **WHEN** one field fails to read
- **THEN** the field is null, the failure is counted in `errors`, and the other fields stay
- Checked by `harness/tests/test_telemetry_mock.py`.

### Requirement: No sample outside a game map
The sampler SHALL write no sample when the game is in the main menu. The field `paused` SHALL be null in the first sample and true when the clock did not move since the last sample.

#### Scenario: The main menu
- **WHEN** no game engine actor exists
- **THEN** no sample is written
- Checked by `harness/tests/test_telemetry_mock.py`.

### Requirement: Mods can add metrics
The module `HarnessTelemetry` SHALL let a mod add a named metric with `register(name, fn)` and SHALL reject bad arguments. A metric that raises SHALL not stop the other metrics.

#### Scenario: A failing metric
- **WHEN** a registered metric raises an error
- **THEN** the sample still holds the other fields and the error is recorded
- Checked by `harness/tests/test_telemetry_mock.py`.

### Requirement: The telemetry reader reads whole lines
The harness SHALL read `telemetry.jsonl` through `ctx.telemetry`. It SHALL ignore a half-written last line and SHALL raise an error on a bad line in the middle. `window(start_clock, end_clock)` SHALL return the samples between two clock values.

#### Scenario: A half-written last line
- **WHEN** the file ends with an incomplete line
- **THEN** the reader returns the complete samples and no error
- Checked by `harness/tests/test_runlib_timectl.py`.

### Requirement: Assertions record short results
`ctx.expect` SHALL offer `equals`, `in_range`, `at_least`, `at_most`, `changed` and `eventually`. Each call SHALL add one record `{name, ok, value, rule}` and log it. The rule text SHALL be cut to 60 characters. A set value SHALL be stored as a sorted list. The scenario result SHALL pass only if every record is ok.

#### Scenario: One failed assert
- **WHEN** a scenario has nine ok records and one failed record
- **THEN** the result is not passed and the run verdict is `fail`
- Checked by `harness/tests/test_runlib_timectl.py`.

#### Scenario: A value outside the range
- **WHEN** `in_range` gets a value outside its limits, or `None`
- **THEN** the record is not ok and holds the value and the rule
- Checked by `harness/tests/test_runlib_timectl.py`.

#### Scenario: A condition becomes true late
- **WHEN** the function given to `eventually` turns true before the timeout
- **THEN** the record is ok and its value is the wait time in seconds
- Checked by `harness/tests/test_runlib_timectl.py`.

### Requirement: Game time is controlled and checked
`ctx.time` SHALL set the game speed to 1, 2 or 3 and check that the speed holds. It SHALL refuse another speed. `set_speed` SHALL unpause the game first and try again up to 3 times. `run_game_seconds` and `run_game_days` SHALL run the game until the clock has advanced, then pause, and SHALL raise a scenario failure when the wall time limit is reached.

#### Scenario: Speed 2 and 3
- **WHEN** a scenario sets speed 2 or 3
- **THEN** the game reports 4 or 8 game seconds for each wall second
- Checked by `harness/tests/test_runlib_timectl.py`.

#### Scenario: The game drops to 1x
- **WHEN** an army is spotted and the game drops the speed during a run
- **THEN** the control sets the speed again and the run goes on
- Checked by `harness/tests/test_runlib_timectl.py`.

#### Scenario: Run game days over the year end
- **WHEN** a scenario runs a number of game days across the end of a year
- **THEN** the day count follows `daysTotal` and does not wrap
- Checked by `harness/tests/test_runlib_timectl.py`.

#### Scenario: The clock is blocked
- **WHEN** the clock does not move after the unpause
- **THEN** the scenario fails with a message about a pop-up that may hold the pause
- Checked by `harness/tests/test_runlib_timectl.py`.

### Requirement: Waits are bounded
`ctx.run_until` SHALL poll a condition on the wall clock or the game clock. It SHALL raise `WaitTimeout` at the limit and `GameStalled` when the game clock stands still twice in a row, after an optional repair. Both errors SHALL be scenario failures, which give the verdict `fail`.

#### Scenario: A wait times out
- **WHEN** the condition never turns true
- **THEN** the run ends with the verdict `fail` and a message that names the limit
- Checked by `harness/tests/test_runlib_waiting.py`.

#### Scenario: A stall is repaired
- **WHEN** the clock stalls once and the repair function restarts it
- **THEN** the wait goes on with no error
- Checked by `harness/tests/test_runlib_waiting.py`.

### Requirement: Every test scenario has a time limit
A test scenario module SHALL set `LIMIT_S` above 0 and at most 13500. A limit above 300 SHALL come with a non-empty `LONG_REASON`. The registry SHALL refuse a name that two files define.

#### Scenario: A long limit with no reason
- **WHEN** a scenario sets `LIMIT_S` to 600 and no `LONG_REASON`
- **THEN** the import of the scenario fails with a clear message
- Checked by `harness/tests/test_runlib_waiting.py`.

#### Scenario: A real time advance
- **WHEN** the scenario `time-advance` runs in the real game
- **THEN** the game days advance by the asked amount and the checks pass
- Checked by `harness/scenarios/time_advance.py`.
