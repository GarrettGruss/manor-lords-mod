# harness/mod-commands Specification

## Purpose
Mod commands let a Lua mod expose its own commands and metrics, so a scenario can drive and observe the state that the mod defines. The parts are the Lua module `HarnessCommands` and the Python class `ModState` (`ctx.mod`).

## Requirements

### Requirement: A mod serves its own commands through files
Each mod that registers a command or a metric SHALL start one poller (every 100 ms) for its mod name. The poller SHALL read `<run>/modcmd/<Mod>/<nnnn>.json`, run the command on the game thread inside `pcall`, and write `<nnnn>.result.json` with `{"ok":true,"result":...}` or `{"ok":false,"error":...}`. Both sides SHALL write a `.tmp` file and then rename it. Without the run folder variable `HARNESS_RUN_DIR`, no poller SHALL start.

#### Scenario: A registered command runs
- **WHEN** a request file arrives for a registered command
- **THEN** the handler runs once and the result file holds its result
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: Order and half-written files
- **WHEN** requests arrive in order, with a gap, or as a half-written file
- **THEN** they run in number order, a gap waits, and a request is taken only after the rename
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: No run folder
- **WHEN** the run folder variable is not set
- **THEN** no poller starts
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Command names and mod isolation
A command name SHALL be `<Mod>.<command>`: letters, digits and underscore, a letter first. The prefix `harness.` SHALL be reserved. A duplicate name SHALL be refused until it is unregistered. The poller of a mod SHALL run only commands of that mod and the built-in `harness.list_commands` and `harness.metrics`.

#### Scenario: Bad and reserved names
- **WHEN** a mod registers `bad name`, `harness.x` or a name twice
- **THEN** the registration is refused with a message
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: A command of another mod
- **WHEN** a request names a command of another mod
- **THEN** the mod answers with a refusal and the other command does not run
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Arguments follow a schema
A command SHALL declare a schema of allowed arguments. The types are `number`, `integer`, `string` and `boolean`. The rule keys are `type`, `required`, `min`, `max`, `maxLength` and `oneOf`. The mod SHALL refuse an unknown, missing or wrongly typed argument before the handler runs. A string SHALL have a default limit of 64 characters.

#### Scenario: Bad arguments
- **WHEN** a request has an unknown argument, a missing required argument, a wrong type, or a value outside its limits
- **THEN** the result is a refusal that names the command and the argument, and the handler does not run
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: String limit
- **WHEN** a string argument is longer than 64 characters and the schema sets no other limit
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Handler results and refusals
A handler SHALL return a JSON value, or `nil` and a message to refuse on purpose. A handler error SHALL become an error result. A result that is not JSON SHALL be refused. A handler slower than 50 ms SHALL be logged and not stopped. Request text SHALL be decoded as data and never run as code.

#### Scenario: Refusal on purpose
- **WHEN** a handler returns `nil, "message"`
- **THEN** the result is `ok` false with that message
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: Handler error and slow handler
- **WHEN** a handler raises an error, or takes longer than 50 ms
- **THEN** the error becomes an error result, and the slow handler finishes and is logged
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

#### Scenario: Request text is not code
- **WHEN** a string argument holds Lua source text
- **THEN** it is handled as a string and not run
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Metrics
A mod SHALL be able to register named metrics with `HarnessCommands.metric`. The built-in command `harness.metrics` SHALL return the current value of each metric of that mod. A metric that fails or returns a table SHALL be left out and named under `errors`.

#### Scenario: Metric list
- **WHEN** a client calls `harness.metrics` for a mod
- **THEN** the answer has the values of its metrics, and failing metrics are named under `errors`
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Hot reload keeps one poller
Each poller SHALL write a random token to `<Mod>/owner.txt` and SHALL stop when the file holds another token. A reloaded mod SHALL skip the requests that were answered.

#### Scenario: A stale poller
- **WHEN** a new Lua state of the mod takes the folder
- **THEN** the old poller stops
- Checked by `harness/tests/test_fakegame_harnesscommands.py`.

### Requirement: Scenario API for mod commands
The scenario API `ctx.mod` SHALL offer `command`, `refusal`, `commands`, `metric`, `wait_metric`, `read_metrics` and `metrics_window`. A mod refusal SHALL raise `ModCommandError` with the message of the mod. A mod that does not answer SHALL raise `ModDidNotAnswer` with the mod name. A bad name SHALL raise `ValueError` before any request is sent. A missing metric SHALL raise `ModMetricError`, or give the default when one is passed.

#### Scenario: Command and refusal
- **WHEN** a scenario runs a command that the mod refuses
- **THEN** `command` raises `ModCommandError` with the reason, and `refusal` returns the reason
- Checked by `harness/tests/test_runlib_modstate.py`.

#### Scenario: Wait for a metric
- **WHEN** a scenario calls `wait_metric` with a predicate and a timeout
- **THEN** it returns the first value that passes, or raises `ModMetricError` with the last value at the timeout
- Checked by `harness/tests/test_runlib_modstate.py`.

#### Scenario: Metric window
- **WHEN** a scenario has read metrics several times
- **THEN** `metrics_window` returns one row for each read, with a time and the values, and can filter by name and time
- Checked by `harness/tests/test_runlib_modstate.py`.

#### Scenario: A mod that is not loaded
- **WHEN** the request folder of the mod does not exist or the mod never answers
- **THEN** the error is `ModDidNotAnswer`, not a mod refusal
- Checked by `harness/tests/test_runlib_modstate.py`.

### Requirement: Request numbers survive a second client
A new client of a mod channel SHALL continue after the highest request number already in the folder, and each mod SHALL have its own numbers.

#### Scenario: A second client
- **WHEN** a second client opens a folder that holds requests 0001 to 0005
- **THEN** its first request is 0006
- Checked by `harness/tests/test_runlib_modstate.py`.
