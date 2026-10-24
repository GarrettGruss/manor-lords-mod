## MODIFIED Requirements
<!-- Issue: #451 -->

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
