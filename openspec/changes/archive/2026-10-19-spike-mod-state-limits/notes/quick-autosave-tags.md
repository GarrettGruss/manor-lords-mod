# Quick save and autosave keep the pawn Tags (task 1.3)

Run `qs-autosave-1` (`run.py --scenario noop --keep-open --new-game`), 2026-10-20, with the owner at the game. Backup of the real save folder first: `SaveGames-backup-qs-20261020` (314 files). Runbook: `quicksave-autosave-runbook.md`.

## Quick save

- The quick save key writes the fixed slot `quicksave` in the real save folder: `quicksave.sav`, `quicksave_descr.sav`, `quicksave.png`, `quicksave_coat_1.png`. A second quick save overwrites it. No other save file changed.
- Marker before the quick save (mod commands `InvasionMod.mod_state_set` and `mod_state_dump`): `invasion:selftest_text=qs_quick_1`, `invasion:selftest_int=4127`, plus 17 values of the mod features.
- After the owner loaded `quicksave`: the dump shows the same 19 Tags and values. **The quick save keeps the pawn Tags.**

## Autosave timer after a load

- At READY, `autosave_status` gave `remaining_s` 31,535,356 (HarnessBoot pushed it one year away).
- After the owner loaded the quick save: `remaining_s` 590, `settings_period_s` 600. **A load restarts the game's 10 minute autosave timer. The boot protection does not survive a load.**
- `disable_autosave` (HarnessActions) pushed it away again (`remaining_s` 31,535,422).
- Consequence: in a `--keep-open` session, every load by a person brings back a real autosave about 10 minutes later. Run `disable_autosave` after each load, or accept the autosave.

## Autosave

- The agent did not change the timer (a bridge call to `SetAutosavePeriodOnPawn` with 120 s was refused by the permission system). The owner loaded `quicksave` again, so the game's own 10 minute timer ran. The marker was set to `selftest_text=qs_auto_1` before it fired.
- The game autosaved about 580 s after the load. It rewrote `autosave.sav`, `autosave_descr.sav`, `autosave.png` and `autosave_coat_1.png`. Older coat images (`autosave_coat_0`, `_2` to `_5`) stay from earlier autosaves; the game does not delete them. No other save file changed.
- After the owner loaded `autosave`: `selftest_text=qs_auto_1`, `selftest_int=4127`. Feature values that changed while the game ran before the autosave also came back (`bandits_natural_order` 100 to 90, `bandits_written_order` 50 to 40, new `last_prompt_day=8`). **The autosave keeps the pawn Tags.**
- `disable_autosave` after each load; the timer was one year away at the end.

## Verdict

Task 1.3 passes: a quick save and an autosave both keep the ModState Tags of the player pawn, the same as a menu save.

## Other observations

- `run.py` did not make `runs/<id>/commands` in this `--keep-open` run. `harness/tools/s29_command.py` failed until the empty folder was made by hand. Then HarnessActions answered.
- `rtsSettings.sav` (game settings) is rewritten at game start.

## Task 2.1: the stale slot saveGame_48

The owner said the slot can be deleted (chat, 2026-10-19); the saves are backed up. The agent deleted its 8 files on 2026-10-19 after a copy to the session scratchpad.
