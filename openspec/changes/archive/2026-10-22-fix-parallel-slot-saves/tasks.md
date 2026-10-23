## 1. Ledger

- [x] 1.1 Add `game_slot` and `game_root` to the ledger entry in `saveslots.install` (#393)
- [x] 1.2 Change `uninstall_all` to the three rules in `design.md`
- [x] 1.3 Tests in `harness/tests/test_runlib_saveslots.py` for the four new spec scenarios

## 2. Guard

- [x] 2.1 Ignore `rtsSettings.sav` always in `phases.user_files`
- [x] 2.2 Ignore the files of ledger entries whose game still runs
- [x] 2.3 Tests in `harness/tests/test_runlib_fixtures.py` for the three new spec scenarios

## 3. Check

- [x] 3.1 Run the full tests and `openspec validate fix-parallel-slot-saves --strict`
- [x] 3.2 Real run on 3 slots at once, one with `--keep-open` (result in `notes/`)
- [x] 3.3 Update `CHANGELOG.md`, the wiki and the skill `harness-run-scenario` if affected
