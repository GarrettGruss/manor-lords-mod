# mod/core Specification

## Purpose
The Invasion Mod is one Lua mod made of separate features. This capability covers the shared parts: the manifest, the feature loader, the feature list, the config and the scheduler.

## Requirements

### Requirement: Features load in dependency order
The mod SHALL load each enabled feature after the features it requires. The order of `feature_list.lua` breaks ties, and requirements load first.

#### Scenario: A feature that requires another
- **WHEN** feature `b` requires `a` and feature `c` requires `b`, and all three are enabled
- **THEN** the loader loads `a`, then `b`, then `c`
- **AND** each feature is loaded as the module `features.<name>.init`
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The loader fails loudly on a bad feature setup
The loader SHALL stop the load with a clear message on a cycle, a duplicate name, a requirement that is not in the list, an enabled feature that requires a disabled feature, a config table for an unknown feature, or a feature that fails to load. The message SHALL name the feature or the cycle.

#### Scenario: A cycle
- **WHEN** feature `a` requires `b` and `b` requires `a`
- **THEN** the load fails with a message that shows the cycle path
- Checked by `harness/tests/test_fakegame_featureloader.py`.

#### Scenario: A requirement is missing or disabled
- **WHEN** an enabled feature requires a feature that is not in the list, or that is disabled in `config.lua`
- **THEN** the load fails and the message names both features
- Checked by `harness/tests/test_fakegame_featureloader.py`.

#### Scenario: A feature raises an error while it loads
- **WHEN** the `init` module of a feature raises an error
- **THEN** the load stops at that feature and the message names the feature and its module path
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: A feature is on only when config enables it
The mod SHALL load a feature only when `config.lua` has a table for it with `enabled = true`. A feature with no config table SHALL count as disabled. A disabled feature SHALL NOT be loaded.

#### Scenario: A disabled feature
- **WHEN** `config.lua` sets `enabled = false` for a feature, or has no table for it
- **THEN** the loader does not load that feature
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The feature list equals the manifest
The mod SHALL keep `Scripts/feature_list.lua` equal to the `features` list in `mod.json`: the same names, in the same order, with the same `requires`.

#### Scenario: The two lists differ
- **WHEN** a feature is in one list and not in the other, or its `requires` differ
- **THEN** the fake game test fails
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: main.lua logs one ready line
The mod SHALL log one line `ready, features: <names>` with tag `InvasionMod` after all enabled features loaded. If the load fails, the mod SHALL log `load failed: <message>` and raise the error again. The mod SHALL NOT start half loaded.

#### Scenario: A normal start
- **WHEN** the game starts the mod with the default config
- **THEN** the log has one `ready, features:` line that lists the enabled features in load order
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: One scheduler timer runs all feature jobs
The mod SHALL run periodic feature work through `scheduler.every(name, every_ms, run)`. The scheduler SHALL use one `LoopAsync` timer with a tick of 100 ms and SHALL run due jobs on the game thread. A job that raises an error SHALL be logged with a stack trace and SHALL NOT stop the other jobs. The tick SHALL NOT be faster than 100 ms, because a 50 ms tick broke the Lua state after about 3 minutes with a menu open (spec 34).

#### Scenario: Two jobs, one fails
- **WHEN** two jobs are registered and one of them raises an error
- **THEN** the error is logged with its job name and the other job still runs at its interval
- Not checked yet.

#### Scenario: A menu stays open
- **WHEN** the tech tree menu stays open for 300 s while the mod state is read twice a second
- **THEN** the Lua state stays alive and the game keeps answering
- Not checked yet. Spec 34 recorded one passing run (`20261018-173614-d910`), but no committed test scenario repeats it.

### Requirement: Tunables live in config.lua
The mod SHALL keep every balance value and every on or off switch in `Scripts/config.lua`, in one table per feature that has the feature name as key and an `enabled` field. The test scenarios SHALL change tunables through named commands, not by editing feature logic.

#### Scenario: A config table without a feature
- **WHEN** `config.lua` has a table whose name is not in the feature list
- **THEN** the load fails with the message `unknown feature`
- Checked by `harness/tests/test_fakegame_featureloader.py`.

### Requirement: The harness finds the mod through its manifest
The mod SHALL declare its name, `display_name`, version, shared modules, pak and features in `mod.json`. Harness code SHALL NOT contain the mod name, so the harness finds the mod only through `mod/<Name>/` paths and `mod.json`.

#### Scenario: Harness code names the mod
- **WHEN** any `.py`, `.lua` or `.ps1` file under `harness/` contains the mod name
- **THEN** the boundary test fails
- Checked by `harness/tests/test_boundary.py`.

### Requirement: Commands work without the harness
Each feature that offers named commands SHALL load `HarnessCommands` with `pcall`. The mod SHALL start and run when `HarnessCommands` is not installed.

#### Scenario: A player installs the mod without the harness
- **WHEN** the shared module `HarnessCommands` is missing
- **THEN** the features load and only the named commands are not registered
- Not checked yet.
