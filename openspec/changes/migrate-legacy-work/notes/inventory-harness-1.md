# Inventory LH1: harness specs 00 to 13, 19, 21, 22, 23, 24, 27, 33

Date: 2026-10-18. Group LH1. Verdicts: CONVERT, DONE (code on main does it), DROP (obsolete or out of scope), LIVE DATA, BUG.
Spec gap: the living spec misses a behavior that main has.

| Legacy file and section | Verdict | Change name or reason | Open issue | Spec gap |
|---|---|---|---|---|
| 00 Follow-up items: MCP tools in a real session, Ctrl+R, autosave, crash report, keep-open, clock cause, baselines, building placement, datatable check | DONE | All marked CLOSED in the file itself. | | no |
| 00 Follow-up: `--keep-open` with another monitor | CONVERT | `spike-other-monitor-and-dpi` | | no |
| 00 Follow-up: spec 09 real pak build "OPEN (user input needed)" | DONE | `pakmod.py`, the A/B suite `pak-ab` and many paks ran in the real game (`docs/harness/09-asset-mods/README.md`, acceptance boxes ticked). | | no |
| 00 Deferred: real pak build | DONE | Built (see above). | | no |
| 00 Deferred: another monitor and DPI scales | CONVERT | `spike-other-monitor-and-dpi` | | no |
| 00 Deferred: other building types with real-mouse placement | DROP | Other types are placed by later specs (14, 17, 18, 30, 32). No separate work. | | no |
| 00 Open decisions: which features first, which test saves | DROP | Answered by the Invasion Mod features and the fixtures in `harness/fixtures/fixtures.json`. | | no |
| 00 Open decisions: nightly regression run, second machine or account | CONVERT | `decide-unattended-regression-run` | | no |
| 00 Roadmap rows and status header | DROP | Legacy status log. Living specs hold the status now (`CONTRIBUTING.md`, legacy section). | #53 | no |
| 01 Plan step 5: log each request to HarnessLog | CONVERT | `add-bridge-request-log` | | no (the backfill dropped the claim) |
| 01 Plan step 5: wipe `bridge\` at launch | DROP | Replaced by a fresh bridge folder in each run folder (`harness/ue4ss-bridge`, "The bridge folder follows the run"). | | no |
| 01 Open questions (layout, game thread queue, struct params, pins, auto reload) | DONE | Answered by `implementation-notes/patches-lua.md`, `patches-python.md` and the spikes. | | no |
| 01 HTTP mode, smoke tests, review checklist | DROP | History. The code is stdio only (backfill report H1). | | no |
| 01 Bridge Python has no test (8 of 10 spec scenarios "Not checked yet") | CONVERT | Part of `add-bridge-request-log` (fake game test). The Python server tests stay a backfill doubt, not a legacy item. | | yes (checks missing) |
| 02 Plan 5: copy of the test save | DONE | Spec 06 part D installs fixtures as `saveGame_<N>` (`harness/save-fixtures`). | | no |
| 02 Plan 6 / open question: "still in development" dialog blocks `LoadGame` | DROP | The load screen opened with the dialog drawn over it (`02-save-autoload/implementation-notes/main-menu-probe.md`, line 35). Hundreds of boots since reach READY. | | no |
| 02 Plan 7: what restarts the clock | DONE | `02-save-autoload/implementation-notes/clock-restart-cause.md` (00 follow-up: partly closed, handled by the retry). | | no |
| 02 Failed boot not tried in the real game | DROP | Covered by the mock modes of the fake game kit (`harness/game-boot`). No consumer for a real test. | | no |
| 03 Open: other monitor, minimized window, banner over the picture | CONVERT | `spike-other-monitor-and-dpi` | | no |
| 03 Open: UE crash folder, Steam closed, `Popen` and launcher exit | DONE | Closed in spec 00 follow-up items (real crash report, direct launch without Steam, keep-open). | | no |
| 04 all | DONE | Acceptance met; built (`harness/telemetry-and-assertions`). | | no |
| 05 Open: client timeout of a long MCP call, 45 s guess | CONVERT | `spike-mcp-client-timeout` | | no |
| 05 Open: tools in a real session | DONE | Closed in spec 00 follow-up. | | no |
| 06 Open: Steam cloud or achievements with a redirected folder | DROP | Not tested. No harm seen in hundreds of runs. The save guard hashes the real folder. A user decision if it matters. | | no |
| 06 Open: crash reports in the private folder | DONE | Real crashes go to the real `Crashes` folder; the launcher copies them (spec 00 follow-up). | | no |
| 06 Open: far-away installed slot number | DROP | Only `max+1` is used (the file says so). | | no |
| 07 Open: look of the world after `set_season` | DROP | No mod feature needs it. Doubt: a user may want a picture check. | | no |
| 07 Open: when `Approval` is recalculated; actions assume a paused game | DROP | Known behavior, handled in scenarios (ranges). No separate work. | | no |
| 07 Open: `spawnRaiders`, `spawnBanditCamp`, `RemoveAllFamilies`, letter banner | DONE | Verified by spec 10 spikes S1, S9 and spec 15. | | no |
| 08 all (baselines, real game crash in a suite) | DONE | Built; thicker baselines closed (spec 00); crashes handled (spec 03 `selftest-crash`). | | no |
| 09 Open: other field types and tables | DONE | Rows, strings and new tables are built by `buildmod` and spec 22, 23, 28 (`harness/pak-mods`). | | no |
| 09 Open: `uninstall.ps1 -Remove` on a real pak | DROP | `pakmod list` shows no pak after the A/B (`09-asset-mods/implementation-notes/ab-n-runs.md`). | | no |
| 09 A/B box "N runs per side" (#53) | DONE | Ticked in the file; suite `pak-ab`. | #53 | no |
| 10 criteria.json and the criteria tables | LIVE DATA | Stays until moved. | | no |
| 10 "move the criteria into openspec" | CONVERT | `move-coverage-criteria-to-openspec` | | yes (`harness/coverage` names legacy default paths; the change fixes it) |
| 10 criteria P3, M2 (not verified), Q3 (human), Q4 (partly) | DROP | P3 moved to spec 15 (done). M2 is owned by `spike-bailey-buildings` (spec 17, #68, another group). Q3, Q4 are human. Rows stay in the live data. | #68 | no |
| 10 Soak: full 730 days, periodic raid, clock slowdown (U9, Q1) | CONVERT | `spike-two-year-soak` | | no |
| 10 S11 rerun, S13 rerun, battlefield anchor raid check, U3 game-time `run_until` | CONVERT | `spike-lord-ai-reruns` | | no |
| 10 "Not verified" of spikes C1, C2, P5, R8, S6, S7, S9 | DROP | Each item is a detail without a consumer (horse units, upkeep, discount rule, custom widget). The mod features test what they need. | | no |
| 10 open-items: real A/B suite | DONE | `pak-ab` ran (open-items update 2026-10-13). | | no |
| 11 Plan steps 1 to 4 | DONE | Built (`harness/game-slots`, `harness/regression-suite`). Issue #151 body is out of date. | #151 | no |
| 11 Step 5 (3 slot against 1 slot A/B), exclusive scenario in a real suite, bridge timeout under load, step 6 docs | CONVERT | `spike-parallel-suite-speedup` | #151 | no |
| 11 Risks: mutex, focus, audio | CONVERT | Task 2.2 of `spike-parallel-suite-speedup`. | #151 | no |
| 12 Acceptance M2 boxes, placement test inside a bailey | DROP | Owned by spec 17 (`spike-bailey-buildings`, #68, another group). | #68 | no |
| 12 Lv3 module and module pak (#90, #65) | DONE | Issues closed; notes `manor-lv3.md`, `manor-module-pak.md`. | | no |
| 13 Follow-up spikes 1 and 2 (M2 data, P3 retry) | DONE | M2 data fields are used in `HarnessWalls`, `HarnessHousing`; P3 done in spec 15. | | no |
| 13 Follow-up spikes 3 to 5 and round 2 spikes (R3 loot gear, stances, `spawnCompleteUnit`, `Squad.camp`, mesh swap) | CONVERT | `spike-community-mod-leads` | | no |
| 13 Open: which mods work on 0.8.111 | DROP | No plan to run community mods (non-goal in the file). | | no |
| 19 Plan and acceptance | DONE | `release.py`, manifest, gate, scan are built; tag `refugeewaves-v0.1.0` exists; `deploy.ps1` skips `paks/` (line 49). | #80 | no |
| 19 Open: Git LFS for big paks | DROP | `release.py` warns above 10 MB (`harness/releaselib/build.py`). No big pak yet. | | no |
| 19 Open: deploy copies `paks/` | DONE | `harness/deploy.ps1` line 49 skips `paks`, `ue`, `art`. | | no |
| 21 Spike A and acceptance boxes | DONE | `genmesh.py`, import and scale are built (`harness/mesh-pipeline`). Issue #102 can close. | #102 | no |
| 21 Spike B | DONE | `21-mesh-generation/implementation-notes/spike-b-big-ox-shed.md`. | #102 | no |
| 21 Open: frame time, UV and normal convention, prop collision | CONVERT | `extend-mesh-pipeline-checks` | #102 | no |
| 33 Fix and proof | DONE | Fixed; `harness/mesh-pipeline` requirement "Game-based material instance" covers it. Issue #237 can close. | #237 | no |
| 33 Open: tune `spec` and `AO` by eye, covered screenshots | CONVERT | `extend-mesh-pipeline-checks` | #237 | no |
| 22 Plan steps 1 to 7, acceptance A1 to A7 | DONE | Skeleton, `buildmod`, release fields, boundary test are built (issue #126 plan: all harness steps done). Doubt: A5 `release.py --mod InvasionMod --dry-run` has no named test. | #126 | no |
| 22 "User breaks M00 into feature specs" | DROP | Done: `docs/mod/M01..M14` exist. Not harness work. | #126 | no |
| 23 Open: save and load of new ids, upgrade use, AI build lists | CONVERT | `spike-new-row-id-persistence` | | no |
| 24 Open: size limits, Tags of lords and buildings, quick save, autosave, stale `saveGame_48` | CONVERT | `spike-mod-state-limits` | | no |
| 24 ModState module "not built yet" | DONE | `mod/shared/ModState/ModState.lua` exists with tests (`test_fakegame_modstate.py`). | | no |
| 27 Plan, open questions 1 to 4, acceptance A1 to A7 | CONVERT | `add-trailer-pipeline` (new capability `harness/trailer-pipeline`) | #133 | no |
| #53 Update stale status lines, roadmap rows, A/B box | DROP | Legacy files are frozen. | #53 | no |
| #53 Skills: coverage number, overview text, modules, speed hold | DONE | `harness-coverage` says 36 of 39; modules and the speed hold are in `harness-overview`. | #53 | no |
| #53 Skill `harness-overview`: "Spec 11 is proposed" | CONVERT | `fix-stale-harness-skill-text` | #53 | no |
| #53 Spec 10 notes may be out of date (S11, S13, soak) | CONVERT | `spike-lord-ai-reruns`, `spike-two-year-soak` | #53 | no |
| #53 Test gaps for 5 helpers in `actions.py` | DONE | All five are tested in `harness/tests/test_runlib_action_checks.py`. | #53 | no |
| #53 Question: delete 50 merged remote branches | DROP | Git housekeeping for the user, not spec work. Stays in the issue. | #53 | no |
| #53 Question: issues for M2 and P3 | DONE | M2 is #68, P3 is #51. | #53 | no |
| #53 Question: issues for older features | DROP | Answered by `CONTRIBUTING.md` ("Old issues keep their titles"). | #53 | no |
| Bug #158 `test_install_scripts` fails while a game runs | BUG | Bug issue, not converted. No legacy spec plans the fix. | #158 | no |
| Bug #160 `suite.py` has no `--slot` | BUG | Bug issue, not converted. `harness/suite.py` has `--slots N|all` now, so it may be closed. | #160 | no |
| Bug #260 fake-game tests fail in WSL | BUG | Bug issue, not converted. | #260 | no |
| Issue #258 game-thread scheduler | DROP | New work by someone else. Not touched. | #258 | no |

## Counts
- CONVERT: 20 rows into 14 changes.
- DONE: 28 rows. DROP: 22 rows. LIVE DATA: 1. BUG: 3.

## Changes written (14)
`spike-parallel-suite-speedup`, `spike-other-monitor-and-dpi`, `decide-unattended-regression-run`, `spike-two-year-soak`, `spike-lord-ai-reruns`, `move-coverage-criteria-to-openspec` (MODIFIED `harness/coverage`), `add-trailer-pipeline` (new `harness/trailer-pipeline`), `spike-community-mod-leads`, `add-bridge-request-log` (ADDED `harness/ue4ss-bridge`), `spike-mcp-client-timeout`, `spike-mod-state-limits`, `spike-new-row-id-persistence`, `extend-mesh-pipeline-checks`, `fix-stale-harness-skill-text`.
All pass `openspec validate <name> --strict`. All have `x-issue: TBD`.

## Doubts
- 07 `set_season` look: dropped; the user may want a picture check.
- 22 A5: no test file was found for `release.py --mod InvasionMod --dry-run`; marked DONE on the strength of the issue #126 plan.
- 10 "Not verified" of seven spikes: dropped as a batch without reading each note in full.
- 06 Steam cloud: dropped; low risk but untested.
