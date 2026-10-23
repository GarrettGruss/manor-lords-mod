# Implementation notes

- `saveslots.uninstall_all(save_dir, ledger_path, game_slot)` follows the three rules of design.md. `phases` passes `ctx.config["slot"]` (0 for a fake run).
- `Installed` and `install` take `game_slot` and `game_root`. `record_saved` does not (old-entry rule).
- `rtsSettings.sav` is in `gameslots.GAME_REWRITTEN_SAVE_FILES` and always ignored.
- Task 3.2 (real run on 3 slots) is not done: it needs the game. Commands are in the lead's hand-off.
