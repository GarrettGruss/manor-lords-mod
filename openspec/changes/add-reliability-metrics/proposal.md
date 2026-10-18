# Proposal: add reliability metrics per spec domain

Issue: #289. No legacy folder.

## Why

The harness and the mod grow fast (189 `feat` and 58 `fix` commits, 515 runs). We do not know which spec domains break most often, or how fast we repair them. Without numbers we cannot judge the risk of a regression before a change.

## What Changes

- A shared domain map: path patterns map files and test scenarios to a capability (`harness/<name>`, `mod/<feature>`, `process/<name>`).
- Phase 1, a git report tool (`harness/tools/reliability.py git`). For each domain it gives:
  - `feat` and `fix` counts, and the fix-to-feat ratio
  - churn (lines added and removed)
  - change failure rate: the share of `feat` commits that get a `fix` in the same domain within N days (default 14)
  - bug lifetime: the time from the commit that a fix repairs (found with `git blame`) to the fix
- Phase 2, a run report (`harness/tools/reliability.py runs`). It reads `runs/*/summary.json`. For each test scenario and each domain it gives:
  - a pass/fail timeline
  - MTTF (time between failures) and MTTR (time from a failure to the next pass)
  - flaky rate: failures that pass on one rerun with the same commit
- Each `summary.json` records the full commit SHA and the domain of the test scenario.
- Both reports write JSON and a short Markdown table. Values show their sample count.

## Non-goals

- Defect tracking with GitHub issues (solution 2). We add it only if phase 1 shows that `fix` labels are too noisy.
- Dashboards or a hosted page.
- Automatic gates that block a merge on a metric.
- Exact values. The sample is small. The reports show counts and trends.

## Capabilities

### New Capabilities
- `harness/reliability`: domain map, git report, run report.

### Modified Capabilities
- `harness/run-launcher`: `summary.json` records the full commit SHA and the test scenario domain.

## Impact

- Code: new `harness/tools/reliability.py` and `harness/reliabilitylib/`; `harness/runlib/summary.py`.
- Data: new `harness/reliability/domains.json`.
- Tests: new `harness/tests/test_reliability_*.py`, `harness/tests/test_runlib_summary.py`.
- Docs: a wiki page, the `harness-overview` skill, `CHANGELOG.md`.
