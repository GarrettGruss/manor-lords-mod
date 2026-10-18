# Design: backfill living specs

## Context

See `proposal.md` for the motivation. The process rules are in `openspec/specs/process/spec-workflow/spec.md`.

On 2026-10-18 `openspec/specs/` holds only `process/spec-workflow`. The legacy specs are 33 harness specs (`docs/harness/00` to `33`, no `20`) and 15 mod specs (`docs/mod/M00` to `M14`). Legacy READMEs mix the current state, dated status logs and plans. They can be out of date. The code on `main` is the truth.

## Goals / Non-Goals

**Goals:**
- One living spec for each capability that has built behavior on `main`.
- Each requirement is true on `main`, and each spec scenario names its check or says "Not checked yet".
- A table that maps every legacy spec to its capabilities, so nothing is lost.

**Non-Goals:**
- Delete, move or rename legacy specs. They stay as history and evidence.
- Copy engine facts or spike numbers into specs. They stay in legacy notes and the wiki.
- Convert open plans in this change (see Open Questions).

## Decisions

### D1: The capability map
Each capability is owned by one agent so no two agents write the same file. Paths are under `openspec/changes/backfill-living-specs/specs/`.

| Group | Capability | Legacy sources | Main code |
|---|---|---|---|
| H1 | `harness/ue4ss-bridge` | 01 | `mod/UEBridge`, `vendor/ue4ss-bridge`, `mcp/ue4ss_bridge` |
| H1 | `harness/game-boot` | 02, 06 (autosave part) | `mod/HarnessBoot`, `mod/shared/HarnessAutosave` |
| H1 | `harness/run-launcher` | 03 | `harness/run.py`, `harness/runlib/` |
| H1 | `harness/telemetry-and-assertions` | 04 | `mod/HarnessTelemetry`, `mod/shared/HarnessTelemetry`, `ctx.expect`, `ctx.time` |
| H1 | `harness/agent-tools` | 05 | `mcp/harness_tools` |
| H1 | `harness/hot-reload` | 06 | `mod/HarnessReload`, `harness/tools/reload_mods.py` |
| H1 | `harness/fake-game-kit` | 06 | `harness/tests/fakegame/` |
| H1 | `harness/save-fixtures` | 06 | `harness/runlib/fixtures.py`, `saveslots.py`, `harness/tools/fixtures.py`, `load_save.py` |
| H1 | `harness/regression-suite` | 08 | `harness/suite.py`, `harness/suitelib/`, `run_series.py` |
| H1 | `harness/game-slots` | 11 | `harness/install.ps1`, `uninstall.ps1`, slot code |
| H1 | `harness/save-game` | 24 (save action part) | `mod/shared/HarnessSave` |
| H1 | `process/testing-strategy` | 00 (test layers, principles, gates) | - |
| H2 | `harness/game-actions` | 07 | `mod/HarnessActions`, `mod/HarnessPlace`, `harness/runlib/actions.py` |
| H2 | `harness/mod-commands` | 10 (mod state contract) | `mod/shared/HarnessCommands`, `harness/runlib/modstate.py` |
| H2 | `harness/coverage` | 10 (criteria matrix) | `harness/tools/coverage.py`, `criteria.json` |
| H2 | `harness/stand-in-mods` | 10 (stand-ins) | `mod/InvasionStandIn`, `mod/RaidStandIn` |
| H2 | `harness/pak-mods` | 09, 22 (pak build), 23 | `harness/tools/pakmod.py`, `harness/tools/modpak.py` |
| H2 | `harness/mod-releases` | 19 | `harness/release.py`, `harness/releaselib/` |
| H2 | `harness/mesh-pipeline` | 21, 33 | Meshy and UE import tools in `harness/tools/` |
| H2 | `harness/trailer-pipeline` | 27 | only if built |
| H2 | `harness/unit-tuning` | 28 | `mod/shared/HarnessTune`, `harness/tools/tune_ui.py` |
| H3 | `harness/manor-commands` | 12, 17, 32 | `HarnessManor`, `HarnessWagenburg`, `HarnessGarrison` |
| H3 | `harness/building-commands` | 14, 18, 31 | `HarnessWalls`, `HarnessParts`, `HarnessBuild`, `HarnessSteer`, building parts of `HarnessHousing` |
| H3 | `harness/settlement-commands` | 15 | `HarnessBandits`, family and tent parts of `HarnessHousing` |
| H3 | `harness/policy-commands` | 16 | `HarnessPolicies` |
| H3 | `harness/combat-commands` | 25, 29 | `HarnessBattle`, `HarnessBattlefield`, `HarnessUnits` |
| H3 | `harness/raid-commands` | 10 (spikes S1 to S9) | `HarnessRaids`, `HarnessLords`, `HarnessSack`, `HarnessLoot` |
| H3 | `harness/game-setup` | 26 | `HarnessGameSetup` |
| H3 | `harness/encampment-commands` | 30 | `HarnessEncampment` |
| H3 | `harness/data-tables` | 10, 09 (live table reads) | `HarnessDataTable`, `ManorCore` |
| MA | `mod/core` | 22 (Lua skeleton), `docs/mod/README.md` | `mod/InvasionMod/Scripts/*.lua`, `mod.json` |
| MA | `mod/mod_state` | M01, 24 | `mod/shared/ModState`, feature `mod_state` |
| MA | `mod/invasion` | M02 | feature `invasion` |
| MA | `mod/raid_widget` | M02 (widget) | feature `raid_widget` |
| MA | `mod/raid_behavior` | M03 | feature `raid_behavior` |
| MA | `mod/bandits` | M04 | feature `bandits` |
| MB | `mod/unit_balance` | M05 | feature `unit_balance` |
| MB | `mod/sack_and_terms` | M06 | feature `sack_and_terms` |
| MB | `mod/vassals` | M07 | feature `vassals` |
| MB | `mod/tribute` | M08 | feature `tribute` |
| MB | `mod/refugees` | M09 | feature `refugees` |
| MC | `mod/finite_resources` | M10 | feature `finite_resources` |
| MC | `mod/tech_tree` | M12 | feature `tech_tree` |
| MC | `mod/tech_tree_widget` | M12 (widget) | feature `tech_tree_widget` |
| MC | `mod/manor_stronghold` | M13 | feature `manor_stronghold` |
| MC | `mods/refugee-waves` | 15 | `mod/RefugeeWaves` |
| MC | `mods/policy-menu` | 16 | `mod/PolicyMenu` |

