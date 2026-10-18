# H3 report: harness command modules

Files: `openspec/changes/backfill-living-specs/specs/harness/<capability>/spec.md` for the nine capabilities below.
`openspec validate backfill-living-specs --strict` passes for the whole change (checked after the last edit).

## Numbers

| Capability | Requirements | With a real check | Scenarios | Scenarios checked |
|---|---|---|---|---|
| harness/manor-commands | 7 | 5 | 19 | 13 |
| harness/building-commands | 9 | 7 | 29 | 23 |
| harness/settlement-commands | 6 | 6 | 21 | 21 |
| harness/policy-commands | 6 | 5 | 13 | 12 |
| harness/combat-commands | 8 | 6 | 21 | 15 |
| harness/raid-commands | 8 | 7 | 30 | 27 |
| harness/game-setup | 2 | 0 | 4 | 0 |
| harness/encampment-commands | 2 | 2 | 8 | 6 |
| harness/data-tables | 5 | 5 | 17 | 15 |
| Total | 53 | 43 | 162 | 132 |

A "real check" is a Python test with assertions (mostly the fake-game tests in `harness/tests/`) or a scenario with `expect` calls (`manor_storage`, `manor_storage_workers`, `rebuild_cost`, `sack_village`, `loot_drop_recovery`, `pak_item_value`).
Every cited path exists.

## Decisions on placement

- `units_census` is in combat-commands (it is the `HarnessUnits` census). `spawn_raiders`, `kill_units`, `set_unit_loot` are in raid-commands.
- `manor_blueprint_add` and `manor_planner` (spec 17 bailey) are in manor-commands, although the code is in `HarnessWalls`.
- `building_stat`, `upgrade_stat` and `building_stat_vector_write` (code in `HarnessHousing`) are in data-tables.
- The `ManorCore` rules are one requirement in data-tables ("The shared game-call module needs no harness module"). `ManorCore` does not fit the name well; the lead may move it.
- `HarnessSteer` is in building-commands as assigned. It fits combat or squad control better.
- `load_pak_blueprint` (spec 18) is in building-commands.

## Probe scenarios are not used as checks

The `probe_*.py` scenarios are research tools. They record answers and do not fail on a wrong answer. I did not cite them as checks. Their commands are marked "Not checked yet" when no Python test covers them:
- manor-commands: `wagen_state`, `wagen_apply`, `wagen_revert` (`probe_manor_wagenburg.py`), the garrison hook (`probe_retinue_cap.py`), the success path of `manor_blueprint_add` (`probe_manor_module.py`).
- building-commands: `wall_pieces`, `wall_pieces_clear`, `steer_*` (`probe_steer.py`), `load_pak_blueprint`.
- raid-commands: `raid_state` (`probe_raids.py`).
- game-setup: both commands (`probe_claim_victory.py`; `test_fakegame_vassals.py` only stubs them).
- policy-commands: `menu_probe_*` (`probe_policy_followups.py`).
- encampment-commands: `encampment_regions` and the pak spawn in the game (`probe_wagenburg.py`).
- combat-commands: `unit_stats`, `set_unit_stat`, `combat_hook`, `unit_probe`, `prop_spawn` (used by `combat_levers.py`, `probe_custom_unit.py`, `probe_cart_block.py`; no test).
- data-tables: `building_stat` content, `upgrade_stat` (`probe_extension.py`).

## Legacy claims dropped

Engine facts and spike results stay in the legacy notes (rule D2 and D5 of the design).
- Spec 12: Keep needs 40 builder units, storage rules of the base game, the Storehouse and Granary table values.
- Spec 14: a wall made by `wall_make` does not block units; planner pieces do. Only the command behavior is in the spec.
- Spec 15: timings of the rebellion (waypoint wait of 100 to 150 s, march after about 650 s), the +2 families from the settle letter, tent slot findings.
- Spec 16: policy ids and effects; the PolicyMenu mod (other group).
- Spec 17: bailey rules (plots inside the ring) and the Commit button findings; spec 18: what a pak part can do; spec 31: the extension number plus 100 rule.
- Spec 25 and 29: A/B results, lever effects, custom unit rows, war wagon results. Only the harness commands that carry them are in the spec.
- Spec 26: "Endless goal stops the victory cinematic, 3 of 3". It is a game fact from a probe run, not a harness behavior with a check.
- Spec 30 and 32: wagon and tent mesh results, collision claims, invasion recommendation.
- Spec 10 spikes S1 to S9 parts outside my modules: `popup_state`, `close_popups` (S8), `show_message` and `read_message` (`HarnessUi`, S9), `tune_*` (`HarnessTune`), `send_letter`, `spawn_probe`. These are in `HarnessActions` but belong to H2 groups (or to no group). `spawn_probe` has no spec in my files.

## Capabilities dropped

None. `game-setup` and `encampment-commands` have only 2 requirements because the modules are small (63 and 166 lines).

## Doubts

- Legacy spec 12, 14, 15 and 16 mention more items than the code does now (for example the criteria matrix). I checked only commands in `mod/HarnessActions/Scripts/main.lua`.
- Some limits (for example 70000 for `building_stat`, 400 wall pieces) come from code constants. They can change; the fake-game tests do not pin all of them.
- The "A rebuild in the game uses the lower cost" scenario in building-commands relies on the description of `rebuild_cost.py`. I read its header and imports, not the whole assert logic.
- `harness/scenarios/manor_storage*.py` are HIDDEN (they need the mouse) but have `expect` checks and fake-game tests. I treated them as real checks.
- `HarnessGarrison` has no test at all. The only use is `probe_retinue_cap.py`.
- Wording "ok" and "not ok" stands for `ok` true and false in the JSON reply.
