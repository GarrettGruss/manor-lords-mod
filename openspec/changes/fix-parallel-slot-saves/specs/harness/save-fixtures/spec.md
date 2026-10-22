## MODIFIED Requirements
<!-- Issue: #393 -->

### Requirement: The user save folder is guarded
The harness SHALL hash the user save folder before and after each run. If any file changed, other than the installed or kept slot, the phase `teardown` SHALL fail with the message that the user's save files changed. Preparation of a fixture SHALL only read the user folder and SHALL abort when a file changes during the read. The guard SHALL ignore the settings file that the game rewrites (`rtsSettings.sav`) and the files of ledger entries whose game still runs in another game slot. It SHALL NOT ignore any other file: a `saveGame_<n>` file that existed before the run and `menu.sav` stay guarded.

#### Scenario: A user file changed during the run
- **WHEN** a user save file differs from the preflight snapshot at teardown
- **THEN** teardown fails loudly and the private appdata is still removed
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A file changes during a copy
- **WHEN** a source file changes while the harness copies it
- **THEN** the preparation aborts and copies nothing
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: Another slot rewrites the settings file
- **WHEN** the game of another slot changes `rtsSettings.sav` while a run is in preflight or running
- **THEN** the guard does not report it, also when the harness settings are not installed
- Checked by `harness/tests/test_runlib_fixtures.py` (planned).

#### Scenario: Another slot installs a fixture slot
- **WHEN** a ledger entry of a run whose game still runs adds or keeps its files in the folder
- **THEN** the guard does not report those files
- Checked by `harness/tests/test_runlib_fixtures.py` (planned).

#### Scenario: A user save or the menu save changes
- **WHEN** an existing `saveGame_<n>` file or `menu.sav` changes, even while other slots run
- **THEN** the guard reports it
- Checked by `harness/tests/test_runlib_fixtures.py` (planned).

### Requirement: Slots from an earlier run are removed
At the start of a run the harness SHALL remove the slots that an earlier run left (for example with `--keep-open`), using the ledger. It SHALL remove only the entries of its own game slot, and the entries whose game no longer runs. It SHALL keep the entries whose game still runs in another game slot.

#### Scenario: A leftover slot
- **WHEN** the ledger holds a slot of an earlier run
- **THEN** preflight removes its files before it installs the new slot
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A kept-open run on another slot
- **WHEN** the ledger holds a slot of a `--keep-open` run on game slot 0, its harness process has ended, and its game still runs
- **THEN** preflight of a run on game slot 1 keeps the slot and its files
- Checked by `harness/tests/test_runlib_saveslots.py` (planned).

#### Scenario: A leftover slot of the same game slot
- **WHEN** the ledger holds a slot of an earlier run on the same game slot as the new run
- **THEN** preflight removes it, because the new run stops that game first
- Checked by `harness/tests/test_runlib_saveslots.py` (planned).

#### Scenario: The game of a ledger entry is gone
- **WHEN** the ledger holds a slot of another game slot and no game process runs under its game folder
- **THEN** preflight removes its files
- Checked by `harness/tests/test_runlib_saveslots.py` (planned).

#### Scenario: An old ledger entry without a game slot
- **WHEN** a ledger entry has no game slot field
- **THEN** it counts as left over and is removed
- Checked by `harness/tests/test_runlib_saveslots.py` (planned).
