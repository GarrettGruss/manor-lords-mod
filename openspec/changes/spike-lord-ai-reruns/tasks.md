## 1. Reruns
- [ ] 1.1 Run the suite `lord-village-ab` fully, one game at a time. Verified by `report.json` and run ids.
- [ ] 1.2 Run the probe `probe-lord-diplomacy`. Verified by a run id and `notes/baron-diplomacy.md`.
- [ ] 1.3 Run the suite `battlefield-anchor-ab` with 3 runs per side, and check a raid challenge. Verified by `report.json` (distance to the manor in a range).
- [ ] 1.4 Run a scenario that uses `ctx.run_until` in game time. Verified by a real run and `harness/tests/test_runlib_waiting.py` for any new rule.

## 2. Close
- [ ] 2.1 Write the results to `notes/`. Verified by review.
- [ ] 2.2 Update the wiki pages on lord AI and `CHANGELOG.md` where a fact changed. Verified by `wiki.py check`.
- [ ] 2.3 Fill the test results table of the implementation pull request.
