## 1. Decision
- [ ] 1.1 Ask the user the three questions in `design.md`. Verified by the answers written in `design.md`.

## 2. If the user chooses a schedule
- [ ] 2.1 Write the delta spec for `harness/regression-suite` (scheduled run, report location, failure signal). Verified by `openspec validate decide-unattended-regression-run --strict`.
- [ ] 2.2 Add the scheduled task script and a fake test. Verified by a Python test in `harness/tests/`.
- [ ] 2.3 Run it once for real while the desktop is unlocked. Verified by a run id and a `report.json`.
- [ ] 2.4 Update `CHANGELOG.md` and the skill `harness-run-scenario`. Verified by review.

## 3. If the user chooses no schedule
- [ ] 3.1 Archive the change with the decision. Verified by review.

## 4. Close
- [ ] 4.1 Fill the test results table of the implementation pull request.
