# harness/pak-mods Specification

## Purpose
Pak mods change game data that Lua cannot change at run time. The harness builds an unencrypted mod pak, installs it for a run, removes it afterwards, and builds the Invasion Mod pak from row patches with checks for conflicts and id ranges.

## Requirements

### Requirement: Tool config and pinned tools
The tool `harness/tools/pakmod.py` SHALL read its config from `harness/pakmod.local.json`. The command `check` SHALL report each config problem, a missing tool, an unpinned tool, a missing `.usmap` mapping and a missing paks folder. It SHALL exit with code 3 on a tool hash mismatch and SHALL NOT run a tool whose hash does not match its pin. `check --pin` SHALL write the hashes.

#### Scenario: Valid config
- **WHEN** the config is valid and the tools match their pins
- **THEN** `check` prints hashes, status and the repak version
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Hash mismatch
- **WHEN** a tool hash differs from its pin
- **THEN** the exit code is 3, the message names the tool, and the tool is never run
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Missing config or mapping
- **WHEN** the config, a tool or the mapping is missing
- **THEN** `check` reports each problem with a clear message
- Checked by `harness/tests/test_pakmod.py`.

### Requirement: The AES key stays secret
The pak tools SHALL pass the AES key to repak only through the environment variable named by `aes_key_env`. They SHALL fail loudly when the variable is not set. They SHALL NOT print the key or write it to a file. A key value pasted in place of the variable name SHALL be refused without being echoed. A dry run SHALL show the command with a masked key.

#### Scenario: No leak
- **WHEN** a command runs with the key set, in a dry run, or with an error
- **THEN** the key text does not appear in the output or in any file
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Key variable missing
- **WHEN** an extract from an encrypted pak runs and the variable is not set
- **THEN** the command fails with a clear message
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Key text in a committed pak
- **WHEN** the release scan finds the key text in a pak or a text file
- **THEN** the scan fails and does not print the key
- Checked by `harness/tests/test_release_zip.py`.

### Requirement: Extract, convert and round trip
The tool `pakmod.py` SHALL provide `find`, `extract`, `tojson`, `fromjson` and `roundtrip`. `extract` SHALL write the `.uasset` and `.uexp` (and an optional `.ubulk`) in the internal layout of the pak, and SHALL fail for a missing asset. `tojson` SHALL fail on a raw export (a missing mapping) and on a mapping that differs from the `.usmap`. `roundtrip` SHALL report the first differing offset of a lossy round trip. Tool calls SHALL use no shell and a time limit.

#### Scenario: Find
- **WHEN** `find` searches the pak indexes
- **THEN** the search is case-insensitive, shows at most 50 matches, names the pak, and uses a cache that refreshes when a pak changes
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Conversion fails loudly
- **WHEN** a tool fails, times out or writes no output
- **THEN** the command reports the failure with the tool message
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Lossy round trip
- **WHEN** the round trip differs from the original
- **THEN** the report gives the first differing offset
- Checked by `harness/tests/test_pakmod.py`.

### Requirement: Work folder guards
Every path and name in `pakmod.py` SHALL stay inside the work folder. A build name SHALL be 1 to 40 characters from `A-Za-z0-9_-` and SHALL NOT be a reserved folder name. The tool SHALL refuse a symlink, an absolute path and a path with traversal in the asset files. All commands SHALL accept `--dry-run`, which changes nothing.

#### Scenario: Bad names and paths
- **WHEN** a name is bad or reserved, or a path leaves the work folder
- **THEN** the command is refused
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Dry run
- **WHEN** a command runs with `--dry-run`
- **THEN** no tool runs and no file is written
- Checked by `harness/tests/test_pakmod.py`.

### Requirement: Build an unencrypted mod pak
The command `build <name>` SHALL pack the build folder into `<name>_P.pak` with the configured mount point and pak version. It SHALL list the built pak and compare it with the folder. When they differ, it SHALL exit with code 4.

#### Scenario: Build
- **WHEN** `build demo` runs
- **THEN** the output pak is `<work_dir>/out/demo_P.pak`, and its listing equals the folder
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: A pak that misses a file
- **WHEN** the built pak lacks a file of the folder
- **THEN** the exit code is 4
- Checked by `harness/tests/test_pakmod.py`.

### Requirement: Install and remove only what the harness wrote
The commands `install`, `remove` and `list` SHALL manage `Paks/~mods` through the manifest `.harness-paks.json`. `install` SHALL refuse to overwrite a file that is not in the manifest, and SHALL record the SHA-256 of the pak. `remove` SHALL delete only manifest files, keep other files and a folder that the user made, and skip a file that changed after install. `remove` without a name or `--all` SHALL fail. A manifest entry with a path SHALL be refused.

#### Scenario: Foreign pak
- **WHEN** a pak with the same name exists and is not in the manifest
- **THEN** `install` refuses and the foreign file stays
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Changed pak
- **WHEN** an installed pak changed after install
- **THEN** `remove` keeps it and reports it
- Checked by `harness/tests/test_pakmod.py`.

#### Scenario: Remove all
- **WHEN** `remove --all` runs with two harness paks and one foreign pak
- **THEN** only the two harness paks are deleted
- Checked by `harness/tests/test_pakmod.py`.

### Requirement: Run a scenario with a pak
The launcher option `--pak NAME` (repeatable) SHALL install the built pak before the game starts and remove it after the run, also after a crash or a timeout. It SHALL record the SHA-256 prefix of each pak in `config.json` under `environment.paks`. It SHALL check names before any folder or lock exists, SHALL refuse a duplicate name, and SHALL be refused with `--fake`. A run that keeps the game open SHALL leave the pak in place.

