## 1. Investigation
- [x] 1.1 Re-read `soak-results.md` and `open-items.md` and write `notes/soak-plan.md`. Verified by review.
- [x] 1.2 Run `soak-days` with extra samples (units, buildings, clock rate). Verified by a real run and its `telemetry.jsonl`.
- [x] 1.3 Try a way to keep the village alive (feed, approval, fewer raiders). Verified by a real run that reaches more than 333 days.

## 2. Decision and result
- [x] 2.1 Ask the user the questions in `design.md`. Verified by the answers in `design.md`.
- [x] 2.2 If the user wants a periodic raid, add it to the soak scenario. Verified by a fake game test and a real run. Not needed: the owner decided no periodic raid.
- [x] 2.3 Run the chosen soak once in the real game. Verified by a run id: no crash, memory range, clock rate range.
- [ ] 2.4 Update criterion Q1 in `criteria.json` only if its state changes. Verified by `uv run python harness/tools/coverage.py --check-spec`.

## 3. Close
- [x] 3.1 Update `CHANGELOG.md` if a scenario changes. Verified by review.
- [ ] 3.2 Fill the test results table of the implementation pull request.
