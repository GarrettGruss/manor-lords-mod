# Proposal: Spike playtest telemetry

Issue: #384.

## Why

The Invasion Mod will go to playtesters. When it fails on a tester's PC, we must be able to triage the failure. Today a release has no mod log of its own: the release tool forbids the harness modules `HarnessLog` and `HarnessTelemetry` (`harness/mod-releases`), so `ManorCore.log` falls back to `print()`. That output goes to the buffered `UE4SS.log`, which loses its last lines in a crash and mixes with other mods.

Owner decisions (2026-10-22, explore session):
- The tester sends a manual bug report bundle. Upload to a server (log and save, on a crash or a bug report) is future work.
- The bundle is made in the game, natively, by the mod. It ships to playtesters.
- The log survives a game crash.
- Triage covers (a) crashes and Lua errors and (b) wrong mod behavior, through a trail of mod decisions and low-rate state samples. Balance and feel numbers come later.
- The report includes the save through a checkbox that is ticked by default.
- The amount of telemetry is not known yet. The design must be adjustable and is measured first.

## What Changes

This spike answers the engine and size questions before the feature change `add-playtest-telemetry` is written:
- Can a player-safe Lua logger write and flush each line to `%LOCALAPPDATA%\ManorLords\Saved\InvasionMod\logs\`, and does the file keep its lines when the game process is killed?
- Can the mod tell a clean exit from a crash (a quit hook, or a heartbeat in a marker file), and detect the crash at the next start?
- Can UE4SS Lua `io` read a save file and the newest folder in `Saved\Crashes`, and write a report folder?
- How long does a pure Lua uncompressed ("stored") zip of a report with a save take, and can it run in steps without freezing the game?
- Can a mod menu (framework of #308) show a text box for the tester's description and a checkbox?
- How much log does a 2-year soak make at a `decision` level, and would a bundle have let us find the cause of past bugs (#337, #357, #325)?

## Non-goals

- Building the feature (logger module, events, report builder, menu button). That is the change `add-playtest-telemetry`.
- Upload to a server.
- Balance and feel analytics.
- Any save function call. The report builder only reads saves.

## Capabilities

### New Capabilities

None. The spike writes findings and a recommendation.

### Modified Capabilities

None.

## Impact

- Probe code only, in a probe module and probe test scenarios. It is not shipped.
- Real game runs on one slot. A test that kills the game process checks the crash case; it runs on a fixture and never touches the user's saves except to read a copy.
- Notes in `openspec/changes/spike-playtest-telemetry/notes/`; lasting engine facts move to the wiki.
