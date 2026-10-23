# Real game runs

All with `--max-runs 1000`, fixture `base-corpse-pit`, no other game running.

| Test scenario | Run id | Verdict |
|---|---|---|
| invasion-first-raid | 20261023-032413-9785 | pass |
| invasion-first-raid, INVASION_SIZE=large | 20261023-033206-1b6d | pass |
| invasion-first-raid, `--pak raidmenu`, INVASION_MENU_SHOT=1 | 20261023-035614-b4eb | pass (picture) |
| invasion-subjugation-raid | 20261023-033954-9669 | pass (banner picture missed: it had faded) |
| invasion-subjugation-raid, `--pak raidmenu` | 20261023-034826-2cea | pass (pictures) |
| invasion-difficulty-pick | 20261023-040408-e9c9 | pass |
| invasion-great-raid-clock | 20261023-040503-6bd7 | fail: no "clock start" log line |
| invasion-great-raid-clock (fixed) | 20261023-040646-bdac | pass |
| invasion-raid-widget, `--pak raidmenu` | 20261023-040750-e55e | pass |
| scenario-settings-great-raids-off, `--pak raidmenu` | 20261023-040832-0cfb | pass (picture) |

Findings:
- The default fixture `base-corpse-pit` is a save made with the mod, so its ModState already holds the great raid clock. The clock start line is not logged. `great_raid_clock.py` now reads the clock from the state in that case (the start year check applies only when the line exists).
- The banner fades in a few seconds. `subjugation_raid.py` now runs live and takes the picture when the banner line appears.
- `test_install_scripts` passes with no game running (5 tests).
- The fixture clock end day came from the old random clock rule, not the new year 10 rule; not a defect of this change.