No capability: spec 13 (inspection of community mods, findings only), M00 (the design, owned by the user), M11 and M14 (not started), `feature-breakdown.md` (a plan). The agent of a group may drop a capability that has no built behavior, and must say so in its report.

### D2: Requirements describe built behavior only
A requirement is written only when the code on `main` does it. The agent checks each requirement in the code. A legacy claim that the code does not support is left out and reported.

### D3: Checks
A spec scenario names a test scenario (`harness/scenarios/`, `mod/InvasionMod/scenarios/`) or a Python test (`harness/tests/`). If there is none, it says "Not checked yet". This needs the MODIFIED requirement in `specs/process/spec-workflow/spec.md`.

### D4: Two new capability groups
`mod/core` holds the shared parts of the Invasion Mod (loader, scheduler, config). `mods/<name>` holds standalone player mods (`RefugeeWaves`, `PolicyMenu`). This needs the MODIFIED requirement in `specs/process/spec-workflow/spec.md`.

### D5: Feedback files are copied
For each mod feature with a legacy `feedback.md`, the open items are copied to `openspec/specs/mod/<feature>/feedback.md`. The legacy file stays.

## Risks / Trade-offs

- [Risk] One large change (about 48 delta specs). → One agent per group; each delta is reviewed by its group. `openspec validate --strict` checks the format.
- [Risk] An agent writes a claim from a stale legacy README. → D2: every requirement is checked in the code; reports list dropped claims.
- [Risk] Requirements copy engine facts. → Engine facts stay in legacy notes and the wiki. Requirements state what the harness or mod does.

## Results

### D6: Planned work moves when it starts
Decided by the user on 2026-10-18. Planned legacy iterations and spike follow-ups stay in their legacy folders. The first change that starts such work rewrites the legacy iteration into a change folder. No change folders or issues are made for them now.

### D7: Results of the conversion
- 47 delta specs, 352 requirements. 58 spec scenarios say "Not checked yet". The group reports are in `notes/`.
- Dropped: `harness/trailer-pipeline` (spec 27 has a plan only, nothing is built).
- One overlap was fixed: the Hussite role composition is only in `mod/invasion` (code in `invasion/plan.lua`), not in `mod/unit_balance`.
- No legacy mod spec had open feedback items, so no `feedback.md` was copied.
- Gap: `harness/deploy.ps1` has no capability. A later change can add `harness/deploy`.
- Checks: every "Checked by" path exists. The checks were named, not run. Many mod checks are fake-game tests only.
- A spot check against the code confirmed the scheduler tick (50 ms), the uniform raid size class, the tribute defaults and the `save_game` slot guard. The wiki said 100 ms for the tick; this change fixes it.
