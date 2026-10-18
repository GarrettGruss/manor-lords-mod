# harness/hot-reload Specification

## Purpose
Hot reload puts a Lua change into the running game in about two seconds, with no game restart. It is the fast loop for mod work.

## Requirements

### Requirement: The tool deploys and reloads changed mods
`harness/tools/reload_mods.py` SHALL run `harness/deploy.ps1`, find the mods whose files were copied, and ask the running game to restart each one. A change in `shared/<Name>` SHALL restart every mod that uses that shared module. The tool SHALL fail when the deploy output does not show `errors: 0`.

#### Scenario: A shared module changes
- **WHEN** the deploy copies a file of a shared module
- **THEN** all mods that use that module are reloaded
- Checked by `harness/tests/test_reload_mods.py`.

#### Scenario: Nothing changed
- **WHEN** the deploy copies no file
- **THEN** the tool reloads nothing and ends with exit code 0
- Checked by `harness/tests/test_reload_mods.py`.

### Requirement: A reload is confirmed by version
The mod `HarnessReload` SHALL restart the mod on the game thread and wait up to 20 seconds for the log line `[Name] loaded version <v>`. It SHALL write `reload.result.json` with `id`, `mod`, `ok`, `version`, `line`, `error` and `seconds`. The tool SHALL compare the version with `local VERSION` in the repo file and treat a mismatch as a failed reload.

#### Scenario: The version matches
- **WHEN** the restarted mod logs the version of the repo file
- **THEN** the result is ok and the tool exits with code 0
- Checked by `harness/tests/test_reload_mods.py`.

#### Scenario: The old version line
- **WHEN** the log holds a version line from before the restart
- **THEN** the mod does not take it as the answer
- Checked by `harness/tests/test_fakegame_harnessreload.py`.

#### Scenario: The version is wrong
- **WHEN** the reported version differs from the repo file
- **THEN** the tool fails and prints both versions
- Checked by `harness/tests/test_reload_mods.py`.

### Requirement: A reload request is safe
The tool SHALL write `reload.json` atomically with a unique id in the run folder. `HarnessReload` SHALL run each id once, refuse a request without an id or with a bad mod name, and run a second request only after the first ends. It SHALL check that `Mods/<name>/Scripts/main.lua` exists, because the engine accepts an unknown name.

#### Scenario: The same id twice
- **WHEN** the same request id arrives twice
- **THEN** the mod restarts only once
- Checked by `harness/tests/test_fakegame_harnessreload.py`.

#### Scenario: A bad request
- **WHEN** the request has a bad mod name
- **THEN** the mod writes an error result and restarts nothing
- Checked by `harness/tests/test_fakegame_harnessreload.py`.

### Requirement: Some mods are not reloaded by default
The tool SHALL skip `HarnessReload` and `HarnessBoot` unless `--mod` names them, because a restart of `HarnessBoot` would load the save again.

#### Scenario: HarnessBoot changed
- **WHEN** a deploy copies a `HarnessBoot` file and no `--mod` is given
- **THEN** the tool skips it and adds a note
- Checked by `harness/tests/test_reload_mods.py`.

### Requirement: The tool reports its outcome by exit code
`reload_mods.py` SHALL return exit code 0 when all mods reloaded, 1 when a reload failed, and 2 for a harness error such as no game, no deploy or bad arguments.

#### Scenario: The run folder has no log
- **WHEN** `--run-dir` names a folder with no `mod.log`
- **THEN** the tool refuses with a harness error
- Checked by `harness/tests/test_reload_mods.py`.
