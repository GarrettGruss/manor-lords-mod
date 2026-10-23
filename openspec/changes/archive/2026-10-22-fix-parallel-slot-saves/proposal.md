## Why

Parallel game slots (spec 11) break two rules of `harness/save-fixtures`. Issues #393 and #378 describe them. Both were seen on 2026-10-22 with 3 slots.

1. A run on slot 1 removed the fixture slot `saveGame_51` that a `--keep-open` run on slot 0 had installed and still used (#378). The preflight removes every ledger slot whose owner process is gone. A `--keep-open` run ends its harness process but leaves the game running, so the owner check says "left over".
2. A run on slot 1 and a run on slot 2 aborted in preflight with "files in the user's save folder changed: rtsSettings.sav" (run 20261022-025243-51f5). The game of another slot rewrites `rtsSettings.sav` at any time. The guard ignores that file only when the harness settings are installed.

## What changes

- A ledger entry records the game slot of its run. A run removes a leftover slot only if the entry belongs to its own game slot, or if no game process runs under the game folder of the entry.
- The save folder guard always ignores the settings file that the game rewrites (`rtsSettings.sav`) and the files of ledger entries whose game still runs. It stays strict for every other file: `saveGame_<n>` files that existed before the run, and `menu.sav`.

## Impact

- Spec `harness/save-fixtures`: two requirements are modified ("The user save folder is guarded", "Slots from an earlier run are removed").
- Code (in the implementation pull request): `harness/runlib/saveslots.py`, `harness/runlib/phases.py`, `harness/runlib/gameslots.py`.
- Issues: #393 (this change), #378 (the first problem).

## Owner decisions (2026-10-22)

- The guard always ignores `rtsSettings.sav`.
- A run removes the ledger entries of runs that no longer exist (no live game under the game folder, no live owner).
- The guard may ignore the save files of other running slots.
