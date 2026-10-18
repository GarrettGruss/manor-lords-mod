# Spec Delta

## MODIFIED Requirements

<!-- Issue: #269 -->

### Requirement: Legacy spec folders are read-only
`docs/harness/` and `docs/mod/M<NN>-*/` SHALL be read-only history. No work SHALL happen in them: no new spec folders, iteration files, notes or status lines. All open legacy work SHALL be an OpenSpec change, listed in the inventory of the change `migrate-legacy-work`. Legacy folders SHALL NOT be moved, renamed or deleted. The coverage data of spec 10 (`criteria.json` and the criteria tables of its README) SHALL stay live, because the coverage tool reads them.

#### Scenario: A criterion is verified
- **WHEN** a criterion of the Invasion Mode brief is verified
- **THEN** `criteria.json` and the spec 10 README tables are updated
- **AND** `harness/tools/coverage.py --check-spec` passes
- Checked by `harness/tools/coverage.py --check-spec`.

#### Scenario: New work for an area with a legacy spec
- **WHEN** new work touches an area that has a legacy spec
- **THEN** the work is an OpenSpec change, and the legacy spec is only read as source material
- **AND** the change names the legacy file it continues
- Checked by review.

#### Scenario: Open legacy work
- **WHEN** an iteration such as M12.02 was still open in its legacy folder on 2026-10-18
- **THEN** it continues as its OpenSpec change, under the issue that the change names
- **AND** its legacy folder gets no more edits
- Checked by review.
