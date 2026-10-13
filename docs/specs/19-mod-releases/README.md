# Spec 19: Mod releases

Issue: #80. Branch: `feat/19-mod-releases`. Status: in progress.

## Goal
Every mod we make can be released to play testers as a GitHub release. One release is one zip for one mod version. A tester unpacks the zip into the game folder and plays. A release is made only from code that passed in the real game.

## Non-goals
- No Nexus Mods or Steam Workshop upload.
- No auto update in the game.
- No release of the harness itself or of stand-in test mods.
- No commit of game assets or of the AES key.

## Plan
1. Manifest `mod/<Name>/mod.json` for each releasable mod. Fields:
   - `name`, `version` (semver), `description`.
   - `shared`: shared modules the mod needs (names in `mod/shared/`). The release adds these modules and what they require.
   - `pak` (optional): `{ "name": "<name>", "source": "file" | "build", "path": "<optional>" }`. `file` (the normal way) means a compiled pak committed at `mod/<Name>/paks/<name>_P.pak` (or at `path`). `build` means the file comes from a `--pak-dir` folder (output of `pakmod.py build <name>`). The zip gets `ManorLords/Content/Paks/~mods/<name>_P.pak`. The folder `paks/` is not copied to the Lua mod folder in the zip.
   - `tested`: `{ "game": "<game version>", "ue4ss": "<UE4SS version>" }`.
   - `gate_scenarios`: scenarios that must have passed in the real game with the current mod files.
2. Per-mod changelog `mod/<Name>/CHANGELOG.md` in Keep a Changelog format, with one section for each version.
3. A player-safe module `mod/shared/ManorCore/ManorCore.lua`. It holds the game calls that a player mod needs and a logger that falls back to `print`. The harness modules (HarnessLords, HarnessHousing, HarnessSack, HarnessBandits) call it, so the harness keeps working.
4. Run summaries record the SHA-256 of every mod file that was deployed (`mod_hashes`). The gate compares them with the current files.
5. `harness/release.py --mod <Name> [--dry-run] [--publish]`:
   - the manifest is valid; the version has no tag yet; the mod changelog has a section for the version;
   - the fake tests pass;
   - the gate: for each gate scenario, the latest real-game run that passed and whose mod hashes match the current files;
   - build `dist/<Name>-v<version>.zip` in game-folder layout, with `enabled.txt`, shared modules, the pak (if any) and `README.txt` (install, uninstall, tested versions);
   - scan the committed paks of the mod for the AES key text;
   - scan the zip: no harness-only module, no AES key text;
   - `--publish`: tag `<name-lower>-v<version>` and `gh release create --prerelease` with the zip and the changelog section as notes.
   - `--dry-run` does everything except the tag and the release.
6. Skill `harness-release`. First release: RefugeeWaves.

## Harness-only modules (never in a release)
`HarnessActions`, `HarnessBoot`, `HarnessLog`, `HarnessCommands`, `HarnessTelemetry`, `HarnessReload`, `HarnessAutosave`, `UEBridge`, the stand-ins and probe mods. The scan fails when one is in the zip.

## Open questions
- Compiled paks (decided by the user, 2026-10-13): compiled mod paks may be committed (CLAUDE.md Safety), also with modified game data. The AES key must never be committed. The release check scans each committed pak of the mod for the key text, and scans the zip again. Original game paks are never committed.
- Pak size: `release.py` prints a WARNING (no failure) for a committed pak over 10 MB (`PAK_SIZE_WARNING_BYTES`), and suggests Git LFS. Git LFS is not set up.
- `deploy.ps1` copies everything under `mod/<Name>/`, so a committed pak is also copied into the game `Mods` folder (harmless, but wasteful). A later change can skip `paks/`.
- Version of UE4SS for testers: the zip does not carry UE4SS. The README tells the tester which build is needed.
- Tag name rule: `<name-lower>-v<version>` (for example `refugeewaves-v0.1.0`).

## Acceptance criteria
- `mod.json` and `CHANGELOG.md` exist for RefugeeWaves, and a schema check in Python passes.
- RefugeeWaves loads without any harness-only module (fake test).
- The existing fake tests stay green.
- `release.py --mod RefugeeWaves --dry-run` passes after a real gate run, and builds a zip that passes the scan.
- `release.py` fails with a clear message for: a bad manifest, a tagged version, a missing changelog section, a missing or stale gate run, a harness module in the zip, the AES key in the zip.
- `--publish` was not run in this spec (the user runs the first release).
