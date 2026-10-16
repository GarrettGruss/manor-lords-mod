# Why the Siege Camp (483) is never built (2026-10-14)

Spec 18, issue #94. Game 0.8.111, fixture `base`, single player. 4 game launches (runs `s94-1` to `s94-4`, `noop --keep-open`, driven by `harness/tools/s94_drive.py`).
No save function was called. The AES key came only from the environment (PowerShell, one command). The game is closed. `~mods` is removed.

## Answer in short

- The Siege Camp site is not an unbuilt normal site. It has no way to be built: no cost list, no construction mesh, a placeholder construction Blueprint, and it never joins a region.
- `Region` invalid is NOT the cause alone. A vanilla, constructed Bandit Camp (type 100, the other `Siege` function row) also has `Region` `<invalid>`. Siege-function camps are region-less by design. Builders, however, come from a region.
- Placing the camp well inside the player's region on open grass gives the same result as the first run: `Region` invalid, never built.
- Three things were tried and did not build it: a Region write, a function change in a pak, and 10 game days with timber and planks.
- Writing `Data.constructed = true` makes `IsConstructed` true. The finished camp has no visible mesh (a bare dirt patch). Siege use (equipment near friendly units) needs an army and was not tested.
- Verdict: the reason is proven only in part. Not proven: which code decides that a camp gets no region. Evidence: see the table. The issue is not closed.

## Static comparison (extracted `buildingStats`, `DT_ConstructionBPs`)

Script: `harness/tools/s94_row_compare.py <json> <rows...>`. Rows 483, 107 (Settlers Camp, builds), 87 (tent, builds), 100 (Bandit Camp).

| Field | 483 Siege Camp | 107 Settlers Camp | 87 tent | 100 Bandit Camp |
|---|---|---|---|---|
| `buildingFunction` | Siege | Default | Temporary | Siege |
| `constructionCost` / `constructionGoods` | 0 / empty | 250 / empty | 0 / empty | 0 / empty |
| `constructionMeshAsset` | None | `SM_MERGED_C_outpost` | none seen | none |
| `bCircularBorder`, Bounds | true, 1200 x 1200 | false, 1200 x 800 | false, 1200 x 800 | false, 1200 x 800 |
| `BuildingCategory` | Military | Military | Gathering | Gathering |
| `needsRoad` | false | false | false | false |
| `bVisibleInUi` | false (true in the pak) | true | false | false |
| `maxHp` | 100 | 50 | 5 | 5 |
| row in `DT_ConstructionBPs` | YES, `C_House_LV2_Bpart_B_C` (a house part, a placeholder) | not checked | no | not checked |

So the data row has no goods and no construction mesh. The tent has the same (cost 0, no goods) and is built by builders in about 4 days. The difference is therefore not the cost. It is the region (builders) and the placeholder construction Blueprint.

## Live comparison (same run, same spot type)

Camera centred on the village (`centre_camera_on`), real click at window fraction (0.33, 0.33): open grass, white ghost, inside Nusslohe (the player region, the control placed a HitchingPost there and got `Region` Nusslohe). Screenshots: `runs/s94-1/screenshots/g2.png` (ghost), `runs/s94-2/screenshots/after10.png`.

| Read | 483 site | HitchingPost (30) control |
|---|---|---|
| `Region` | `<invalid>` | Nusslohe |
| `ownerPawn` | the player pawn | the player pawn |
| `constructionGoods` | empty | empty |
| `Resources` | 2 parts `res_16_0`, `res_16_1` (timber slots) | none |
| parts | 4 | 1 |
| `Data.constructed` after 10 days (timber 100, planks 100 given) | false | true |
| in `Region:GetBuildings()` | NO (list has 24 masters, not this one) | yes |
| `getBuildingCount(483)` | 0 | 1 (type 30) |
| `buildingFunction` | 17 (Siege) | 11 |

A property diff of both masters (`harness/tools/s94_propdiff.py`) also shows: the 483 master has `ambiences` `fireplace` and `flag`, circular `finalBorder` points and storage limits 500, which the control has not.

## Experiments

1. Region write (run 2): new command `master_set_region` (HarnessParts) writes `site.Region` from Lua. Read back: Nusslohe. After 10 game days: still not built, `getRegionBuilders` empty, still not in `GetBuildings`, `getBuildingCount(483, true)` 0. The `Region` property is not the region's building list. A bridge write of an object path is refused (needs a UObject, so a mod command is needed).
2. Pak variant `s94fn` (run 3): row 483 `buildingFunction` Siege to Default (new `s65_edit_json.py enum`). The master got function 0, but `Region` stayed invalid and 10 days with timber gave no build. So the Siege function is not what blocks the region.
3. Vanilla Bandit Camp (run 3): `spawnBanditCamp` made a type 100 master. `constructed` true, `Region` invalid, 17 parts, owner `PawnCPP_AI`. So a region-less camp is normal and the game sets `constructed` directly (no builders).
4. Finish by write (run 4): new command `master_finish` writes `Data.constructed = true`. `IsConstructed` becomes true and stays so for 5 game days. No visible mesh at the site (`runs/s94-4/screenshots/finished.png`: bare dirt). The two timber slots stay.

## Reading

- The camp is "Work in Progress" content: no cost, no construction mesh, a house part as construction Blueprint, no region. It cannot be built through the normal builder path, and nothing else builds it in this mode.
- A function that adds a master to a region is not known. Region functions seen: `GetBuildings`, `getBuildingCount`, `getRegionBuilders`, `HasConstructionYard`. None adds a building. Engine functions to look at next (not called, signatures unknown): `setPlacedBuilding`, `finishSpawningSoloBuildingAsync`, `setupBuildings`, `SetupBuilding` on the master.
- Not tested: placing next to an army, a real siege use, a data change of the construction Blueprint row 483 (for example to a vanilla camp construction Blueprint) or a cost.

## Changes outside the repo

- Game folder `Paks\~mods\`: `siege483_P.pak` (runs 1, 2, 4) and `s94fn_P.pak` (run 3), each removed after its run. `~mods` does not exist now.
- `modtools/work` (git-ignored): `s94fnjson/`, `s94fn/`, `out/s94fn_P.pak`. The test pak `s94fn_P.pak` is not committed.
- The `mod.log` of the game folder was not edited by hand.

## Tools added

- `harness/tools/s94_drive.py`: village centre, camera, ghost (screenshot without click), place, masters, give, days, mod commands, for a `--keep-open` run.
- `harness/tools/s94_bridge.py`: send bridge ops to a keep-open run (the MCP bridge points to another folder).
- `harness/tools/s94_propdiff.py`, `harness/tools/s94_row_compare.py`: compare two masters or rows.
- Commands `master_site`, `master_set_region`, `master_finish` (HarnessActions 48).

## Trap

- A permission rule refused `export` or an inline `VAR="$(cat file)"` in Git Bash. The AES key was set in PowerShell (`$env:MANORLORDS_AES_KEY = ...` in the same command as `pakmod.py build`). Without the key the build still wrote a pak but did not verify it, and the pak file was missing.
