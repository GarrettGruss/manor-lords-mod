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
