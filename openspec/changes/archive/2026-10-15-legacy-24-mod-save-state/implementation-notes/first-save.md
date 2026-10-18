# First real guarded harness save (spec 24, plan step 2, A0)

Date: 2026-10-15 (local time). Issue #128.

## Before the run
- The main session made a verified backup of the real save folder: `runs/manual-save-backup-20261015-223600` (314 files, hashes in the `.sha256` next to it).
- The ledger `runs/.installed-slots.json` held one stale entry: `saveGame_47` (a harness copy of the `base` fixture from an earlier run, 8 files).
  Its hashes matched the ledger. It was removed with `saveslots.uninstall_all` (the normal harness cleanup). The real folder then had 306 files.
  The 8 removed files are the only difference to the manual backup for the whole spike.
- `saveGame_48` (8 files) is not in the ledger and is in the backup. It was there before this work. It was left alone. It made the fixture install use slot 49.
- The game was closed. `~mods` does not exist (nothing to empty).

## Run `20261016-033725-80ea` (scenario `probe-save-first`, hidden, keep=False)
- Verdict: pass. The fixture `base` was installed as `saveGame_49` and loaded. One call: `ctx.actions.save_game("first", keep=False)`.
- Slot chosen by the guard: `saveGame_50`. The game wrote exactly 7 files: `.sav`, `_descr.sav`, `_coat_0..4.png`. No `saveGame_50.png` (no thumbnail file).
  The guard accepted the set (`NEW_SLOT_FILE`). Folder count 314 -> 321.
- Backup made by the guard: `runs/save-backups/saves-20261015-223807`.
- Summary notes: `installed slot saveGame_49 removed (8 files)`, `harness save saveGame_50 removed (7 files)`, `the user's save files did not change`.
- After the run: the real folder equals the manual backup, except the 8 `saveGame_47` files (see above). No file changed. No extra file. The ledger is empty.
- Answer to the open question: the caller chooses the slot. `requestSaveFile("saveGame_50", "harness first")` wrote `saveGame_50.*`. The game did not pick another name.
  The hook of `PawnCPP:requestSaveFile` saw the same two arguments (see `persistence-tests.md`).

## Verdict
Clean. A0 is met: fake tests exist (earlier) and one real save left the other saves unchanged.
