# Spec Delta

## Purpose

This capability defines how work on the harness and on mods is tested: the test layers from fast to slow, the principles that every test follows, and the gate that work passes before it is merged.

## ADDED Requirements

### Requirement: Use the fastest test layer that answers the question
An agent SHALL use the fastest layer that can answer its question and SHALL move to a slower layer only when it must. The layers are, from fast to slow: Lua syntax check, fake game tests, live probe through the bridge, test scenario run in the real game, regression suite, and human review.

#### Scenario: A pure logic change
- **WHEN** a change touches only Lua logic of a mod
- **THEN** the fake game tests and the syntax check run before any real game run
- Checked by review.

#### Scenario: The syntax layer
- **WHEN** a Lua file has a syntax error
- **THEN** `harness/tests/lua_syntax.py` fails
- Checked by `harness/tests/lua_syntax.py`.

### Requirement: Tests assert ranges and treat crashes as results
A test for game behavior SHALL assert ranges, not exact values, because the simulation is not deterministic. A game crash SHALL be a result with logs, not a harness failure. Every wait SHALL have a time limit. Repeated runs SHALL measure flakiness, and one pass SHALL NOT prove a feature.

#### Scenario: A test scenario for game state
- **WHEN** a test scenario checks a number the game simulates
- **THEN** it uses `in_range`, `at_least` or `at_most`, and uses `equals` only for flags and names
- Checked by review.

#### Scenario: A crash during a run
- **WHEN** the game crashes during a run
- **THEN** the verdict is `crash` and the logs are collected
- Checked by `harness/tests/test_runlib_phases.py`.

### Requirement: A test never touches real user data
A test SHALL NOT touch the real save folder, the real game folder or the network. It SHALL use temp folders. The harness SHALL never write to the user's saves, except through the guarded action `save_game` and the guarded fixture install.

#### Scenario: A new Python test
- **WHEN** a new Python test needs files
- **THEN** it uses `tempfile` folders
- Checked by review.

### Requirement: Rules are enforced by tests
The repo SHALL keep two rules as tests: harness code SHALL NOT name the Invasion Mod or its features, and only `HarnessSave.lua` SHALL call a game save function.

#### Scenario: A planted mod name
- **WHEN** harness code names the Invasion Mod
- **THEN** the boundary test fails
- Checked by `harness/tests/test_boundary.py`.

#### Scenario: The boundary check itself
- **WHEN** a mod name is planted in Python and in Lua test files
- **THEN** the check finds both
- Checked by `harness/tests/test_boundary.py`.

### Requirement: The criteria matrix is checked
The coverage tool `harness/tools/coverage.py` SHALL read the scenarios' `COVERS` lists without running them, count a criterion as verified when its method is verified or a tagged scenario has a passing run, and return exit code 2 for an unknown criterion id. `--check-spec` SHALL compare `criteria.json` with the spec tables.

#### Scenario: An unknown criterion id
- **WHEN** a scenario lists an id that is not in `criteria.json`
- **THEN** the tool exits with code 2
- Checked by `harness/tests/test_coverage.py`.

### Requirement: Work passes a gate before merge
A pull request SHALL be merged only after the full test set passes: `test_runlib*`, `test_suitelib*`, `test_harness_tools*`, `test_reload_mods`, `test_pakmod`, `test_coverage`, `test_fakegame_*`, `test_telemetry_mock`, `lua_syntax.py`, `boot_state_machine.py` and `coverage.py --check-spec`. The pull request SHALL show the evidence, list the criteria left to the human, and note what was not verified.

#### Scenario: A branch is ready
- **WHEN** a branch is ready for review
- **THEN** the full set was run on Windows and the pull request holds the evidence and the unverified items
- Checked by review.

### Requirement: A feature has measurable criteria
A feature spec SHALL state its acceptance criteria as measurable game state (ranges) and SHALL mark each criterion automated or human. At least one test scenario SHALL check each automated criterion, and the goal is that at least 90 percent of the criteria of a feature are automated.

#### Scenario: A new feature spec
- **WHEN** a feature spec is written
- **THEN** each criterion names a range and is marked automated or human, with a reason for each human one
- Checked by review.

### Requirement: A new feature comes with a test
A new feature SHALL add a test in the same commit. A new test scenario SHALL be added to the scenario list test in `harness/tests/test_runlib_scenario.py`, and a failing test SHALL fail with a clear message.

#### Scenario: A new test scenario
- **WHEN** a test scenario file is added
- **THEN** the scenario list test names it
- Checked by `harness/tests/test_runlib_scenario.py`.
