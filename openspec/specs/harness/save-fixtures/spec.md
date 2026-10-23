# harness/save-fixtures Specification

## Purpose
Fixtures give every run a known start save. The harness installs a fixture into the user save folder under a free slot name, lets the game load it, and removes it again without touching the user's own saves.

## Requirements

### Requirement: Fixtures are listed in a manifest
The manifest `harness/fixtures/fixtures.json` SHALL list each fixture with its description, origin, tags and the SHA-256 of each file. The save files SHALL be stored in `harness/fixtures/saves/<name>/` under the stem `slot`, and git SHALL ignore that folder. The default fixture SHALL be `base-corpse-pit`, and it SHALL carry the tag `default`.

#### Scenario: The manifest is valid
- **WHEN** the manifest in the repo is read
- **THEN** it is valid and holds hashes and no save data
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A stored file changed
- **WHEN** a stored fixture file no longer matches its hash
- **THEN** the harness refuses to use it
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: The default fixture
- **WHEN** a run names no fixture
- **THEN** it loads `base-corpse-pit`, the only fixture with the tag `default`
- Checked by `harness/tests/test_runlib_fixtures.py`.

### Requirement: A fixture is installed under a free slot
The harness SHALL copy the fixture files to the slot `saveGame_<max+1>` in the user save folder, above the highest existing slot. It SHALL rewrite `saveSlot` and `saveName` in the descriptor. It SHALL write the ledger entry first and each file with its hash. It SHALL never overwrite a file.

#### Scenario: Install
- **WHEN** a fixture is installed
- **THEN** only new files are written and the ledger lists each file with its SHA-256
- Checked by `harness/tests/test_runlib_saveslots.py`.

#### Scenario: A target exists
- **WHEN** a file of the target slot already exists
- **THEN** the install is refused
- Checked by `harness/tests/test_runlib_saveslots.py`.

#### Scenario: A save with no descriptor
- **WHEN** a save file has no `_descr.sav` next to it
- **THEN** the install is refused
- Checked by `harness/tests/test_runlib_saveslots.py`.

### Requirement: Uninstall deletes only unchanged ledger files
The harness SHALL delete an installed file only when its hash still matches the ledger. A changed or missing file SHALL be reported and SHALL NOT be deleted. Every change of the ledger or the save folder SHALL take the shared saves lock.

#### Scenario: A file changed after install
- **WHEN** an installed file was changed
- **THEN** the uninstall reports it and keeps the file
- Checked by `harness/tests/test_runlib_saveslots.py`.

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
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: Another slot installs a fixture slot
- **WHEN** a ledger entry of a run whose game still runs adds or keeps its files in the folder
- **THEN** the guard does not report those files
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A user save or the menu save changes
- **WHEN** an existing `saveGame_<n>` file or `menu.sav` changes, even while other slots run
- **THEN** the guard reports it
- Checked by `harness/tests/test_runlib_fixtures.py`.

### Requirement: Slots from an earlier run are removed
At the start of a run the harness SHALL remove the slots that an earlier run left (for example with `--keep-open`), using the ledger. It SHALL remove only the entries of its own game slot, and the entries whose game no longer runs. It SHALL keep the entries whose game still runs in another game slot.

#### Scenario: A leftover slot
- **WHEN** the ledger holds a slot of an earlier run
- **THEN** preflight removes its files before it installs the new slot
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A kept-open run on another slot
- **WHEN** the ledger holds a slot of a `--keep-open` run on game slot 0, its harness process has ended, and its game still runs
- **THEN** preflight of a run on game slot 1 keeps the slot and its files
- Checked by `harness/tests/test_runlib_saveslots.py`.

#### Scenario: A leftover slot of the same game slot
- **WHEN** the ledger holds a slot of an earlier run on the same game slot as the new run
- **THEN** preflight removes it, because the new run stops that game first
- Checked by `harness/tests/test_runlib_saveslots.py`.

#### Scenario: The game of a ledger entry is gone
- **WHEN** the ledger holds a slot of another game slot and no game process runs under its game folder
- **THEN** preflight removes its files
- Checked by `harness/tests/test_runlib_saveslots.py`.

#### Scenario: An old ledger entry without a game slot
- **WHEN** a ledger entry has no game slot field
- **THEN** it counts as left over and is removed
- Checked by `harness/tests/test_runlib_saveslots.py`.

### Requirement: The start can be a save file or a new game
`run.py` SHALL accept `--fixture NAME`, `--save PATH.sav` or `--new-game [--map NAME]`. A `--save` file SHALL be installed like a stored fixture. A new game SHALL install nothing. A new game SHALL be refused together with `--save` or `--fixture`.

#### Scenario: A save file
- **WHEN** a run starts with `--save` and a save file
- **THEN** the file is installed under its own label and removed at the end
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: A new game
- **WHEN** a run starts with `--new-game`
- **THEN** no fixture is needed and nothing is installed
- Checked by `harness/tests/test_runlib_fixtures.py`.

### Requirement: The fixture tool manages fixtures
`harness/tools/fixtures.py` SHALL offer `list`, `import`, `record`, `uninstall` and `remove --appdata`. It SHALL delete only a folder named `appdata` that holds `ManorLords/Saved`. Exit codes SHALL be 0 done, 1 fixture or slot error, 3 a file in the user folder changed during a read.

#### Scenario: A wrong folder
- **WHEN** `remove --appdata` names a folder not called `appdata`
- **THEN** the tool refuses and deletes nothing
- Checked by `harness/tests/test_runlib_fixtures.py`.

#### Scenario: Import a save
- **WHEN** `import` copies a user slot or a save file
- **THEN** the files are stored under the stem `slot` and the manifest holds their hashes
- Checked by `harness/tests/test_runlib_fixtures.py`.

### Requirement: A game can be opened on a fixture
`harness/tools/load_save.py` SHALL start the game on a fixture, a save file or a new game, leave it open and paused, and pass extra arguments to `run.py`.

#### Scenario: Open on a fixture
- **WHEN** a user runs `load_save.py NAME`
- **THEN** it runs the scenario `noop` with `--keep-open` and that fixture
- Not checked yet.
