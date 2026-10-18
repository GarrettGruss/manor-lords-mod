---
type: Reference
title: Source map
description: What each top folder and main subfolder of the repo owns, the entry files, and which paths are git-ignored.
tags: [architecture, layout, folders, gitignore]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T16:03:40Z }
sources:
  - resource: repo://.gitignore
  - resource: repo://CLAUDE.md
  - resource: repo://harness/
  - resource: repo://mod/
  - resource: repo://mcp/
  - resource: repo://vendor/ue4ss-bridge/
  - resource: repo://docs/
  - resource: repo://openspec/
  - resource: repo://.claude/skills/
  - resource: repo://.mcp.json
  - resource: repo://pyproject.toml
---
# Source map

Read [System overview](overview.md) first for how the parts work together.

## Top level

| Path | Owns |
| --- | --- |
| `CLAUDE.md` | Project rules for agents: writing, subagents, specs, git, safety, environment. |
| `CHANGELOG.md` | Keep a Changelog file. User-visible changes go under `Unreleased`. |
| `pyproject.toml`, `uv.lock`, `.python-version` | The uv project (Python 3.12, venv `.venv`). `mcp==1.30.0` is pinned. |
| `.mcp.json` | Starts the two MCP servers over stdio. |
| `.claude/` | `settings.json` (permissions) and `skills/`. A skill folder may hold its own scripts and tests (for example `skills/repo-wiki/scripts/wiki.py`); they are not part of the game harness. |
| `harness/` | The outer harness. See below. |
| `mod/` | Lua mods, shared Lua modules and the Invasion Mod. |
| `mcp/` | The two MCP servers. |
| `vendor/ue4ss-bridge/` | Notes on the vendored upstream bridge: `VERSION`, `PATCHES.md`, `LICENSE`. |
| `docs/` | Specs, mod docs and this wiki. |

## harness/

| Path | Owns |
| --- | --- |
| `run.py` | Entry point of one run. See [Scenario run](../workflows/scenario-run.md). |
| `run_series.py` | Runs the launcher N times and prints a table. |
| `suite.py` | Suites, baselines and A/B. See [Suites and A/B](../workflows/suites-and-ab.md). |
| `release.py` | Mod release CLI. See [Mod releases](../workflows/releases.md). |
| `deploy.ps1` | Copies `mod/` into the UE4SS `Mods` folder with hash checks. |
| `install.ps1`, `uninstall.ps1`, `installstate.ps1` | Back up game settings, write harness values, build game slots, restore. See [Install and environment](../operations/install-and-environment.md). |
| `game-launch.ps1`, `game-close.ps1` | Start and stop the game by hand. |
| `runlib/` | The library behind `run.py` and scenarios: phases, runner, summary, bridge client, `ctx` helpers, fixtures, saves. |
| `suitelib/` | Suite runner, A/B statistics, baselines, reports. |
| `releaselib/` | Release build, manifest, changelog, gate, scan. |
| `scenarios/` | One Python module per scenario. `probe_*` scenarios are hidden research tools. |
| `suites/` | Suite JSON files (for example `core.json`, `smoke.json`). |
| `baselines/` | Baseline ranges (`smoke.json`, `time-advance.json`, `telemetry-sanity.json`). |
| `fixtures/fixtures.json` | The fixture list. The fixture saves are in `harness/fixtures/saves/` (git-ignored). |
| `tools/` | Command line tools: `coverage.py`, `pakmod.py`, `modpak.py`, `reload_mods.py`, `fixtures.py`, `load_save.py`, `collect_crash.py`, `genmesh.py`, `genimage.py`, `recook_meshy_pak.py`. Files named `s<NNN>_*.py` are one-off spike scripts. |
| `raidstandin/` | Python client for the RaidStandIn mod. |
| `vanilla/` | `itemStats.json`, vanilla item data. |
| `tests/` | All Python and fake-game tests. See [Python tests](../testing/python-tests.md) and [Fake game kit](../testing/fake-game-kit.md). |

## mod/

Each folder is deployed to `ue4ss\Mods\<name>\`. Folders in `mod/shared/` are merged into `ue4ss\Mods\shared\<Name>\<Name>.lua`. See [Shared Lua modules](shared-lua-modules.md).

| Path | Owns |
| --- | --- |
| `shared/` | Shared Lua modules: `ManorCore`, `ModState`, `HarnessLog`, `HarnessCommands` and the other `Harness*` modules. |
| `HarnessBoot/`, `HarnessActions/`, `HarnessTelemetry/`, `HarnessReload/`, `HarnessPlace/` | Harness mods. See [Harness and player mods](other-mods.md). |
| `UEBridge/` | The bridge Lua mod (`scripts/main.lua`, `json.lua`, `settings.lua`). |
| `PolicyMenu/`, `RefugeeWaves/` | Player-facing mods. |
| `InvasionStandIn/`, `RaidStandIn/` | Stand-in mods that test logic a mod defines. |
| `HarnessLoadProbe/`, `HarnessLogTest/` | Small probe mods. |
| `InvasionMod/` | The Invasion Mod: `Scripts/` (`main.lua`, `feature_loader.lua`, `feature_list.lua`, `scheduler.lua`, `config.lua`, `features/`), `data/<feature>/` row patches, `scenarios/<feature>/`, `paks/`, `ue/`, `mod.json`. See [Invasion Mod structure](invasion-mod.md). |

## mcp/

| Path | Owns |
| --- | --- |
| `ue4ss_bridge/` | MCP server and CLI for live game queries. Vendored with harness patches. |
| `harness_tools/` | MCP server `manor-harness`: `server.py` declares tools, `tools.py` holds the logic. |
| `README.md` | Setup and environment variables of the bridge server. |

## docs/

| Path | Owns |
| --- | --- |
| `harness/<NN>-<name>/` | Legacy harness specs (read-only), with `implementation-notes/`. |
| `mod/` | The Invasion Mod design (`M00`) and legacy feature specs (read-only). |
| `wiki/` | This wiki. |

## openspec/

| Path | Owns |
| --- | --- |
| `config.yaml` | Project context and rules for every OpenSpec artifact. |
| `specs/<capability>/spec.md` | Living specs: the behavior that is true on `main`. |
| `changes/<change-name>/` | Open changes: proposal, delta specs, design, tasks, `notes/`. |
| `changes/archive/` | Done changes. |

The skills `.claude/skills/openspec-*/` and the commands `.claude/commands/opsx/` are generated by the OpenSpec CLI.

See [Specs, docs and project process](../operations/docs-and-specs.md).

## Git-ignored paths

From `.gitignore`: `runs/` (run folders), `saves/*.bak`, `.venv/`, `__pycache__/`, `harness/pakmod.local.json`, `modtools` (repak, UAssetGUI, work files, the AES key), `slots/` (parallel game copies), `harness/fixtures/saves/` (user save fixtures) and `dist/` (release output).

A git worktree has none of these. Copy the fixture saves and `pakmod.local.json` from the main checkout. Compiled mod paks (`mod/<Name>/paks/*_P.pak`) may be committed. The AES key must never be committed.
