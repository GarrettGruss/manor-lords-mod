# Spec Delta

## Purpose

The release tool `harness/release.py` turns one mod version into a zip for play testers and, on request, a GitHub pre-release. It checks the manifest, the changelog, the tests, the real-game gate and the zip content before anything leaves the PC.

## ADDED Requirements

### Requirement: The release command and its modes
The command `uv run python harness/release.py --mod <Name>` SHALL check and build the release for one mod. The options `--dry-run` and `--publish` SHALL exclude each other. Without `--publish`, nothing SHALL leave the PC. Each failed check SHALL print `FAILED: <reason>` and exit with code 1. An unknown mod SHALL fail with a clear message.

#### Scenario: Exclusive options
- **WHEN** both `--dry-run` and `--publish` are given
- **THEN** the command is refused
- Checked by `harness/tests/test_release_cli.py`.

#### Scenario: A failed check
- **WHEN** any check fails
- **THEN** the exit code is 1 and the message starts with `FAILED:`
- Checked by `harness/tests/test_release_cli.py`.

#### Scenario: Unknown mod
- **WHEN** the mod name has no folder
- **THEN** the command fails with a clear message
- Checked by `harness/tests/test_release_cli.py`.

### Requirement: The manifest is checked
The release tool SHALL read `mod/<Name>/mod.json` and list all problems in one error. It SHALL require `name`, `version`, `description`, `shared`, `tested` and `gate_scenarios`. The name SHALL equal the folder name. `pak` SHALL be `null`, a build source or a file source. `gate_scenarios` SHALL NOT be empty unless `features` is set. Feature names SHALL be unique and `ids` ranges SHALL be ordered pairs.


#### Scenario: Valid manifests
- **WHEN** the manifest of any releasable mod in the repo is loaded
- **THEN** it has no problem
- Checked by `harness/tests/test_release_manifest.py`.

#### Scenario: Several problems
- **WHEN** a manifest has missing keys, unknown keys and a bad version
- **THEN** one error lists all of them
- Checked by `harness/tests/test_release_manifest.py`.

#### Scenario: Name and gate rules
- **WHEN** the name differs from the folder, or `gate_scenarios` is empty without `features`
- **THEN** the manifest is refused
- Checked by `harness/tests/test_release_manifest.py`.

### Requirement: Shared modules and harness-only modules
The release tool SHALL compute the closure of the shared modules that the mod declares and requires. An undeclared or missing shared module SHALL fail. A hard `require` of a harness-only module (for example `HarnessActions`, `HarnessCommands`, `HarnessLog`) in the mod or in a shared module SHALL fail. A `pcall(require, ...)` SHALL count as optional.

#### Scenario: Closure
- **WHEN** a shared module requires another shared module
- **THEN** the closure holds both, and comments and optional requires do not count
- Checked by `harness/tests/test_release_manifest.py`.

#### Scenario: Harness-only dependency
- **WHEN** the mod hard-requires a harness-only module
- **THEN** the release fails
- Checked by `harness/tests/test_release_manifest.py`.

#### Scenario: A mod with no harness module
- **WHEN** the mod `RefugeeWaves` is checked
- **THEN** it needs no harness-only module
- Checked by `harness/tests/test_release_manifest.py`.

### Requirement: Tag and changelog
The tag SHALL be `<name-lower>-v<version>`. The release SHALL fail when the tag exists locally or on `origin`. An unreachable origin SHALL fail unless `--offline` is set. The file `mod/<Name>/CHANGELOG.md` SHALL hold a non-empty `## [x.y.z] - date` section for the version, and that text SHALL be the release notes.

#### Scenario: Tag checks
- **WHEN** the tag is free, exists locally, exists on origin, or origin is unreachable
- **THEN** the check passes, fails, fails, or fails unless `--offline`
- Checked by `harness/tests/test_release_cli.py`.

#### Scenario: Release notes
- **WHEN** the section of the version is missing or empty
- **THEN** the release fails with a clear message
- Checked by `harness/tests/test_release_manifest.py`.

