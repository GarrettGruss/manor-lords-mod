# Spec Delta

## Purpose

The MCP server `manor-harness` lets an agent run a test scenario and read the result without shell commands. A run is started and then polled, because a run takes one to three minutes.

## ADDED Requirements

### Requirement: A run starts at once and is polled
The tool `run_scenario` SHALL start `harness/run.py` as a detached process and return at once with `status: started`, the `run_id`, the `slot` and the launcher pid. The tool `wait_for_run` SHALL wait at most 50 seconds for `summary.json` and SHALL return `done` with the summary, or `running` with a phase hint and the elapsed time.

#### Scenario: Start and poll
- **WHEN** an agent calls `run_scenario` and then `wait_for_run`
- **THEN** the first call returns `started` and the second returns `running` or `done`
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: A long wait is capped
- **WHEN** an agent asks `wait_for_run` for 500 seconds
- **THEN** the call waits at most 50 seconds
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: The launcher refuses to run
- **WHEN** the launcher ends before it makes a summary
- **THEN** `wait_for_run` returns `failed_to_start` with the launcher log
- Checked by `harness/tests/test_harness_tools_tools.py`.

### Requirement: The server offers ten tools
The server SHALL offer `list_scenarios`, `run_scenario`, `wait_for_run`, `read_summary`, `list_runs`, `read_log`, `read_telemetry`, `list_screenshots`, `game_status` and `stop_game`. Read-only tools SHALL carry the read-only hint. `run_scenario` and `stop_game` SHALL carry the destructive hint.

#### Scenario: A client lists the tools
- **WHEN** an MCP client connects over stdio
- **THEN** it can list the tools and call two of them
- Checked by `harness/tests/test_harness_tools_mcp.py`.

### Requirement: A busy slot refuses a start
`run_scenario` SHALL refuse with an error result when the slot is busy (all slots, for `auto`), when the slot is not installed, or when the scenario is unknown or hidden. A start claim file per slot SHALL stop two quick calls from starting two launchers in one slot.

#### Scenario: Two calls at once
- **WHEN** two `run_scenario` calls for one slot run at the same time
- **THEN** exactly one starts and the other is refused with the first run id
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: A stale claim
- **WHEN** the claim belongs to a launcher that is no longer alive
- **THEN** the new call replaces the claim and starts
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: A hidden scenario
- **WHEN** an agent starts a hidden test-only scenario through the tool
- **THEN** the tool refuses it
- Checked by `harness/tests/test_harness_tools_scenarios.py`.

### Requirement: Names and paths are checked
Every run id, log name and scenario name SHALL match `[A-Za-z0-9_-]{1,64}`. `read_log` SHALL accept only the names `mod.log`, `UE4SS.log`, `boot.json`, `scenario.log`, `scenario.json`, `launcher.log` and `config.json`. Every resolved path SHALL be inside `runs/`.

#### Scenario: A path trick
- **WHEN** a tool gets a run id with `..`, a slash or a drive letter
- **THEN** the tool returns an error result and reads no file
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: A link out of the runs folder
- **WHEN** a path inside `runs/` is a link to a folder outside it
- **THEN** the tool rejects the path
- Checked by `harness/tests/test_harness_tools_tools.py`.

### Requirement: Results are small
Each tool result SHALL be under 20,000 bytes, and a cut SHALL be marked `truncated`. `read_log` SHALL return at most 1000 lines and 15,000 characters from the end of the file. `read_telemetry` SHALL return at most 200 samples. `list_runs` SHALL return at most 50 runs. `list_screenshots` SHALL return at most 200 paths.

#### Scenario: A huge log
- **WHEN** a log is larger than the limit
- **THEN** the tool returns the tail with a `truncated` mark
- Checked by `harness/tests/test_harness_tools_tools.py`.

#### Scenario: Log text is data
- **WHEN** a log line holds text that looks like an instruction
- **THEN** the tool returns it inside a JSON field as data
- Checked by `harness/tests/test_harness_tools_tools.py`.

### Requirement: Errors are results
A tool SHALL return `{"ok": false, ...}` with a clear message on an error and SHALL NOT raise to the client.

#### Scenario: No runs yet
- **WHEN** `read_summary` runs with no run or no summary
- **THEN** the result is an error result with a clear message
- Checked by `harness/tests/test_harness_tools_tools.py`.

### Requirement: Stopping the game is guarded
`stop_game` SHALL refuse while a live run holds the lock of the slot or a start claim is active. Otherwise it SHALL stop the game processes of that slot and report the stopped pids, and report a process that stays.

#### Scenario: A run holds the lock
- **WHEN** `stop_game` is called while a run holds the slot lock
- **THEN** the tool refuses and stops nothing
- Checked by `harness/tests/test_harness_tools_tools.py`.

### Requirement: Game status shows slots and the run cap
`game_status` SHALL report the game processes, the slots with their lock holders, the free slots, and the runs used against the cap. A lock of a dead process SHALL not count as a holder and SHALL not be removed by the tool.

#### Scenario: A stale lock
- **WHEN** the lock file names a dead pid
- **THEN** the slot shows as free and the file stays
- Checked by `harness/tests/test_harness_tools_tools.py`.
