---
type: Overview
title: Quickstart
description: Entry page of the repo wiki with what the repo is, the edit-deploy-run-read loop, and a task map that routes each common job to its wiki page and skill.
tags: [quickstart, navigation, harness, mod]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T15:30:28Z }
sources:
  - resource: repo://CLAUDE.md
  - resource: repo://.claude/skills/harness-overview/SKILL.md
  - resource: repo://harness/run.py
  - resource: repo://mod/InvasionMod/mod.json
---
# Quickstart

This repo is an agent harness for Manor Lords mods. An agent edits a Lua mod, deploys it, runs the real game, reads `summary.json`, and repeats. The main product is the Invasion Mod (`mod/InvasionMod/`). The rules for agents are in `CLAUDE.md`. Read its Safety section before you touch saves or the game.

This wiki explains the current system. Specs (`docs/harness/`, `docs/mod/`) hold the history and the decisions. Check an important detail in the source before you rely on it. To keep the wiki current, use the skill `repo-wiki`.

## The loop in five lines

1. Change Lua in `mod/` (and tests in `harness/tests/`).
2. Run the fast tests: `uv run python -m unittest discover -s harness/tests -p "test_fakegame_*.py"` ([Fake game kit](testing/fake-game-kit.md)).
3. Run one real game iteration: `uv run python harness\run.py --scenario <name>` ([Scenario run](workflows/scenario-run.md)).
4. Read `runs/<id>/summary.json` first ([Run folder and verdicts](concepts/run-folder-and-verdicts.md)).
5. Repeat. For stochastic behavior, run a suite or an A/B test ([Suites, baselines and A/B tests](workflows/suites-and-ab.md)).

Start every Python command with `uv run python`. The project runs on Windows ([Install and environment](operations/install-and-environment.md)).

## Task map

| I want to | Read | Skill |
|---|---|---|
| Understand the parts and how they connect | [System overview](architecture/overview.md), [Source map](architecture/source-map.md) | `harness-overview` |
| Run a scenario and read the verdict | [Scenario run](workflows/scenario-run.md), [Run folder and verdicts](concepts/run-folder-and-verdicts.md) | `harness-run-scenario` |
| Find out why a run failed or crashed | [Debugging runs](operations/debugging-runs.md) | `harness-debug-run` |
| Write a test scenario | [Writing scenarios](workflows/writing-scenarios.md) | `harness-write-scenario` |
| Compare variants over many runs | [Suites, baselines and A/B tests](workflows/suites-and-ab.md) | `harness-ab-testing` |
| Call mod logic from a scenario, or add a command | [Mod commands and state](concepts/mod-commands-and-state.md) | `harness-mod-state` |
| Keep mod values in a player save | [Mod commands and state](concepts/mod-commands-and-state.md#modstate-lua-values-inside-a-save) | `harness-mod-state` |
| Stay safe with saves, autosave and crash-prone calls | [Safety rules](concepts/safety-rules.md) | - |
| Change Lua and see it in the running game | [Dev loop and fixtures](workflows/dev-loop-and-fixtures.md) | - |
| Start a run from a known save | [Dev loop and fixtures](workflows/dev-loop-and-fixtures.md#fixtures) | - |
| Work on an Invasion Mod feature | [Invasion Mod structure](architecture/invasion-mod.md), [Invasion Mod features](architecture/invasion-features.md) | - |
| Find or change a shared Lua module | [Shared Lua modules](architecture/shared-lua-modules.md) | - |
| Work on HarnessBoot, the player mods or the stand-ins | [Harness and player mods](architecture/other-mods.md) | - |
| Query the live game | [UE4SS bridge](integrations/ue4ss-bridge.md) | `harness-game-spike` |
| Drive runs through MCP tools | [Harness MCP tools](integrations/harness-mcp-tools.md) | `harness-run-scenario` |
| Change game data tables | [Pak mods](workflows/pak-mods.md) | `harness-pak-mod` |
| Make a 3D model | [Meshy models](workflows/meshy-models.md) | `harness-meshy` |
| Release a mod to play testers | [Mod releases](workflows/releases.md) | `harness-release` |
| Install the harness, game slots, environment variables | [Install and environment](operations/install-and-environment.md) | - |
| Run the Python tests or measure coverage | [Python tests and coverage](testing/python-tests.md) | `harness-coverage` |
| Test Lua without the game | [Fake game kit](testing/fake-game-kit.md) | - |
| Write a spec, branch, commit, open a PR | [Specs, docs and project process](operations/docs-and-specs.md) | `harness-git-workflow` |
| Split work between agents | [Specs, docs and project process](operations/docs-and-specs.md#subagents) | `harness-dispatch-agents` |

## Rules to know first

- Never call a game save function from a probe, a scenario or eval. The only save path is the guarded `save_game` action ([Safety rules](concepts/safety-rules.md)).
- Harness code must not name the Invasion Mod or its features (`harness/tests/test_boundary.py`).
- The simulation is not deterministic. Assert ranges.
- A game crash is a result with logs, not a harness failure.
- Deploy with `harness/deploy.ps1`. Do not copy mod files by hand.
