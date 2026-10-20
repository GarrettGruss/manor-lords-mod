## 1. Decision
- [x] 1.1 Ask the user the three questions in `design.md`. Verified by the answers written in `design.md`.

## 2. If the user chooses a schedule
- [x] 2.1 (not needed: no schedule) Write the delta spec for `harness/regression-suite` (scheduled run, report location, failure signal). Verified by `openspec validate decide-unattended-regression-run --strict`.
- [x] 2.2 (not needed: no schedule) Add the scheduled task script and a fake test. Verified by a Python test in `harness/tests/`.
- [x] 2.3 (not needed: no schedule) Run it once for real while the desktop is unlocked. Verified by a run id and a `report.json`.
- [x] 2.4 (not needed: no schedule) Update `CHANGELOG.md` and the skill `harness-run-scenario`. Verified by review.

## 3. If the user chooses no schedule
- [x] 3.1 Archive the change with the decision. Verified by review.

## 4. Close
- [x] 4.1 Fill the test results table of the implementation pull request.
