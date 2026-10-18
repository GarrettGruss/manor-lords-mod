# Spec Delta

## Purpose

The guarded action `save_game` lets a test scenario make one save into the user's real save folder without any risk to the user's own saves. It is the only allowed way for the harness to call a game save function.

## ADDED Requirements

### Requirement: Only one file calls a save function
Only `mod/shared/HarnessSave/HarnessSave.lua` SHALL call a game save function. It SHALL contain exactly one call, and the command `save_game` SHALL be registered only in the helper mod `HarnessActions`. A player mod and a probe SHALL NOT call a save function.

#### Scenario: A save call elsewhere
- **WHEN** any code file other than the allow-listed one names a save function call
- **THEN** the test fails
- Checked by `harness/tests/test_save_call_sites.py`.

#### Scenario: The allow-listed file
- **WHEN** the file `HarnessSave.lua` is scanned
- **THEN** it has exactly one call
- Checked by `harness/tests/test_save_call_sites.py`.

### Requirement: The Lua side refuses unsafe requests
`HarnessSave` SHALL accept only a slot that matches `^saveGame_%d+$` and a name of letters, digits, space, `-` and `_` up to 40 characters. It SHALL refuse a slot that exists. It SHALL refuse the save when the existence check cannot run (fail closed). It SHALL fail when the player pawn is not loaded.

#### Scenario: A free slot
- **WHEN** the request names a free slot
- **THEN** the save runs once
- Checked by `harness/tests/test_fakegame_harnesssave.py`.

#### Scenario: An existing slot
- **WHEN** the slot already exists
- **THEN** the save is refused and nothing is saved
- Checked by `harness/tests/test_fakegame_harnesssave.py`.

#### Scenario: A bad slot or name
- **WHEN** the slot or the name does not match its pattern
- **THEN** the request is refused
- Checked by `harness/tests/test_fakegame_harnesssave.py`.

### Requirement: The slot and the label are chosen safely
`ctx.actions.save_game(label, keep=False)` SHALL accept a label of letters, digits, space, `-` and `_` up to 40 characters. It SHALL choose the slot `saveGame_<max+1>`, one above the highest slot, and SHALL refuse when any file of that slot exists before it calls the game.

#### Scenario: The next slot
- **WHEN** the folder holds slots up to `saveGame_7`
- **THEN** the chosen slot is `saveGame_8`
- Checked by `harness/tests/test_runlib_harness_save.py`.

#### Scenario: A bad label
- **WHEN** the label has a character that is not allowed
- **THEN** the action is refused before any backup or call
- Checked by `harness/tests/test_runlib_harness_save.py`.

### Requirement: A backup comes first
Before the save call, the harness SHALL copy the whole save folder to a backup folder outside the game folder and check the copy by hash. It SHALL keep the 5 newest backups. It SHALL take the shared saves lock for the whole action.

#### Scenario: A backup is made first
- **WHEN** the action runs
- **THEN** a verified backup of the whole folder exists before the game is asked to save
- Checked by `harness/tests/test_runlib_harness_save.py`.

#### Scenario: Old backups
- **WHEN** more than 5 backups exist
- **THEN** only the 5 newest stay
- Checked by `harness/tests/test_runlib_harness_save.py`.

### Requirement: Any change to an old save is undone
After the save, the harness SHALL wait up to 30 seconds until `<slot>.sav` exists and the folder is stable for two polls. Only files of the new slot SHALL be new. If an existing file changed or vanished, or an unexpected file appeared, the harness SHALL restore the changed or removed files from the backup and raise a save guard error.

#### Scenario: A changed old file
- **WHEN** an existing save file changed during the save
- **THEN** it is restored from the backup and the action fails
- Checked by `harness/tests/test_runlib_harness_save.py`.

#### Scenario: The file never appears
- **WHEN** the new slot file does not appear in 30 seconds
- **THEN** the action fails with a timeout error and the folder is checked
- Checked by `harness/tests/test_runlib_harness_save.py`.

#### Scenario: The game refuses
- **WHEN** the game command is refused
- **THEN** the action fails and the folder is unchanged
- Checked by `harness/tests/test_runlib_harness_save.py`.

### Requirement: The new save is cleaned up unless kept
Unless `keep=True`, the harness SHALL put the files of the new slot in the slot ledger, so the end of the run deletes them. With `keep=True` the files SHALL stay and the end-of-run guard SHALL accept them. The action SHALL return the slot name.

#### Scenario: A save without keep
- **WHEN** a scenario saves without `keep`
- **THEN** the slot files are in the ledger and are deleted at the run end
- Checked by `harness/tests/test_runlib_harness_save.py`.

#### Scenario: A kept save
- **WHEN** a scenario saves with `keep=True`
- **THEN** the files stay and are not in the ledger
- Checked by `harness/tests/test_runlib_harness_save.py`.

### Requirement: The save action can be missing
When no saver is available, the action SHALL report that it is not possible, and a guard error SHALL become an action error.

#### Scenario: No saver
- **WHEN** a scenario calls `save_game` and no saver is wired
- **THEN** the action is reported as not possible
- Checked by `harness/tests/test_runlib_harness_save.py`.
