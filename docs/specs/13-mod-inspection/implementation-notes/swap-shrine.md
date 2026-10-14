# SwapShrine v2.09 (inspection note)

Date: 2026-10-14. Source: `C:\Users\garre\Downloads\SwapShrine 398 1 2026-10-02T09-38Z ZdGYlfI7s.zip` (Nexus file id 398). Local copy (git-ignored): `modtools/example-mods/swap-shrine/`. Nothing was run.
Archive: 24,716 bytes, SHA-256 `16c5765700684bd4617cab61cd8c96d6ff7703f381145c7254dcda4028749dcc`.
Files: `enabled.txt` (text "1"), `Scripts/main.lua` (108,772 bytes, 2,835 lines, SHA-256 `e4a6b0744a88e1f018001fa046fee22d54001a25294b971631d07baaeacb88f9`). No readme, no author, no license text.

## What it does for the player
With Ctrl+Shift plus a key (0 to 9 and some letters), the selected Shrine, or the Shrine placement preview, shows another mesh from the game folder (`J_Shrine5_luv`, `luv2` to `luv9`). The choice is saved per save file.

## Mechanism (UE4SS Lua only, no pak)
- It loads a game mesh on demand: `KismetSystemLibrary:MakeSoftObjectPath`, `Conv_SoftObjPathToSoftObjRef`, then `LoadAsset_Blocking`, for paths under `/Game/NotStronghold/Buildings/scanLuv/Jakob/SG_Shrine5/`. The assets are in the game paks but not loaded.
- It swaps the mesh on the Shrine's static mesh component: `SetMobility(2)` then `SetStaticMesh(mesh)`. For collision it reuses an existing hidden mesh component as a "collision proxy" (`SetCollisionEnabled(3)`, `SetRelativeScale3D`). It says it avoids runtime-created components and `ReregisterComponent`.
- It finds objects with `FindAllOf("StaticMeshComponent")` and `FindAllOf("SMBuildingMaster")`. The placement preview is the `DummyBuilding` component of `MyPawnCPP_BP3_C`.
- Persistence: its own text file per save, `ue4ss/Mods/SwapShrine/Saves/SwapShrine_<save>.txt` (mesh name and X, Y, Z per line). The save name comes from `MLSaveGame.saveName`. It learns that the game saves by hooking `IoHandler:SaveGameToSlot` and `SaveDataToSlot` (slot name is argument 2) and `MLGameInstance:RequestMenuSave` (log only). It only observes. It restores after load with `RegisterLoadMapPostHook` and `ExecuteWithDelay`.
- It writes a flag file `ue4ss/Mods/SwapShrineCost/retinue_recalc.tmp` for a "cost" companion mod that is not in the archive.
- Safety: at most 5 swaps per Shrine and session; `pcall` around calls; falls back to the original mesh.

## Game version and staleness
No version written. The archive is dated 2026-10, so it targets about 0.8.111. `MLGameInstance:RequestMenuSave`, `IoHandler:SaveGameToSlot`, `MLSaveGame`, `SMBuildingMaster` and `DummyBuilding` are names we use now. The mesh paths were not checked against our asset list. It looks current.

## Risk review
Pure Lua. It writes only under its own mod folder (fallback hard path `C:/Games/ManorLords/...` if the game folder lookup fails). No network, no process call. It hooks save functions but never calls them. Do not load it in a harness run: it would write files and slow the run.

## Lessons for us (specs 18 and 12)
- A Lua-only visual swap works on a finished building: `LoadAsset_Blocking` plus `SetStaticMesh`. For spec 18 (bailey buildings #68, siege camp #94) this can show another game mesh on an existing building without a pak. Collision stays that of the old shape unless a proxy is used.
- `LoadAsset_Blocking` by soft path loads an unloaded game mesh safely. (Our crash came from reading soft object fields in a row struct, not from this call. Probe one path first.)
- It adds no building, row or build path. It does not help #90/#65 (manor commit), #52 (walls) or #94 (a build path).
- The `DummyBuilding` component is the placement preview. We can read what the player is about to place, and swap its mesh.
- A mod that keeps state per save needs a file keyed by `MLSaveGame.saveName`. Our fixtures reuse one save, so reset such files per run.

## Test idea
Scenario `building-mesh-swap`: load the fixture, take one `SMBuildingMaster`, find its `StaticMeshComponent`, load an alternate game mesh with `LoadAsset_Blocking`, call `SetStaticMesh`, read the property back, and assert it names the new mesh. Take a screenshot before and after. Probe mesh paths only; never touch data table rows with soft objects.
