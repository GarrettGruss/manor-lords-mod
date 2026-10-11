---
name: harness-game-spike
description: Safely experiment with the running game to find out what Lua can read or do (a spike). Use when a feature depends on an engine fact that is not known yet, such as a function, a property, a data table, or what a call changes.
---

# Run a spike in the real game

A spike answers one question about the engine with evidence. Write the question first (the spec's spike list, for example S4 or S6), then keep the work small.

## Setup
1. Read the existing notes in `docs/specs/*/implementation-notes/` for the same area (spike-S*.md, `actions-catalog.md`). Do not repeat a finished spike.
2. Start a game that stays open: `.venv\Scripts\python.exe harness\run.py --scenario noop --keep-open --run-id <id>` (or a hidden `probe-*` scenario, see `harness/scenarios/probe_raids.py`).
3. Talk to the game through the bridge (`ue4ss-bridge` MCP tools, or the bridge client from Python with the run's bridge folder; see `harness/README.md`). The MCP bridge tools may point to a different folder than a `--keep-open` run. Use the run's folder if they cannot reach it.
4. Raw Lua eval (`eval_lua`) is approved by the user (2026-10-10) for single-player experiments only. Mods and scenarios must not depend on it.

## Hard rules (CLAUDE.md Safety)
- Never call a function that saves: `PawnCPP:requestSaveFile`, `SaveToDiskWithThumbnail`, `IoHandler:SaveGameToSlot`, `RequestMenuSave`, `Request Autosave`. They write into the user's real save folder. The launcher only reports a change after it happened.
- Do not read struct values with soft object fields (`getItem`, `RowStruct`) through the bridge: it crashes the game.
- Touch UObjects only on the game thread. The bridge does this for you.
- One agent uses the game at a time. End every game process you start. Check `tasklist`.
- Never write to the user's saves. Runs use a private copy of a fixture save.

## Method
- Change one thing, read before and after, write both numbers down. Count things (units, buildings, stock) instead of trusting a return value.
- Repeat a surprising result. A first-run effect can be a timing effect (the intro cinematic ends about 13 s after load and resets the speed).
- A game day is 40 game seconds. `getGameTimeAdjusted` is the reliable clock, not `bIsPlayerPaused`.
- Time-box each primitive. If it does not work after a reasonable try, record what was tried. "Not possible from Lua, because ..." is a valid result.

## Turn it into a test
When a primitive works: add a data-only action (HarnessActions, validated inputs, no eval) or a mod command, a read command that counts the effect, a scenario with `COVERS`, and fake-game tests. Run the scenario 3 of 3. Only then mark the criterion (skill `harness-coverage`).

## Write it down
One note per spike in the spec's `implementation-notes/` folder: question, method, numbers, verdict, what is not verified. Update the spec README in the same commit.
