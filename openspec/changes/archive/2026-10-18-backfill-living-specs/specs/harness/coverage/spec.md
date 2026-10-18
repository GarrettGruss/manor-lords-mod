# Spec Delta

## Purpose

The coverage tool measures how much of the Invasion Mode brief the harness can test. It reads a list of criteria and the `COVERS` tags of the scenarios, and prints the share of automatable criteria that have a verified test method.

## ADDED Requirements

### Requirement: The criteria file is validated
The tool `harness/tools/coverage.py` SHALL read the criteria file (default `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/criteria.json`) as a list of objects with fixed fields. The mark SHALL be `A`, `P` or `H`, and an id SHALL be unique. An `H` criterion SHALL have a `reason_human`. An `A` or `P` criterion SHALL have a `method`. A bad file SHALL stop the tool with exit code 2 and a list of the problems.


#### Scenario: A bad criteria file
- **WHEN** a criterion has a missing field, a bad mark, a duplicate id, or no reason for `H`
- **THEN** the tool exits with code 2 and names each problem
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: The real file
- **WHEN** the tool loads the criteria file of the repo
- **THEN** the file is valid and every id is unique
- Checked by `harness/tests/test_coverage.py`.

### Requirement: Scenario tags are read without running scenarios
The tool SHALL read the `NAME` and the `COVERS` list of each scenario file in `harness/scenarios/` by parsing the source, and SHALL NOT import or run it. A file without `COVERS` SHALL be ignored. A `COVERS` value that is not a literal list SHALL stop the tool. A syntax error SHALL stop the tool with exit code 2 and name the file.

#### Scenario: Metadata
- **WHEN** a scenario file sets `NAME` and `COVERS`
- **THEN** the tool reads both and does not execute the file
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: Bad scenario file
- **WHEN** a scenario file has a syntax error or a computed `COVERS`
- **THEN** the tool stops with an error that names the file
- Checked by `harness/tests/test_coverage.py`.

### Requirement: Verified share
The tool SHALL count an `A` or `P` criterion as verified when its `method_verified` flag is true or a covering scenario has a passing run. Only the verdict `pass` SHALL count, with the newest passing run of a scenario. A broken `summary.json` SHALL be skipped. The report SHALL show the verified share against the target of 90 percent, the blocked criteria, the human criteria, and the gap list.


#### Scenario: Shares and blocked criteria
- **WHEN** the criteria and scenarios are read
- **THEN** the report shows the verified share, the blocked criteria and the gaps
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: A scenario without a passing run
- **WHEN** a scenario covers a criterion and has no passing run
- **THEN** the criterion is not verified and is not in the gap list
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: A passing run
- **WHEN** a covering scenario has a passing run
- **THEN** the criterion is verified
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: Only a pass counts
- **WHEN** a scenario has older passing runs and a newer failing run
- **THEN** the newest passing run is used and the failing run is ignored
- Checked by `harness/tests/test_coverage.py`.

### Requirement: Unknown ids and exit codes
The tool SHALL exit with code 2 when a scenario covers an id that the criteria file does not have, and SHALL name the id. With `--min-verified <share>`, it SHALL exit with code 1 when the verified share is lower. With `--json`, it SHALL print the result as JSON with the keys `total`, `by_mark`, `automatable_share`, `verified`, `verified_share`, `blocked`, `human`, `unknown_covers`, `gaps`, `scenarios` and `target`.

#### Scenario: Unknown id
- **WHEN** a scenario has `COVERS = ["X9"]` and X9 is not a criterion
- **THEN** the tool prints "unknown id X9" and exits with code 2
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: Minimum share
- **WHEN** the verified share is 50 percent and `--min-verified` is 0.5, then 0.9
- **THEN** the exit code is 0, then 1
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: JSON output
- **WHEN** the tool runs with `--json`
- **THEN** the output has all the keys above and the list of verified ids
- Checked by `harness/tests/test_coverage.py`.

### Requirement: The criteria file agrees with the spec tables
With `--check-spec`, the tool SHALL compare the ids, titles and marks of the criteria file with the criteria tables of the spec README (default `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/README.md`). It SHALL print each difference and exit with code 1, or print that they agree and exit with code 0.

#### Scenario: The real files agree
- **WHEN** `--check-spec` runs on the files of the repo
- **THEN** the exit code is 0
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: A changed table
- **WHEN** the spec table has another id, title or mark than the criteria file
- **THEN** the tool names the difference and exits with code 1
- Checked by `harness/tests/test_coverage.py`.
