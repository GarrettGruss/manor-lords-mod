## 1. Check
- [ ] 1.1 Read `TemporalComponent.Season` in the real game at the four season starts (notes in `notes/season-values.md`). Confirm which values are spring and fall.

## 2. Code
- [ ] 2.1 Remove `show_countdown` and the warning banner from `minor_raid_step`. Remove the warning time keys if no feature reads them.
- [ ] 2.2 Remove `prompt_step`, `last_prompt_day` and `prompt_every_days`.
- [ ] 2.3 Replace `banner_every_days` in `clock_step` with a season trigger: one banner at spring and one at fall. Keep the last banner season in ModState so a load does not repeat it.
- [ ] 2.4 Keep `invasion_pick_difficulty` and `invasion_set_difficulty` as commands.

## 3. Tests
- [ ] 3.1 Fake game tests in `harness/tests/test_fakegame_invasion.py`: no minor raid banner, no difficulty banner, 6 clock banners in 3 years, no repeat after a load.
- [ ] 3.2 Update the test scenarios `first_raid.py` (no countdown check), `difficulty_pick.py` and `great_raid_clock.py`.
- [ ] 3.3 Run the full test set and `openspec validate update-raid-banners --strict`.

## 4. Close
- [ ] 4.1 Update `docs/wiki/architecture/invasion-features.md`, the affected skills and `CHANGELOG.md`.
- [ ] 4.2 Archive the change as the last commit.
