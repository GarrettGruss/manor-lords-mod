# harness/game-slots Specification

## Purpose
Game slots let several copies of the game run at the same time, for A/B tests and parallel suites. The scripts `install.ps1` and `uninstall.ps1` build the slots and change the game settings in a way that can be undone.

## Requirements

### Requirement: Install backs up and sets the harness settings
`harness/install.ps1` SHALL refuse to run while a game runs. It SHALL copy `GameUserSettings.ini`, `UserSettings.ini` and `rtsSettings.sav` to `slots/.install/backup/` with their SHA-256, once. A second install SHALL keep the first backup. It SHALL write the state file before the first change and SHALL set the harness values (lowest quality, windowed 1280x720, 30 fps, no VSync) while other keys stay.

#### Scenario: Harness values and other keys
- **WHEN** the install runs
- **THEN** the harness values are set and the other keys, such as key bindings, stay
- Checked by `harness/tests/test_install_scripts.py`.

#### Scenario: A second install
- **WHEN** the install runs again
- **THEN** the first backup is kept
- Checked by `harness/tests/test_install_scripts.py`.

### Requirement: Uninstall restores the user files
`harness/uninstall.ps1` SHALL restore the user files from the backup and check their hashes. A backup that changed since the install SHALL not be restored and SHALL be an error. A file that did not exist before the install SHALL be removed. Only a full verified restore SHALL delete the backup.

#### Scenario: The game changed the files
- **WHEN** the game changed the settings files after the install
- **THEN** the uninstall restores them bit for bit
- Checked by `harness/tests/test_install_scripts.py`.

#### Scenario: Another game folder
- **WHEN** the uninstall runs for another game folder than the install
- **THEN** it leaves the state alone
- Checked by `harness/tests/test_install_scripts.py`.

### Requirement: Uninstall never reaches the game folder
By default `uninstall.ps1` SHALL delete the switch file `ue4ss/harness/autoboot.enable` and disable the harness mods in `mods.txt`. With `-Remove` it SHALL also delete the files in the deploy manifest, the pak files whose hash still matches, the folders `ue4ss/bridge` and `ue4ss/harness`, and the slot folders. It SHALL remove junctions as links first. It SHALL refuse a path outside `-GameDir` and SHALL never touch UE4SS itself, `dwmapi.dll` or saves.

#### Scenario: Remove with slots
- **WHEN** `-Remove` runs on a game folder with slots
- **THEN** the slots are removed and no file of the game folder is deleted
- Checked by `harness/tests/test_install_scripts.py`.

### Requirement: Slots are separate game copies
`install.ps1 -Slots N` SHALL build `slots/<n>/Manor Lords/` for each new slot, up to slot 3. A slot SHALL have its own copy of `Win64` with its mods and its own `Content/Paks` with an empty `~mods`. `Engine`, plugins, movies and slate SHALL be junctions to the game folder, and the game paks SHALL be hard links. Slot 0 SHALL be the normal game folder. Each slot SHALL be added to `slots.json` after it is built, and the deploy SHALL run for it.

#### Scenario: A slot has its own mods
- **WHEN** a slot is built
- **THEN** it has its own `Win64` and an empty `~mods`
- Checked by `harness/tests/test_install_scripts.py`.

#### Scenario: Slot list from the state file
- **WHEN** `slots.json` lists slots with an existing exe
- **THEN** `installed_slots()` returns slot 0 and those slots in order, and a slot with a missing exe is left out
- Checked by `harness/tests/test_parallel_slots.py`.

#### Scenario: No state file
- **WHEN** no state file exists
- **THEN** only slot 0 is installed
- Checked by `harness/tests/test_parallel_slots.py`.

#### Scenario: An unknown slot
- **WHEN** a slot number is not installed, or the state file is broken
- **THEN** the harness fails with a clear error
- Checked by `harness/tests/test_parallel_slots.py`.

### Requirement: A run picks a slot and locks it
`run.py --slot N|auto` SHALL run the game of slot N. With `auto` it SHALL take the first installed slot with no live lock. Each slot SHALL have its own run lock. A busy explicit slot SHALL fail with an error that names the slot. When all slots are busy, `auto` SHALL fail. A text that is not a number from 0 to 3 or `auto` SHALL be refused.

#### Scenario: Auto skips a locked slot
- **WHEN** slot 0 is locked and slot 1 is free
- **THEN** `auto` takes slot 1
- Checked by `harness/tests/test_parallel_slots.py`.

#### Scenario: All slots busy
- **WHEN** every installed slot is locked
- **THEN** `auto` fails with a clear error
- Checked by `harness/tests/test_parallel_slots.py`.

#### Scenario: A busy explicit slot
- **WHEN** the asked slot is locked by a live run
- **THEN** the error names the slot
- Checked by `harness/tests/test_parallel_slots.py`.

### Requirement: Locks and counters are shared by worktrees
The run locks, the run counter and the save ledger SHALL live in the main checkout, so all git worktrees share them. Many processes SHALL be able to count runs without losing a count. A lock whose file is being deleted SHALL count as taken, and a release SHALL retry a blocked delete.

#### Scenario: Many processes count
- **WHEN** many processes bump the run counter at once
- **THEN** no count is lost and none crashes
- Checked by `harness/tests/test_parallel_slots.py`.

### Requirement: Games do not read the save list while another run changes it
The launcher SHALL hold a saves scan lock from the launch of a game until its boot leaves `WAITING_FOR_MENU`, for at most 90 seconds. The lock SHALL be free after a failed boot.

#### Scenario: Menu lock
- **WHEN** a game sits in the menu
- **THEN** the lock is held, and it is free after the boot leaves the menu
- Checked by `harness/tests/test_parallel_slots.py`.

#### Scenario: A game stuck in the menu
- **WHEN** the game stays in the menu past the limit
- **THEN** the lock is freed after the limit
- Checked by `harness/tests/test_parallel_slots.py`.

### Requirement: The save guard knows the installed settings
While the settings are installed, the user-save guard of a run SHALL leave out `rtsSettings.sav`, and SHALL leave out every harness file. Without the install, that file SHALL count.

#### Scenario: Settings installed
- **WHEN** `settings.json` exists
- **THEN** `rtsSettings.sav` is not in the guarded user files
- Checked by `harness/tests/test_parallel_slots.py`.

### Requirement: Each slot has its own window tile
Each slot SHALL have a fixed screen tile for its 1280x720 window: slot 0 at the top left, then top right, bottom left and bottom right.

#### Scenario: Tile of slot 1
- **WHEN** slot 1 starts
- **THEN** its window goes to x 1280, y 0
- Not checked yet.
