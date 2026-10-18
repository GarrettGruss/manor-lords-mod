## 1. Move
- [ ] 1.1 Ask the user for the target place (`design.md`). Verified by the answer in `design.md`.
- [ ] 1.2 Copy `criteria.json` and the criteria tables to the target. Verified by `uv run python harness/tools/coverage.py --check-spec` on the new files.
- [ ] 1.3 Change the default paths in `harness/tools/coverage.py` and the tests. Verified by `uv run python -m unittest harness/tests/test_coverage.py`.
- [ ] 1.4 Check that `openspec archive` keeps the data files. Verified by a dry run on a copy of the repo.

## 2. Docs
- [ ] 2.1 Update `CONTRIBUTING.md` (the exception for spec 10), the skill `harness-coverage` and the wiki page on coverage. Verified by `wiki.py check` and review.
- [ ] 2.2 Add the change to `CHANGELOG.md` under Changed. Verified by review.

## 3. Close
- [ ] 3.1 Fill the test results table of the implementation pull request.
