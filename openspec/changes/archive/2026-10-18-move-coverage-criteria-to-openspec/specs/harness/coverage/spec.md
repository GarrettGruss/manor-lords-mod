## MODIFIED Requirements
<!-- Issue: #279 -->

### Requirement: The criteria file is validated
The tool `harness/tools/coverage.py` SHALL read the criteria file (default `openspec/specs/harness/coverage/criteria.json`) as a list of objects with fixed fields. The mark SHALL be `A`, `P` or `H`, and an id SHALL be unique. An `H` criterion SHALL have a `reason_human`. An `A` or `P` criterion SHALL have a `method`. A bad file SHALL stop the tool with exit code 2 and a list of the problems.

#### Scenario: A bad criteria file
- **WHEN** a criterion has a missing field, a bad mark, a duplicate id, or no reason for `H`
- **THEN** the tool exits with code 2 and names each problem
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: The real file
- **WHEN** the tool loads the criteria file of the repo
- **THEN** the file is valid and every id is unique
- Checked by `harness/tests/test_coverage.py`.

### Requirement: The criteria file agrees with the spec tables
With `--check-spec`, the tool SHALL compare the ids, titles and marks of the criteria file with the criteria tables of the criteria document (default `openspec/specs/harness/coverage/criteria.md`). It SHALL print each difference and exit with code 1, or print that they agree and exit with code 0.

#### Scenario: The real files agree
- **WHEN** `--check-spec` runs on the files of the repo
- **THEN** the exit code is 0
- Checked by `harness/tests/test_coverage.py`.

#### Scenario: A changed table
- **WHEN** the spec table has another id, title or mark than the criteria file
- **THEN** the tool names the difference and exits with code 1
- Checked by `harness/tests/test_coverage.py`.
