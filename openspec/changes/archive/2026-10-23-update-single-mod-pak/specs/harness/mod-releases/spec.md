## ADDED Requirements
<!-- Issue: #471 -->

### Requirement: The Invasion Mod ships one pak
The manifest of the Invasion Mod SHALL name one pak, `InvasionMod`, with source `file`. That pak SHALL hold all widget assets and all data table rows of the mod. The release zip SHALL hold only that pak under `ManorLords/Content/Paks/~mods/`. The repo SHALL NOT hold another committed pak for the mod.

#### Scenario: Release zip file list
- **WHEN** the release tool builds the zip of the Invasion Mod
- **THEN** the only `.pak` file in the zip is `InvasionMod_P.pak`
- Checked by `harness/tests/test_invasionmod_pak.py` (manifest and committed pak) and a release dry run.