#### Scenario: Install and remove
- **WHEN** a run uses `--pak demo`
- **THEN** the pak is in `~mods` during the run and removed at the end, and the hash is in `config.json`
- Checked by `harness/tests/test_runlib_variant.py`.

#### Scenario: Failed earlier phase
- **WHEN** an earlier phase fails or crashes
- **THEN** the cleanup phase still removes the pak
- Checked by `harness/tests/test_runlib_variant.py`.

#### Scenario: Unbuilt pak or foreign file
- **WHEN** the pak is not built, or a foreign file has the same name
- **THEN** the run fails with a clear message and the foreign file stays
- Checked by `harness/tests/test_runlib_variant.py`.

#### Scenario: Keep open
- **WHEN** a run keeps the game open
- **THEN** the pak stays in place and a note says so
- Checked by `harness/tests/test_runlib_variant.py`.

### Requirement: Build the Invasion Mod pak from row patches
The command `buildmod <ModName>` SHALL build `mod/<ModName>/paks/<ModName>_P.pak` from `data/<feature>/patches/*.json` of all features in the order of `mod.json`, then by file name. A feature with `"pak": false` in `mod.json` SHALL be checked but not built. A patch SHALL have `table`, `row`, `op` (`add` or `set`) and the keys of that operation. The supported tables SHALL be `buildingStats` and `DT_Upgrades` (digit row ids), and `DT_GameSetupPresets` and `DT_Translation_GameSetups` (row names). A key of `set` that holds `/` or is `*` SHALL be a path into a struct or a map, and SHALL set every matching value. Each build SHALL start from the current game table and from an empty work folder. A bad patch SHALL fail with a message that names the file.

#### Scenario: Patch format
- **WHEN** a patch has an unknown table, operation or key, a missing key, or invalid JSON
- **THEN** the build fails and the message names the file
- Checked by `harness/tests/test_modpak.py`.

#### Scenario: Add and set
- **WHEN** an `add` patch clones row `from` to a new row and sets fields
- **THEN** the new row has the cloned values with the changes, and an existing row cannot be added or a missing source used
- Checked by `harness/tests/test_modpak.py`.

#### Scenario: Named rows and paths
- **WHEN** a patch adds a row to `DT_GameSetupPresets` and sets `gameSetupData/*/goals`
- **THEN** the new row needs no id range, every difficulty of the new row has the value, and the source row stays unchanged
- Checked by `harness/tests/test_modpak.py` (class `NamedTableTests`) and the real game run `hussite-tpl-13`.

#### Scenario: End to end
- **WHEN** the build runs with fake tools
- **THEN** a pak is built, and a failed check builds nothing
- Checked by `harness/tests/test_modpak.py`.

#### Scenario: Repo patches
- **WHEN** the repo mods are checked
- **THEN** every patch passes the checks
- Checked by `harness/tests/test_modpak.py`.

### Requirement: Patch conflicts are errors
The build SHALL fail when two patches add the same row, or when two features set the same field of one row. The message SHALL name both files. Different fields of one row SHALL NOT conflict. Two features SHALL NOT write the same asset file.

#### Scenario: Same row or field
- **WHEN** two patches add one row, or two features set one field
- **THEN** the build fails and names both files
- Checked by `harness/tests/test_modpak.py`.

#### Scenario: Same asset
- **WHEN** two features copy the same asset path
- **THEN** the build fails
- Checked by `harness/tests/test_modpak.py`.

### Requirement: New row ids stay in the feature range
Each `add` patch SHALL use a row id inside the `ids` range of its feature in `mod.json` for that table. The build SHALL fail when the id is outside the range, or when the feature has no range for the table.

#### Scenario: Id outside the range
- **WHEN** a feature adds a row outside its range
- **THEN** the build fails with the file, the row and the range
- Checked by `harness/tests/test_modpak.py`.

#### Scenario: Table without a range
- **WHEN** a feature adds a row to a table without an `ids` range
- **THEN** the build fails
- Checked by `harness/tests/test_modpak.py`.

### Requirement: Assets are copied into the pak
The build SHALL copy `data/<feature>/assets/**` into the pak folder with their folders. It SHALL refuse a symlink.

#### Scenario: Assets with folders
- **WHEN** a feature has assets in sub folders
- **THEN** they are in the pak with the same folders
- Checked by `harness/tests/test_modpak.py`.

### Requirement: Upgrades use only vanilla ids
A pak SHALL NOT add a `DT_Upgrades` row with a new id, and SHALL NOT set `upgradesInto` of an upgrade to a new `buildingStats` id. A pak MAY add new `buildingStats` ids in the feature range (they load, are placed, built, saved and loaded).

#### Scenario: New building id
- **WHEN** a pak adds a `buildingStats` row in the feature range
- **THEN** the building can be placed, built, saved and loaded
- Checked by spike run `rowid-write-b` and `rowid-read-a` (notes/id-persistence.md).

#### Scenario: New upgrade id
- **WHEN** a pak adds a `DT_Upgrades` row with a new id
- **THEN** the game copies the cost into `needs` but never carries out the upgrade
- Checked by spike runs `rowid-control-b` and `rowid-control-e` (notes/id-persistence.md).

### Requirement: Cooked widgets are mod pak assets
A cooked Widget Blueprint (`.uasset` and `.uexp`) SHALL be a file under `data/<feature>/assets/`, so `buildmod` puts it in the same pak as the table rows. One widget file SHALL have one owner feature.

#### Scenario: A widget in the mod pak
- **WHEN** `buildmod` runs for a mod with a widget asset in a feature
- **THEN** the pak holds the widget and the table rows
- Checked by `harness/tests/test_modpak.py` and `harness/tests/test_invasionmod_pak.py`.
