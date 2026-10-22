## 1. Ledger

- [ ] 1.1 Add `game_slot` and `game_root` to the ledger entry in `saveslots.install` (#393)
- [ ] 1.2 Change `uninstall_all` to the three rules in `design.md`
- [ ] 1.3 Tests in `harness/tests/test_runlib_saveslots.py` for the four new spec scenarios

## 2. Guard

- [ ] 2.1 Ignore `rtsSettings.sav` always in `phases.user_files`
- [ ] 2.2 Ignore the files of ledger entries whose game still runs
- [ ] 2.3 Tests in `harness/tests/test_runlib_fixtures.py` for the three new spec scenarios

## 3. Check

- [ ] 3.1 Run the full tests and `openspec validate fix-parallel-slot-saves --strict`
- [ ] 3.2 Real run on 3 slots at once, one with `--keep-open` (result in `notes/`)
- [ ] 3.3 Update `CHANGELOG.md`, the wiki and the skill `harness-run-scenario` if affected
