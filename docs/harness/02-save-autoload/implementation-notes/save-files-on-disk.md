# Save files on disk

Checked on 2026-10-09 by listing `%LOCALAPPDATA%\ManorLords\Saved\SaveGames` (read only).

## Slot name format (answers an open question in the spec)
Each save slot is a group of files that share one slot name:

| File | Meaning |
|---|---|
| `<slot>.sav` | The world snapshot (about 2 to 4 MB). |
| `<slot>_descr.sav` | The descriptor (about 2 KB). This is what the menu lists (`MLSaveGameDescr`). |
| `<slot>.png` | The thumbnail. |
| `<slot>_coat_<n>.png` | Coat of arms images (0 to 5 files). |

Slot names seen:
- `saveGame_<N>` for manual saves. N is a number (0, 1, 10, 11, 12, ...).
- `autosave` for the autosave. It has the same file group.
- Other files in the folder are not slots: `menu.sav` and `rtsSettings.sav` (settings and menu state).

## Consequences for the harness
- The test save is a copy of one slot, with a new slot name. The copy needs `<slot>.sav` and `<slot>_descr.sav`. The images may be optional. This is not checked.
- Never write into the user's own slots. Copy the files to a name like `harness_test` and test that the menu lists it. Not checked yet.
- The save folder is also where `menu.sav` and `rtsSettings.sav` are written by the game. The game changes them on each run (their dates were from today).

## Still unknown
- Does the game list a slot by file discovery (any `<name>_descr.sav`), or by number (`saveGame_<N>`)?
  The C++ base has `StartSlotDiscovery`, `GetFreeSlotName` and `SlotNameFromIndex(Int)`.
  A custom slot name may be ignored by the menu. Test this before building on it.
- Which `LevelName` the chosen save uses. Read it with `IoHandler:LoadGameFromSlot` at runtime.
