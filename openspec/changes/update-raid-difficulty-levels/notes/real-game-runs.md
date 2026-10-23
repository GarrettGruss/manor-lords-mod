# Real game runs still needed (not run: another agent uses the game)

Before the runs: rebuild `raidmenu_P.pak` with the new `make_scenario_settings_widget.py` (five rows, four choices) and copy it to `mod/InvasionMod/paks/`. Back up the save folder first. Use `--max-runs 1000`. In Git Bash set `MSYS_NO_PATHCONV=1`.

Commands (`uv run python harness\run.py ...`):

1. New game menu, with screenshots `menu-defaults`, `menu-changed`, `after-begin` (task 3.3; copy them to `evidence/` and list them in `evidence/README.md`):
   `--scenario scenario-settings-new-game-menu --new-game --pak raidmenu --slot N --max-runs 1000`
2. Level 0 great raid on a fixture: `--scenario scenario-settings-great-raids-off --slot N --max-runs 1000`
3. Levels by command: `--scenario invasion-difficulty-pick --max-runs 1000` (also with `--env INVASION_DIFFICULTY=1` and `=3`)
4. Subjugation raid at vassal level 1: `--scenario invasion-subjugation-raid --env INVASION_DIFFICULTY=1 --max-runs 1000`
5. Great raid waves and relief army: `--scenario invasion-great-raid-waves --env INVASION_DIFFICULTY=1 --max-runs 1000` (long run, one slot)
6. Raid widget lines: `--scenario invasion-raid-widget --max-runs 1000`
7. Save and load keeps the five values: `--scenario scenario-settings-load-keeps-settings --new-game --pak raidmenu --env SETTINGS_PART=save` then `--save <slot>` (first real `save_game` use for this scenario: fresh save backup, owner informed).

## Results (2026-10-23, slot 1, pak rebuilt)
- `levels-newgame-1` new game menu: pass (pictures in `evidence/`).
- `levels-invasion-difficulty-pick-1` (default 2): pass. Variants `=1` and `=3`: not run (see below).
- `levels-scenario-settings-great-raids-off-1`: pass.
- `levels-invasion-subjugation-raid-1` and `-2`: harness_error, `invasion_set_raid_days refused: no subjugation raid is planned`. The season rule plans the raid 12 to 20 days ahead and the first raid lasted longer, so the subjugation raid spawned first (scenario timing, also possible on main). Fix: the scenario moves the raid day to 45 days after the plan. `-3`: pass.
- `levels-great-raid-waves-1`, `levels-great-raid-clock-1`: started, then the batch was stopped by Claude Code because the system was low on memory. No verdict.
- Not run: `invasion-first-raid`, `invasion-raid-widget --pak raidmenu`, difficulty-pick with `INVASION_DIFFICULTY=1` and `=3`, `scenario-settings-load-keeps-settings`.
- The save folder gained `saveGame_52*` during the session (not made by these runs, which save nothing); no existing file changed.
