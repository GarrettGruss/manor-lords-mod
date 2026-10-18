## 1. Measure
- [ ] 1.1 Add a temporary test wait (not shipped) and call it with 30, 45, 60 and 90 s in a real session. Verified by the results in `notes/mcp-timeout.md`.
- [ ] 1.2 Decide the default and the cap. Verified by the note.

## 2. Change, if needed
- [ ] 2.1 Change the default in `mcp/harness_tools` and its tests. Verified by `uv run python -m unittest discover -s harness/tests -p "test_harness_tools*.py"`.
- [ ] 2.2 Update the delta spec for `harness/agent-tools`, the skill `harness-run-scenario` and `CHANGELOG.md`. Verified by `openspec validate spike-mcp-client-timeout --strict` and review.

## 3. Close
- [ ] 3.1 Fill the test results table of the implementation pull request.
