# Spec Delta

## Purpose

The mod_state feature keeps the values of the Invasion Mod inside the player's save, so that raid plans, clocks and counters come back after a load. It uses the shared module ModState.

## ADDED Requirements

### Requirement: Values are stored as Names in the pawn Tags
The mod SHALL store its values as Names in the `Tags` array of the player pawn, in the format `<mod>:<key>=<value>` (for example `invasion:raid_day=412`). The game saves and loads this array, so the values SHALL come back after a save and a load. The mod SHALL NOT call a save function.

#### Scenario: Three values survive a save and a load
- **WHEN** a test sets one integer, one boolean and one string value, makes a harness save, and loads that slot in a new run
- **THEN** `mod_state_dump` returns the same three values
- Checked by `mod/InvasionMod/scenarios/mod_state/roundtrip.py`.

### Requirement: A save without mod entries gives defaults
The mod SHALL use the registered default of each key when the Tags hold no entry for it. A save from before the mod SHALL load with all defaults and no error.

#### Scenario: A load of the base fixture
- **WHEN** the `base` fixture (no mod entries) is loaded
- **THEN** every registered key has its default value
- **AND** the log has no error
- Checked by `mod/InvasionMod/scenarios/mod_state/default_load.py`.

### Requirement: Two saves keep two separate sets of values
The mod SHALL keep the state with the save it was written into. Loading one save SHALL NOT show the values of another save of the same game.

#### Scenario: Two saves with different values
- **WHEN** set A is saved to one slot, set B is saved to another slot, and each slot is loaded in its own run
- **THEN** each run reads back its own set
- Checked by `mod/InvasionMod/scenarios/mod_state/two_saves.py`.

### Requirement: One entry per key, changed in place
The mod SHALL keep exactly one Tag entry for each key. A changed value SHALL overwrite the array element of the key. The mod SHALL NOT remove a Tag, and SHALL NOT change a Tag that does not start with the prefix `<mod>:`.

#### Scenario: A value changes twice
- **WHEN** a key is set to a new value two times
- **THEN** the Tags array does not grow after the first write and holds one entry for the key
- Checked by `harness/tests/test_fakegame_modstate.py`.

#### Scenario: Foreign Tags stay as they are
- **WHEN** the Tags hold a Tag that is not the mod's and a flush runs
- **THEN** that Tag has the same value and the same place before and after
- Checked by `mod/InvasionMod/scenarios/mod_state/default_load.py`.

### Requirement: Keys are registered and typed
A feature SHALL register each key with a default and a kind (`integer`, `number`, `boolean` or `string`) before it reads or writes the key. A read or write of an unregistered key, a value of the wrong kind, a key registered twice, or a name longer than 1023 characters SHALL fail with a clear message. A string value SHALL use only the characters A-Z a-z 0-9 `_` `.` `-`.

#### Scenario: A typo in a key
- **WHEN** a feature reads or writes a key that it did not register
- **THEN** the call fails and the message names the key and the mod
- Checked by `harness/tests/test_fakegame_modstate.py`.

### Requirement: The mod stores a state version
The mod SHALL store the version of its state format in the entry `<mod>:v=<n>` and SHALL read it back as the stored version, so a later change can migrate old state.

#### Scenario: The first write
- **WHEN** a value is set for the first time
- **THEN** the Tags hold the value entry and a version entry `<mod>:v=<n>`
- Checked by `harness/tests/test_fakegame_modstate.py`.

### Requirement: A bad stored entry fails loudly
The mod SHALL fail with a clear message when the Tags hold a duplicate entry for one key, or an entry whose value does not fit its kind. An entry of the mod prefix with an unregistered key SHALL be kept as it is and listed as unknown.

#### Scenario: A duplicate entry
- **WHEN** the Tags hold two entries for the same key
- **THEN** the load fails and the message names the key
- Checked by `harness/tests/test_fakegame_modstate.py`.

### Requirement: The state loads again after each game load
The mod SHALL read the Tags again when the player pawn begins play after a load. The pawn is not yet available at that moment, so the mod SHALL poll until the new pawn exists, and SHALL log an error if it does not appear.

#### Scenario: A new pawn after a load
- **WHEN** the pawn is replaced by a pawn with other Tags
- **THEN** the state table holds the values of the new Tags
- Checked by `harness/tests/test_fakegame_modstate.py`.

### Requirement: Named commands show and change the state
The mod SHALL offer the named commands `InvasionMod.mod_state_dump`, `mod_state_get`, `mod_state_set` and `mod_state_add_foreign_tag`. `mod_state_dump` SHALL return the values, kinds, stored version, unknown entries and all pawn Tags. `mod_state_add_foreign_tag` SHALL accept only names that match `mstest_<letters, digits, underscore>`.

#### Scenario: A dump on a new game
- **WHEN** a test calls `mod_state_dump` before any value is set
- **THEN** the answer shows the registered `selftest_*` keys with their defaults
- Checked by `harness/tests/test_fakegame_modstate.py`.

#### Scenario: A foreign Tag with a wrong name
- **WHEN** a test calls `mod_state_add_foreign_tag` with a name that does not match the test pattern
- **THEN** the command is refused
- Checked by `harness/tests/test_fakegame_modstate.py`.
