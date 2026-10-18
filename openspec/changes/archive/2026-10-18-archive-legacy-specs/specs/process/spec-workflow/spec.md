# Spec Delta

## MODIFIED Requirements

<!-- Issue: #288 -->

### Requirement: Legacy spec folders are read-only
The old legacy specs (formerly `docs/harness/<NN>-*/`, `docs/mod/M<NN>-*/` and `docs/mod/feature-breakdown.md`) SHALL live unchanged in `openspec/changes/archive/<date>-legacy-*/` as read-only history. No work SHALL happen in them. All their open work SHALL be an OpenSpec change. References SHALL use the archive paths; only `CHANGELOG.md` files keep old paths as history. The coverage data SHALL live in `openspec/specs/harness/coverage/`.

#### Scenario: A criterion is verified
- **WHEN** a criterion of the Invasion Mode brief is verified
- **THEN** `openspec/specs/harness/coverage/criteria.json` and `criteria.md` are updated
- **AND** `harness/tools/coverage.py --check-spec` passes
- Checked by `harness/tools/coverage.py --check-spec`.

#### Scenario: New work for an area with a legacy spec
- **WHEN** new work touches an area that has a legacy spec
- **THEN** the work is an OpenSpec change, and the archived legacy spec is only read as source material
- **AND** the change names the archived legacy file it continues
- Checked by review.

#### Scenario: Open legacy work
- **WHEN** an iteration such as M12.02 was still open in its legacy folder on 2026-10-18
- **THEN** it continues as its OpenSpec change, under the issue that the change names
- **AND** its archived legacy folder gets no more edits
- Checked by review.

#### Scenario: A link to a legacy note
- **WHEN** code, a skill, the wiki or a spec points to a legacy note
- **THEN** the path starts with `openspec/changes/archive/` and the file exists
- Checked by review and `wiki.py check` (for wiki sources).
