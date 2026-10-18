## 1. Build
- [x] 1.1 Add the log call in `mod/UEBridge/scripts/main.lua` as a marked patch, and list it in `vendor/ue4ss-bridge/PATCHES.md`. Verified by review of the diff.
- [x] 1.2 Write the fake game test for the three spec scenarios. Verified by `uv run python -m unittest harness/tests/test_fakegame_uebridge.py`.
- [x] 1.3 Check that no property value or Lua source reaches the log. Verified by the eval scenario of the test.

## 2. Real game
- [ ] 2.1 Run one smoke test scenario with the bridge and read `mod.log`. Verified by a run id and the log lines.

## 3. Close
- [x] 3.1 Update `CHANGELOG.md`, the wiki page on the bridge, and the skill `harness-debug-run` (the log is a new place to look). Verified by `wiki.py check`.
- [ ] 3.2 Fill the test results table of the implementation pull request.
