# Spec Delta

## Purpose

The bridge is the live control channel into the running game. An agent or a test scenario reads and sets properties, calls UFunctions and inspects objects without a mod edit or a game restart.

## ADDED Requirements

### Requirement: Requests use a file protocol
The bridge client SHALL send each request as `request.json` in the bridge folder and read the answer from `response.json`. The client SHALL write `request.tmp` first and rename it. The request body SHALL hold a unique `id`, and the client SHALL ignore a response with another id.

#### Scenario: A request gets its own answer
- **WHEN** a client sends a request and an older response with another id is in the folder
- **THEN** the client drops the old response and waits for the response with its own id
- Not checked yet.

#### Scenario: A fresh request is still unconsumed
- **WHEN** `request.json` is younger than 10 seconds when a new request starts
- **THEN** the client fails with a message that the request is still unconsumed
- **AND** a `request.json` older than 10 seconds is deleted as a leftover of a dead game
- Not checked yet.

### Requirement: A timeout names its cause
The bridge client SHALL end a request that gets no answer with a `BridgeError` after the timeout (15 seconds by default). The message SHALL say which case it was: never picked up, picked up but no answer, or the game died.

#### Scenario: The game is not running
- **WHEN** a request is never picked up and no game process runs
- **THEN** the error says the request was never picked up because the game is not running
- Not checked yet.

#### Scenario: The game died during the request
- **WHEN** the request was picked up and the game process ends before the answer
- **THEN** the error holds the text of the crash report written after the request started
- Not checked yet.

### Requirement: The bridge folder follows the run
The Lua mod `UEBridge` SHALL use `<HARNESS_RUN_DIR>/bridge` as its folder when `HARNESS_RUN_DIR` is set. The harness SHALL point the Python client at the same folder, so each run has its own request and response files.

#### Scenario: A scenario talks to the game of its run
- **WHEN** a scenario starts in a run
- **THEN** the client folder is the absolute path `runs/<id>/bridge` of that run
- **AND** the client uses the game folder and the process id of the slot of the run
- Not checked yet.

### Requirement: Game objects are touched on the game thread
The `UEBridge` mod SHALL run every operation that touches a game object on the game thread. It SHALL delete `request.json` before it runs the handler, so one request never runs twice.

#### Scenario: A batch of operations
- **WHEN** a request of the op `batch` arrives
- **THEN** its operations run in order on the game thread and the response holds one entry for each operation
- Not checked yet.

### Requirement: Raw Lua eval has two locks
The `eval_lua` tool and the CLI verb `eval` SHALL exist only when the environment variable `UE4SS_BRIDGE_ALLOW_EVAL` is `1`. The Lua mod SHALL accept eval only when `allow_eval` is true in its settings, and SHALL force eval off when `allow_writes` is false. The eval timeout SHALL be at most 60 seconds.

#### Scenario: Eval is off by default
- **WHEN** the environment variable is unset and `allow_eval` keeps its default `false`
- **THEN** the tool is not registered and the Lua mod refuses an eval request
- Not checked yet.

### Requirement: Writes and large answers are limited
The `UEBridge` mod SHALL refuse `set`, `call` and `dump` when `allow_writes` is false. It SHALL clamp list limits to at most 500 and turn a response over 1,000,000 bytes into an error. It SHALL refuse a `get`, `set` or `call` whose name is not a non-empty string.

#### Scenario: A nil name
- **WHEN** a request calls `get`, `set` or `call` with a missing name
- **THEN** the mod answers with an error and the game does not crash
- Not checked yet.

### Requirement: Bridge failures are results
The bridge SHALL report a failure as a `BridgeError` text or an error entry in the response. A bridge failure SHALL NOT crash the harness. A scenario that gets a `BridgeError` while the game is dead SHALL end with the verdict `crash`.

#### Scenario: The game dies during a scenario
- **WHEN** a bridge call fails and the game process has ended
- **THEN** the run verdict is `crash`
- Checked by `harness/tests/test_runlib_phases.py`.

### Requirement: Scenarios use a small client
The harness SHALL give each scenario a `Bridge` client that wraps the bridge calls it needs (clock, pause, property reads, calls on the player). The client SHALL take its transport function as a parameter, so tests can replace it.

#### Scenario: A test replaces the transport
- **WHEN** a test builds `Bridge` with a fake transport function
- **THEN** the clock and pause helpers run against the fake with no game
- Checked by `harness/tests/test_runlib_timectl.py`.
