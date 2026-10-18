# Which host shows the Wagenburg (2026-10-18)

Spec 30, issue #229. Game 0.8.111, fixture `base`, single player, slot auto. No save function was called. No eval. `allow_eval` was not changed.
Probe: `harness/scenarios/probe_wagenburg.py` (hidden). Mod commands: `encampment_sites`, `encampment_regions`, `encampment_spawn`, `encampment_list`, `encampment_remove` (HarnessActions version 56, module `HarnessEncampment`).

## Runs
| Run | Pak | What |
|---|---|---|
| `s30-1` | `wagen` | First try. Host a worked. Host c was refused: the command parser of HarnessActions reads only a fixed list of fields, so the class path never arrived. Fix: each new command reads its own fields from the raw JSON. |
| `s30-2` | `wagen` | Host c in a neutral and an AI region, and host a. |
| `s30-3` | `wagen` | Host c in 2 neutral and 2 AI regions, host a, and 3 game days of bandit counts. |
| `s30-4` | none | Control for host a: the vanilla camp. |

Screenshots (git-ignored, in `runs/<id>/screenshots/`): `camp_near_n.png` (s30-2: the camp with the Wagenburg and the tent marker), `neutral_after_c.png` (s30-2), `ai2_after_c.png` and `ai2_after_s.png` (s30-3), control `camp_near_*.png` (s30-4).
A screenshot copies screen pixels. Windows of other game runs, which ran at the same time, covered parts of some pictures. The probe takes 3 aim points for each place, so one is usually clear.

## Host a: replace the mesh of the bandit camp (WORKS)
Method: a pak sets `BlueprintPath` of `buildingStats` row 100 (bandit camp, class `BM_HomelessTents_C`, shared with the tent row 87) to `BM_Wagenburg_C`. Only the row changes. The vanilla class `BM_HomelessTents` is not touched, so tents are not affected.

| Check | Result |
|---|---|
| Camp of the loaded fixture (the game rebuilt it at load) | Master type 100 at (-15171, 60853), 1 part, mesh `SM_Wagenburg`. Control without the pak: 17 parts (`SM_MERGED_C_HuntersTent` and more). So the part list of a saved camp follows the row at load. |
| Camp from the game's own spawn (`spawn_bandit_camp`, native `spawnBanditCamp`) | New master type 100, `constructed` true, 1 part, `SM_Wagenburg`. The game chose a random place. Screenshot `s30-2/camp_near_n.png`: the wagon ring stands where the camp message icon points. |
| Bandits still use the camp | Bandit units 18 to 36 after the spawn, as in the control. After 3 game days (speed 3) still 36, with the pak and in the control. Camp masters: 2 with the pak and 2 in the control, both constructed, same bandit lord. Not tested: a raid that walks out of the camp, and where the bandits stand in the ring. |
| Crash | None in 4 runs. |

Cost: one data row in the pak, plus the cooked Blueprint and mesh (3.4 MB).

## Host b: a new building row placed by the player (PARTLY)
- Row 4000 (clone of row 87, `BlueprintPath` `BM_Wagenburg_C`, `bVisibleInUi` true) loads: `building_stat 4000` reads `homeless_tents`, function 7, visible true.
- Placement needs the real mouse (`activateBuildingMode` plus a click). It was not done here: the task said to avoid the mouse. Spec 18 and 21 proved this path for new ids (123, 124, 125, 140, and ids up to 65536): placed, built, visible. The same asset should work. Open: one placement run with the mouse.
- No mouse-free route exists to place a new id (spec 18 `mousefree-placement.md`). `settle_region` makes only type 87.
- A menu card needs a UI pak and a category. Not tested.

## Host c: a plain actor spawned by Lua (WORKS)
Method: `encampment_spawn` spawns the loaded class `BM_Wagenburg_C` with `World:SpawnActor` at a ground point. The ground height comes from the camera trace. `load_pak_blueprint` loads the class first.

| Place | Result |
|---|---|
| Neutral region Wilde Wand (no owner) | Visible, ring in a clearing (`s30-2/neutral_after_c.png`). |
| Neutral region Kleine Nolle | Visible (`s30-3/neutral2_after_c.png`). |
| AI region Obere Wiese (owner `PawnCPP_AI`, settled) | Visible in an open meadow (`s30-3/ai2_after_s.png`). |
| AI region Hochweg | Alive, and it blocks the camera trace (ground height +250 cm), but it is not seen in the picture. The spot is in a dense forest, and the canopy hides the ring. Not a spawn failure. |
| After the spawns | All actors alive. `encampment_remove all` destroyed them (only actors that the mod spawned). |

Notes:
- The actor blocks the camera trace, so it has collision. Whether units path around it is not tested.
- A plain actor is not part of the game save. It is gone after a save and load. The mod must spawn it again on each load (a list of places in ModState). Not tested (no save call is allowed).
- It has no owner, no region, no building function and no hit points. The AI does not know about it.

## Redirect of the game's bandit camp spawn
Yes, by data (host a). The native spawn reads row 100 each time, so no hook is needed. Not tested: a camp that the game spawns by itself on the day tick. The probe uses the cheat call `spawnBanditCamp`, which is the same native function.

## Traps found
- `HarnessActions` `parseRequest` is a fixed list of JSON fields. A new command must read its own fields from `raw` (as `HarnessParts` does).
- `building_stat` accepts ids up to 70000 (`HarnessHousing.MAX_TYPE`). `HarnessBuild` and `HarnessPlace` stop at 600, so their helpers still refuse 4000.
- In Git Bash, set `MSYS_NO_PATHCONV=1` for `s65_edit_json.py` (JSON path) and for the UE editor (`/Game/...` becomes `C:/Program_Files/Git/Game/...` otherwise).
- `pakmod.py fromjson --to <name>` writes `buildingStats.uasset` at the top of the work folder. Move it to `ManorLords/Content/NotStronghold/Data/` before `build`.
- Set the AES key in PowerShell (`$env:MANORLORDS_AES_KEY`) in the same command as `pakmod.py build`.
