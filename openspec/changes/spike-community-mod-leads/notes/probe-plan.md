# Probe plan: community mod leads

Issue #280. Status: probes are written and pass the fake game tests. None has run in the real game yet.

All probes are hidden test scenarios (`HIDDEN = True`). They use named commands only (`HarnessLeads`, through `HarnessActions`). They never call a save function and never use raw Lua eval. Each probe writes `probe.jsonl` and metrics in `runs/<id>/`. Read `runs/<id>/summary.json` and `metrics.json` first.

Back up the save folder before the first real run. Run one probe at a time, because a call may crash the game.

New commands (`mod/shared/HarnessLeads/HarnessLeads.lua`, fake game tests in `harness/tests/test_fakegame_harnessleads.py`): `lead_unit_gear`, `lead_stance`, `lead_spawn_unit`, `lead_squad_camp`, `lead_mesh_list`, `lead_mesh_swap`.

## 1.1 R3 real loot
- Run: `uv run python harness\run.py --scenario probe-lead-loot --fixture manor-bailey --slot auto`
- Does: spawns one bandit squad, reads `GetEquippedID` for slots 0..3 of each unit (alive, then dead), kills the squad, puts 5 of good 1 into the manor with `manor_put` (`addToInventory`).
- Answers the lead: `gear_numeric_alive` and `gear_numeric_dead` above 0 means the equipped ids can be read, also after death. `gear_other_*` above 0 means the call form is wrong (see the error text in `probe.jsonl`). `manor_stock_gain` equal to 5 means goods move.
- Not covered: the map from equipped id to a good. Read the ids in `probe.jsonl` for that.

## 1.2 Stances
- Run: `uv run python harness\run.py --scenario probe-lead-stance --slot auto`
- Does: new AI lord, war, one army, challenge. Calls `SetBehaviourStance` aggressive, then defensive on the first squad. Reads `Squad.behaviourStance` and the squad centre after each call. Screenshots `stance-1-aggressive`, `stance-2-defensive`.
- Answers the lead: `call_ok_*` is 1 and `stance_after_*` changes (0 neutral, 1 aggressive, 2 defensive) means the call works. `moved_aggressive` against `moved_defensive` shows if the squad behaves differently. The AI may overwrite the stance in the next tick: compare with the read after the wait.

## 1.3 Unit growth
- Run: `uv run python harness\run.py --scenario probe-lead-growth --slot auto`
- Does: new AI lord, war, one army, challenge. Counts squads and units, calls `spawnCompleteUnit` 3 times (template `spearMilitia`, arrives in 0 days), waits 10 game seconds, counts again.
- Answers the lead: `spawn_calls_ok` 3 and `squads_after` greater than `squads_before` and `units_after` greater than `units_before` means the army can grow one squad at a time. If the squads are made but not listed in the lord, check `new_squads_seen` and the answer of the call in `probe.jsonl`.

## 1.4 Squad camp state
- Run: `uv run python harness\run.py --scenario probe-lead-camp --slot auto`
- Does: new AI lord with an army at war and no challenge. Reads `camp`, `campLocation`, `rallyingStatus` and `WeightedCenter` of each squad 3 times while the army waits, then starts a challenge and reads 2 more times.
- Answers the lead: compare `camp_set_wait*` with `camp_set_march*` and `camp_location_set_*`. A change between the waiting reads and the marching reads means the fields show the camp state. Constant values mean the fields are not used for this army.

## 1.5 Building mesh swap
- Run: `uv run python harness\run.py --scenario probe-lead-mesh --slot auto` (default fixture).
- Does: lists building mesh components, picks one and a mesh of another building, calls `SetStaticMesh`, records mesh path, bounds, collision flag and socket count before and after, then restores the old mesh. Screenshots `mesh-before`, `mesh-after`.
- Answers the lead: `swap_ok` 1 and `mesh_changed` 1 means the swap works. `collision_same` 1 means the collision flag did not change. The collision shape itself is not proven by this flag: use the bounds (`extent_x_*`) and, if needed, a follow-up that walks a unit into the building.
- Limit: the screenshot shows the current camera. The swapped building may be off screen. `probe.jsonl` has its position.
- The probe loads the new mesh with `StaticFindObject`, then `LoadAsset`. It does not call `LoadAsset_Blocking`; if the loaded mesh is not found, the lead as written (`LoadAsset_Blocking`) needs a separate step.
