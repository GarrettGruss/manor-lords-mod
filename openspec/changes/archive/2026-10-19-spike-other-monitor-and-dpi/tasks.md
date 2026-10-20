## 1. Screenshots
- [-] 1.1 Take screenshots with the game on a second monitor. Verified by pictures in `evidence/` and a run id. Cancelled: change abandoned by owner decision, 2026-10-20.
- [-] 1.2 Take a screenshot with a minimized game window. Verified by the run summary (the launcher must report it, not hide it). Cancelled: change abandoned by owner decision, 2026-10-20.
- [-] 1.3 Take a screenshot while a message banner is on screen. Verified by a picture in `evidence/`. Cancelled: change abandoned by owner decision, 2026-10-20.

## 2. Mouse placement and tiles
- [-] 2.1 Run `place_building` at a second DPI scale and window size. Verified by a real game run and `harness/tests/test_runlib_osinput.py` for any new rule. Cancelled: change abandoned by owner decision, 2026-10-20.
- [-] 2.2 Check the window tile of slots on the second screen. Verified by a run with `--slots 2` and a picture. Cancelled: change abandoned by owner decision, 2026-10-20.

## 3. Close
- [-] 3.1 Write `notes/monitor-dpi-findings.md` with the limits. Verified by review. Cancelled: change abandoned by owner decision, 2026-10-20.
- [-] 3.2 Update the skill `harness-run-scenario` and `CHANGELOG.md` if the advice changes. Verified by review. Cancelled: change abandoned by owner decision, 2026-10-20.
- [-] 3.3 Fill the test results table of the implementation pull request. Cancelled: change abandoned by owner decision, 2026-10-20.
