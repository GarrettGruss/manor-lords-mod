---
name: harness-release
description: Release a mod to play testers as a GitHub pre-release (manifest, changelog, real-game gate, zip, scan, tag). Use when you make a mod releasable, prepare a new version, or run harness/release.py.
---

# Mod releases (spec 19)

A release is one zip for one mod version. Rules are in `openspec/changes/archive/2026-10-15-legacy-19-mod-releases/README.md`.

## Make a mod releasable
0. The releasable mod is `mod/InvasionMod`. The first release was the removed standalone mod RefugeeWaves 0.1.0 (pre-release `refugeewaves-v0.1.0`).
1. The mod must not need harness-only modules. Allowed: `ManorCore` (player-safe game calls and a logger that falls back to `print`) and shared modules that need nothing harness-only. Not allowed: `HarnessActions`, `HarnessBoot`, `HarnessLog`, `HarnessCommands`, `HarnessTelemetry`, `HarnessReload`, `HarnessAutosave`, `UEBridge`, stand-ins and probes. Need a game call that lives only in a Harness module? Move it into `mod/shared/ManorCore/ManorCore.lua` and let the Harness module call it. Keep the fake tests green.
2. Optional dependencies use `pcall(require, "HarnessCommands")`. Only a plain `require("X")` counts as a hard dependency (the checker reads it).
3. `mod/<Name>/mod.json`: `name` (the folder name), `version` (semver), `description`, `shared` (every hard-required shared module), `pak` (`null`, or `{name, source: "build"}` or `{name, source: "file", path}`), `tested` (`game`, `game_build`, `ue4ss`), `gate_scenarios` (may be empty only when `features` is set). Optional: `display_name` (the player-facing name; text for players comes from here) and `features` (list of `{name, requires, ids}`; `ids` maps a table name to `[first, last]`). A release leaves out the `data/` and `scenarios/` folders of the mod, and the gate hashes ignore them.
4. `mod/<Name>/CHANGELOG.md`: Keep a Changelog, one `## [x.y.z] - date` section for each version.

## Release steps
0. Run the reliability assessment (skill `reliability-assessment`): `uv run python .claude/skills/reliability-assessment/scripts/reliability.py assess`. Commit the report in `docs/reliability/`. Name each domain of the mod that is over a limit in the release notes (rule `process/reliability-assessment`).
1. Run each gate scenario in the real game with the final mod files: `uv run python harness/run.py --scenario <name>`. Every run records `runs/<id>/mod_files.json` (SHA-256 of every file under `mod/`). Any later edit of a mod file or a shared module it uses closes the gate. Run it again.
2. Dry run: `uv run python harness/release.py --mod <Name> --dry-run`. It checks, in order: the manifest, a free tag, the changelog section, the fake tests (`--skip-tests` only for a quick look), the gate, then it builds `dist/<Name>-v<version>.zip` and scans it. `dist/` is git-ignored.
3. Publish (only when the user asks): merge to `main`, update `main`, then `uv run python harness/release.py --mod <Name> --publish`. It needs a clean tree and HEAD inside `origin/main`. It makes the tag `<name-lower>-v<version>` and runs `gh release create --prerelease` with the zip and the changelog section.

## The zip
Game-folder layout: `ManorLords/Binaries/Win64/ue4ss/Mods/<Name>/` (with `enabled.txt`), `.../Mods/shared/<Module>/`, `ManorLords/Content/Paks/~mods/<pak>_P.pak` if the manifest has a pak, and `README.txt` (install, uninstall, tested versions). The scan fails on a harness-only module or on the AES key text. It reads the key from `modtools/work/aes_key.txt` of the main checkout (`--aes-key-file` overrides) and never prints it.

## Paks
Compiled mod paks may be committed (user decision 2026-10-13). Keep the pak at `mod/<Name>/paks/<pak>_P.pak` and set `"pak": {"name": "<pak>", "source": "file"}`. The release check scans each committed pak for the AES key text; the zip scan checks again. Never commit the key, original game paks, extracts or `.usmap` files. `source: "build"` takes the pak from `--pak-dir <folder>` (output of `pakmod.py build`) instead.

A committed pak over 10 MB (`PAK_SIZE_WARNING_BYTES` in `releaselib/build.py`) gives a WARNING with its name and size, and suggests Git LFS. It does not fail the release.

## In a worktree
The zip scan needs the AES key. It is not in a worktree. Pass `--aes-key-file C:\Users\garre\development\manor-lords-mod\modtools\work\aes_key.txt`, or run the release from the main checkout. The gate needs real-game runs with `runs/<id>/mod_files.json`. Do not launch the game without the user's wish.

## Failures
Each failure prints `FAILED: <reason>` and exits 1. Gate failures name the scenario to run. A "other mod files" gate failure lists the files that differ from the last passing run.
