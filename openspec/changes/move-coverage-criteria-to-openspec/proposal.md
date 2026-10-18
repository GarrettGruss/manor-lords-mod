# Proposal: Move coverage criteria to openspec

Issue: #279. Legacy source: `docs/harness/10-invasion-testability/criteria.json` and the criteria tables in `docs/harness/10-invasion-testability/README.md`.

## Why
The coverage data of spec 10 is live. `harness/tools/coverage.py` reads `criteria.json` and checks it against the README tables (`--check-spec`). `CONTRIBUTING.md` keeps it in the legacy folder as an exception. The legacy folders are read only, so a criterion cannot be updated in the right place. The living spec `harness/coverage` names the legacy paths as defaults. This change moves the data into `openspec/` so the legacy folder can be left alone.

## What Changes
- Move `criteria.json` and the criteria tables to a place under `openspec/specs/harness/coverage/` (the user decides the exact place; see `design.md`).
- Change the two default paths in `harness/tools/coverage.py`.
- Update the requirement texts in `harness/coverage` (MODIFIED).
- Update `CONTRIBUTING.md`, the skill `harness-coverage` and the wiki page on coverage.
- The open criteria stay as data: P3 and M2 (not verified), Q3 (human), Q4 (partly, a person judges). Their test work is in other changes (`spike-bailey-buildings` for M2).

## Non-goals
- Change the criteria, their marks or the 90 percent target.
- Verify new criteria.
- Delete the legacy copy. It stays as history.

## Legacy folders
`docs/harness/10-invasion-testability/` (read only; the live data moves out of it).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `harness/coverage`: the default paths of the criteria file and the criteria document.

## Impact
`harness/tools/coverage.py`, `harness/tests/test_coverage.py`, `CONTRIBUTING.md`, `.claude/skills/harness-coverage/SKILL.md`, wiki. The command `coverage.py --check-spec` must pass after the move.
