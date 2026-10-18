# harness/run-launcher Specification

## Purpose
The run launcher `harness/run.py` makes one test iteration. It deploys the mods, starts the real game, runs one test scenario, collects the evidence, stops the game and writes a short result file.

## Requirements

### Requirement: One run is a fixed list of phases
The launcher SHALL run the phases `preflight`, `deploy`, `launch`, `boot`, `scenario`, `collect` and `teardown` in this order, each with a time limit. After the first bad phase it SHALL skip the other phases, except the phases `collect` and `teardown`, which always run. With `--fake <outcome>` it SHALL run fake phases with no game.

#### Scenario: A phase fails
- **WHEN** a phase raises an error
- **THEN** the later phases are `skipped`, and `collect` and `teardown` still run
- **AND** the file `summary.json` is written
- Checked by `harness/tests/test_runlib_runner.py`.

#### Scenario: A phase hangs
- **WHEN** a phase does not end within its limit
- **THEN** it gets the status `timeout` and the run goes on with the always-run phases
- Checked by `harness/tests/test_runlib_runner.py`.

#### Scenario: The user presses Ctrl+C
- **WHEN** the launcher gets a keyboard interrupt
- **THEN** `summary.json` is still written and `teardown` still runs
- Checked by `harness/tests/test_runlib_runner.py`.

### Requirement: Each run has its own folder
The launcher SHALL make a folder `runs/<id>/` for each run. The id SHALL be `YYYYMMDD-HHMMSS-<4 hex>` in UTC, or the value of `--run-id`. It SHALL refuse an id that exists. It SHALL write files atomically, first `.tmp` and then rename.

#### Scenario: A duplicate run id
- **WHEN** `--run-id` names an existing run folder
- **THEN** the launcher ends with `harness_error` and does not touch the old folder
- Checked by `harness/tests/test_runlib_cli.py`.

#### Scenario: The plan is written first
- **WHEN** a run starts
- **THEN** `config.json` holds the scenario, the fixture, the slot, the phase limits and the masked environment
- Checked by `harness/tests/test_runlib_runfolder.py`.

### Requirement: The verdict follows fixed rules
The launcher SHALL end each run with one verdict: `pass` (exit code 0), `fail` (1), `crash` (2), `timeout` (3) or `harness_error` (4). It SHALL pick the first match in this order: crash, timeout, a failed boot or scenario, any bad phase, a missing scenario result, pass. A `pass` SHALL need every phase `ok`.

#### Scenario: A crash and a later error
- **WHEN** the game ended without a stop request and a later phase reports an error
- **THEN** the verdict is `crash`
- Checked by `harness/tests/test_runlib_summary.py`.

#### Scenario: A failed scenario and a cleanup problem
- **WHEN** a scenario assert fails and a cleanup phase also reports a problem
- **THEN** the verdict is `fail`, not `harness_error`
- Checked by `harness/tests/test_runlib_summary.py`.

#### Scenario: No scenario result
- **WHEN** all phases are `ok` but the scenario result is missing
- **THEN** the verdict is `harness_error`
- Checked by `harness/tests/test_runlib_summary.py`.

### Requirement: The summary stays short
The launcher SHALL write `summary.json` under 4096 bytes, also when the run raises. A phase with the status `ok` SHALL keep only its name and seconds. When the file is too large, the launcher SHALL add a warning note and cut long texts.

#### Scenario: A huge error text
- **WHEN** a phase raises an exception with a very long message
- **THEN** `summary.json` is under 4096 bytes and holds a warning note
- Checked by `harness/tests/test_runlib_runner.py`.

### Requirement: A game crash is a result
The launcher SHALL check in the phases `launch`, `boot` and `scenario` that the game process is alive. When it ended without a stop request, the launcher SHALL record the exit code, copy the crash reports and UE4SS dumps into `crash/`, and end with the verdict `crash`.

#### Scenario: The game ends during the scenario
- **WHEN** the game process ends and no stop was requested
- **THEN** the verdict is `crash` and `summary.json` holds the crash reason and exit code
- Checked by `harness/tests/test_runlib_phases.py`.

