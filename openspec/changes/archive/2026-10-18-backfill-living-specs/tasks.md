# Tasks

## 1. Plan

- [x] 1.1 Write the proposal, the design with the capability map (D1) and the delta for `process/spec-workflow`; verify with `openspec validate backfill-living-specs --strict`
- [x] 1.2 Decide how planned legacy work moves (D6, the user chose "convert when started"); verify by review

## 2. Convert

- [x] 2.1 Write the harness core deltas (group H1) and the report `notes/h1-report.md`; verify with `openspec validate --strict`
- [x] 2.2 Write the harness tooling deltas (group H2) and `notes/h2-report.md`; verify with `openspec validate --strict`
- [x] 2.3 Write the harness command deltas (group H3) and `notes/h3-report.md`; verify with `openspec validate --strict`
- [x] 2.4 Write the Invasion Mod deltas (groups MA, MB, MC) and their reports; verify with `openspec validate --strict`

## 3. Review

- [x] 3.1 Check that every "Checked by" path exists; verify with a script over all deltas
- [x] 3.2 Spot-check claims in the code and fix overlaps between groups (D7); verify by review
- [x] 3.3 Fix the wiki where the review found it wrong (scheduler tick); verify with `wiki.py check`

## 4. Docs

- [x] 4.1 Point the legacy banners (`docs/harness/README.md`, `design/README.md`) and the wiki page `docs-and-specs.md` to the living specs; verify with `wiki.py check`
- [x] 4.2 Add the change to `CHANGELOG.md`; verify by review

## Workflow follow-up

- Push, open the pull request that closes #253, and wait for the user's review.
- After the review, run `openspec archive backfill-living-specs --yes` as the last commit, then merge.
