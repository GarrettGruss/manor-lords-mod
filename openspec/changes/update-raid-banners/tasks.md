## 1. Check
- [ ] 1.1 Confirm in the code how the game year number and the year length are read (the yearly raid rule of `update-raid-clock-yearly` has them). Notes in `notes/year-start.md`.

## 2. Code
- [ ] 2.1 Remove the daily countdown from `minor_raid_step`. Show one banner 30 game days before a subjugation raid and a player (large) raid, with the target type and the size estimate. Keep a flag in ModState so it shows once and not again after a load.
- [ ] 2.2 Remove `prompt_step`, `last_prompt_day` and `prompt_every_days`.
- [ ] 2.3 Replace the random clock length with `great_raid.start_year` (default 10). Remove `min_days` and `max_days`. Replace `banner_every_days` in `clock_step` with one banner at the start of years 7, 8 and 9. Keep the last banner year in ModState so a load does not repeat it.
- [ ] 2.4 Keep `invasion_pick_difficulty` and `invasion_set_difficulty` as commands.

## 3. Tests
- [ ] 3.1 Fake game tests in `harness/tests/test_fakegame_invasion.py`: no yearly small raid banner, one 30 day banner for a subjugation raid (vassal and stand-in) and a player raid, no difficulty banner, 3 clock banners (years 7, 8, 9) and none in year 10, no repeat after a load.
- [ ] 3.2 Update the test scenarios `first_raid.py` and `subjugation_raid.py` (one banner, 30 days before), `difficulty_pick.py` and `great_raid_clock.py` (fixed end year).
- [ ] 3.3 Run the full test set and `openspec validate update-raid-banners --strict`.

## 4. Close
- [ ] 4.1 Update `docs/wiki/architecture/invasion-features.md`, the affected skills and `CHANGELOG.md`.
- [ ] 4.2 Archive the change as the last commit.