### Requirement: The real-game gate
The release tool SHALL require a passing real run of each `gate_scenarios` entry. The run SHALL have the same hashes for all released mod files and shared modules, and the same game build as `tested.game_build`. Files in `data/` and `scenarios/` SHALL NOT count. A fake run SHALL NOT count. The error SHALL name the scenario to run.

#### Scenario: Matching run
- **WHEN** a passing real run has matching hashes and game build
- **THEN** the gate opens and reports the latest matching run
- Checked by `harness/tests/test_release_gate.py`.

#### Scenario: Changed file or other build
- **WHEN** a released file changed after the run, or the game build differs
- **THEN** the gate closes with a message about the difference
- Checked by `harness/tests/test_release_gate.py`.

#### Scenario: No run or only failed runs
- **WHEN** no run exists or all runs failed
- **THEN** the gate closes and names the command to run
- Checked by `harness/tests/test_release_gate.py`.

#### Scenario: Data files
- **WHEN** only `data/` or `scenarios/` files change
- **THEN** the gate hashes do not change
- Checked by `harness/tests/test_release_gate.py`.

### Requirement: The zip layout
The zip SHALL be named `<Name>-v<version>.zip` and use the game folder layout: the mod under `ManorLords/Binaries/Win64/ue4ss/Mods/<Name>/` with `enabled.txt`, the shared closure under `Mods/shared/`, an optional pak under `ManorLords/Content/Paks/~mods/`, and a `README.txt` with install, uninstall and tested versions. The folders `data/`, `scenarios/`, `paks/`, `ue/` and `art/` of the mod SHALL stay out of the Lua folder. Equal input SHALL give equal bytes.

#### Scenario: Layout
- **WHEN** the zip is built
- **THEN** its paths follow the game folder, the readme has the three sections, and the data and scenario folders are absent
- Checked by `harness/tests/test_release_zip.py`.

#### Scenario: Equal bytes
- **WHEN** the same files are zipped twice
- **THEN** the zips are equal
- Checked by `harness/tests/test_release_zip.py`.

#### Scenario: Pak sources
- **WHEN** the manifest names a pak by file or by build
- **THEN** the pak goes to the `~mods` folder, and a missing pak fails with a clear message
- Checked by `harness/tests/test_release_zip.py`.

### Requirement: The zip scan and the AES key
The release tool SHALL scan the zip and delete it when the scan fails. The scan SHALL fail on a harness-only module in a path, a hard `require` of one in a Lua file, and the AES key text (in several encodings) in any file or in a committed pak. A key shorter than 16 characters SHALL be rejected. The key SHALL NOT be printed. A committed pak over 10 MB SHALL give a warning with a Git LFS hint and SHALL NOT fail.

#### Scenario: Clean zip
- **WHEN** the zip has no harness-only module and no key
- **THEN** the scan passes, and an optional `pcall(require)` passes
- Checked by `harness/tests/test_release_zip.py`.

#### Scenario: Key in a file
- **WHEN** the key text is in a text file, a binary file or a committed pak
- **THEN** the scan fails, names the file, and does not print the key
- Checked by `harness/tests/test_release_zip.py`.

#### Scenario: Big pak
- **WHEN** a pak is over the size limit
- **THEN** the output has a warning with the name, the size and an LFS hint
- Checked by `harness/tests/test_release_zip.py`.

### Requirement: Publish from committed files only
With `--publish`, the tool SHALL require a clean working tree and a HEAD inside `origin/main`. It SHALL then create the tag, push it, and run `gh release create --prerelease` with the zip and the release notes. The fake test run SHALL be the full discovery of `harness/tests`, unless `--skip-tests` is given (which prints a warning).

#### Scenario: Publish with a dirty tree
- **WHEN** the working tree has uncommitted changes
- **THEN** the release fails with a message to commit first
- Not checked yet.

#### Scenario: Pre-release on GitHub
- **WHEN** all checks pass
- **THEN** a tag and a GitHub pre-release with the zip exist
- Not checked yet.