#### Scenario: The game ends after the stop request
- **WHEN** teardown stops the game on purpose
- **THEN** it is not a crash
- Checked by `harness/tests/test_runlib_phases.py`.

#### Scenario: A real crash
- **WHEN** the scenario `selftest-crash` runs in the real game
- **THEN** the verdict is `crash`, the exit code is 2, and `collect` and `teardown` ran
- Checked by `harness/scenarios/selftest_crash.py`.

### Requirement: One run at a time per slot, with a run cap
The launcher SHALL take a run lock for its slot (`runs/.lock` for slot 0, `runs/.lock-<n>` for other slots) and SHALL refuse to start when a live process holds it. It SHALL take over the lock of a dead process and record a note. It SHALL count runs in `runs/.iterations` and refuse to start at the cap (default 400, set by `--max-runs` or `HARNESS_MAX_RUNS`).

#### Scenario: The lock is held
- **WHEN** another live process holds the lock of the slot
- **THEN** the launcher prints `harness_error` and exits with code 4, with no run folder
- Checked by `harness/tests/test_runlib_cli.py`.

#### Scenario: The lock is stale
- **WHEN** the holder of the lock is dead
- **THEN** the launcher takes the lock and `summary.json` has a note about it
- Checked by `harness/tests/test_runlib_cli.py`.

#### Scenario: The run cap is reached
- **WHEN** the counter has reached the cap
- **THEN** the launcher refuses the run and the message names the option and the environment variable
- Checked by `harness/tests/test_runlib_cli.py`.

### Requirement: The game gets a private environment
The launcher SHALL start the game executable directly with the working folder `Win64` and a private `LOCALAPPDATA`. It SHALL set `HARNESS_RUN_DIR`, `HARNESS_AUTOBOOT`, `HARNESS_TEST_SAVE` and `HARNESS_TELEMETRY_INTERVAL_S`. `--env KEY=VALUE` SHALL add variables, but the launcher SHALL refuse names that start with `HARNESS_RUN_DIR`, `LOCALAPPDATA`, `PATH` or `UE4SS_BRIDGE`, and the names the launcher sets itself.

#### Scenario: A reserved variable
- **WHEN** `--env` names `HARNESS_AUTOBOOT`
- **THEN** the launcher fails before it makes a run folder
- Checked by `harness/tests/test_runlib_variant.py`.

#### Scenario: A secret value
- **WHEN** `--env` has a name that contains KEY, TOKEN, SECRET or PASSWORD
- **THEN** `config.json` stores the value masked and `summary.json` lists only the key
- Checked by `harness/tests/test_runlib_variant.py`.

### Requirement: Bad options fail before any run
The launcher SHALL check its options, the scenario name, the fixture and the slot before it makes a run folder. On an error it SHALL print `harness_error: <message>` to stderr, return exit code 4 and write no summary.

#### Scenario: An unknown scenario
- **WHEN** `--scenario` names a scenario that does not exist
- **THEN** the launcher ends with exit code 4 and no run folder
- Checked by `harness/tests/test_runlib_phases.py`.

#### Scenario: Both or none of scenario and fake
- **WHEN** neither or both of `--scenario` and `--fake` are given
- **THEN** the launcher refuses the call
- Checked by `harness/tests/test_runlib_phases.py`.

### Requirement: The mod's pak can be installed for one run
With `--pak NAME` the launcher SHALL install the built pak into the slot before the game starts and remove it after teardown. With `--keep-open` it SHALL leave the pak installed and add a note with the remove command.

#### Scenario: An earlier phase failed
- **WHEN** a phase before teardown fails or the game crashed
- **THEN** the pak is still removed
- Checked by `harness/tests/test_runlib_variant.py`.

#### Scenario: A foreign file in the way
- **WHEN** a pak file with another content already exists
- **THEN** the run fails with a clear message and the foreign file is kept
- Checked by `harness/tests/test_runlib_variant.py`.
