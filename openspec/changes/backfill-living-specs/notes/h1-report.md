# H1 report (harness core)

All 12 delta specs pass `openspec validate backfill-living-specs --strict` (no error or warning in H1 files).

## Numbers

| Capability | Requirements | Spec scenarios | With a real check | Not checked yet |
|---|---|---|---|---|
| harness/ue4ss-bridge | 8 | 10 | 2 | 8 |
| harness/game-boot | 6 | 12 | 11 | 1 |
| harness/run-launcher | 9 | 21 | 21 | 0 |
| harness/telemetry-and-assertions | 8 | 17 | 17 | 0 |
| harness/agent-tools | 8 | 14 | 14 | 0 |
| harness/hot-reload | 5 | 9 | 9 | 0 |
| harness/fake-game-kit | 8 | 11 | 11 | 0 |
| harness/save-fixtures | 8 | 14 | 13 | 1 |
| harness/regression-suite | 11 | 25 | 25 | 0 |
| harness/game-slots | 9 | 17 | 16 | 1 |
| harness/save-game | 7 | 15 | 15 | 0 |
| process/testing-strategy | 8 | 11 | 6 (+5 "Checked by review") | 0 |

No capability was dropped.

## Legacy claims dropped (reason)

- 01: "Log each request (id, verb, target, duration) to HarnessLog": not found in `mod/UEBridge` code.
- 01: "Wipe `bridge\` at launch": the launcher makes a fresh `runs/<id>/bridge` per run. No wipe code. Not written as a requirement.
- 01: HTTP mode on `127.0.0.1:8930`, smoke tests, review checklist: plan or history. The code is stdio only (patch P7).
- 00: roadmap table, status lines, "what is verified today", risk table, deferred items, open decisions: status logs and plans (D2).
- 00: "Ctrl+R hot reload", cheat manager notes: not harness behavior.
- 06 and 11: spike measurements (2.1 s reload, 42 s boot), settings spike results: engine facts and numbers, kept out.
- 24: all mod-state parts (ModState, save hooks, side files): out of scope for `save-game` (owned by MA).
- 03/04: exact phase time limits and exact numbers like the 90 s default scenario limit are left out of requirements, except where they are part of the contract (13500 s max, 300 s long rule, 4096 B summary).

## Doubts

- ue4ss-bridge: 8 of 10 spec scenarios are "Not checked yet". There is no Python test for `mcp/ue4ss_bridge/server.py` (request protocol, timeouts, eval gate) and the Lua mod is only checked in the real game (smoke notes). The behavior is read from the code and from `PATCHES.md`.
- `configure_bridge_client` (the run-bound bridge folder) is only mocked in tests, so that spec scenario is "Not checked yet".
- game-boot: the "boot only on switch" scenario has no test (the fake kit modes always set the env). `boot_state_machine.py` is a script that `test_fakegame_kit.py` imports; I cite the script as the check.
- game-boot: the 8 s clock-stopped rule and the 25 s cinematic limit come from the Lua code. The mode names `pausefails`, `silentrestart`, `cinematic` cover them.
- game-slots: the window tile scenario has no test. `deploy.ps1` is not specced here (no owner in D1 for deploy); run-launcher mentions only `deploy` as a phase. Someone may want a `harness/deploy` capability.
- save-game: CLAUDE.md says `save_game` has not run in the real game. The spec describes the fake-tested behavior only. No scenario checks it in the real game.
- save-fixtures: `test_runlib_fixtures.py` covers install/teardown through fake phases, not the real game.
- regression-suite: the baselines `harness/baselines/` exist for 3 scenarios only; not stated as a requirement.
- Some checks cite test files that include the helper `Expectations` tests (`test_runlib_timectl.py` holds them, not `test_runlib_expectations.py`).
- I ran `python3` once with an empty heredoc by mistake (no effect, no file touched). No other Python was run.
