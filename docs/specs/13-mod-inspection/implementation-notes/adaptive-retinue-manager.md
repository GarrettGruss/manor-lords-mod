# AdaptiveRetinueManager (EN, v2.6) (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\AdaptiveRetinueManager EN 381 3 2026-09-20T12-50Z 2GaWH48FA`. Nothing was run.
Files and SHA-256:
| File | Size | SHA-256 |
|---|---|---|
| `AdaptiveRetinueManager/enabled.txt` | 0 | (empty file) |
| `AdaptiveRetinueManager/scripts/config.lua` | 266 | `e494a7c4bd62a963ea5ba856dc7fc7d8cc86eccb0792f799bd53f2acc77372f4` |
| `AdaptiveRetinueManager/scripts/main.lua` | 180803 (4057 lines) | `915b3a98d739879178e0e2534cc1a442c8c7480a14f0b5f1b16c2af2e2e3eb31` |
| `AdaptiveRetinueManager/native_bridge/AdaptiveRetinueNativeBridge.dll` | 12800 | `803d67c42e36ada4f501c5b83b354e011b3804acfffd37533c47d99d594be1d5` |
No README. The header says v2.5.2, the load message says v2.6 "BULK ACTIONS" (main.lua:4057). It is a "companion UI for AdaptiveRetinue" (main.lua:2), a mod that is NOT in this download.

## What it does for the player
A custom in-game panel (Ctrl+F10) to manage several Retinue squads: list squads and members, recruit one man or "fill to 36" into a chosen squad, open the vanilla wardrobe for a member of an older squad, check and upgrade armor for one member or a whole squad ("Upgrade All"), delete a squad (confirm twice). Arrow keys and Esc work as a fallback (main.lua:20-29, 4027-4033).

## How it works (Lua)
- Panel drawn with UMG objects built at run time: `StaticConstructObject` of `UserWidget`, `WidgetTree`, `CanvasPanel`, `Border`, `TextBlock`; hit boxes by mouse click (`RegisterKeyBind(Key.LEFT_MOUSE_BUTTON)`) (main.lua:2470, 3700-3730, 4032).
- Retinue squads: `getAllCommandedSquads()` filtered by `squad.squadType == 3` (Retinue) sorted by `ID` (main.lua:174-197). Squad fields read: `ID`, `assignedRecruits`, `rallyingStatus` (0 disbanded, 1 rallying, 2 rallied), `maxSize` (default 36) (main.lua:199-210).
- Selection: `PawnCPP:selectSquad(id, true, false)`, `deselectSquad`, `isSquadSelected`, `selectedSquads` (main.lua:614, 543).
- Delete: `PawnCPP:addRemoveSquadRequest(id)`, then verify by re-reading squads, then set `shouldUpdateArmyUI` and `shouldUpdateArmyListUI` and call `updateCommandedAndEnemySquads()` (main.lua:763-800).
- Recruit: it presses the vanilla `retinueEditor_C` "recruit nobles" button event by Lua call (`ed:BndEvt__retinueEditor_recruit_nobles_...()`, main.lua:1862), finds the new member object, then MOVES it to another squad. The editor is `MainUICPP_C.retiuneEditor_C_0` (main.lua:238, 258).
- Armor: calls `ed:BndEvt__retinueEditor_upgrade_armor_funds_...()` and `ed:isCurrentRetainerUpgraded()`; normal game cost applies (main.lua:1003-1160).
- Reload hook: `playCinematicSequence` (main.lua:4048). Trace hooks on `spawnCompleteUnit`, `spawnArmy`, `updateSquadEquipmentStats`, `updateRecruitmentPool`, `getRecruitmentPool`, `getSquadByID`, `GetSquadUnits`, `getAllSquads`, `addRetinueSquad` for a debug trace only (main.lua:3602-3618).

## How it works (native DLL)
Why a DLL: the Lua side proved (comments at main.lua:1172-1190, 1300-1420) that `Squad` structs returned by `getAllCommandedSquads()` are COPIES. Writing `assignedRecruits` or `equippedRecruits` in them does not stick. The authority was `RTSMultiEngineCPP.squads` (a `TArray<FSquad>`) in 0.8.104. Only native code could change it.
- Lua gets the address of the `squads` FProperty by `rts:Reflection():GetProperty("squads")` and the offsets of `Squad.ID`, `assignedRecruits`, `equippedRecruits` by `ForEachProperty` on `/Script/ManorLords.Squad` (main.lua:1925-1960). It writes them in a config file `native_bridge.cfg` (hex addresses, source id, target id, new member address). Then it calls `package.loadlib(dll, "luaopen_AdaptiveRetinueNativeMoveMember")` and the DLL writes a status file (main.lua:1895-1990).
- DLL strings (read only): exports `luaopen_AdaptiveRetinueNativeBridge`, `...MoveMember`, `...Restore`; it resolves these UE4SS exports by `GetProcAddress`: `FProperty::GetOffset_Internal`, `GetElementSize`, `FArrayProperty::GetInner`, `UObject::ProcessEvent`, `GetValuePtrByPropertyName(InChain)`, `FMemory::Realloc`. Messages: "RTS-SQUADS OK v12", "ERR bad RTS.squads header v12", "MOVE OK", "MOVE PARTIAL", "PATCHED before ProcessEvent", "RESTORED editor". Windows imports: `CreateFileW`, `ReadFile`, `WriteFile`, `GetModuleHandleW`, `GetModuleFileNameW`, `GetProcAddress`, `CloseHandle`. No network library, no process creation.
- So the DLL edits the game's squad array in memory (reallocating the member arrays) with a hand-made layout check ("header v12").

## Game version and signs it is stale
Target 0.8.104 (header comments). Against the 0.8.111 jmap:
- Present: `PawnCPP:selectSquad(squadID: SquadHandle, resetSelection, playSounds)`, `deselectSquad`, `isSquadSelected`, `addRemoveSquadRequest`, `updateCommandedAndEnemySquads(includeFleeing)`, `shouldUpdateArmyUI`, `shouldUpdateArmyListUI`, `selectedSquads`, `MainUICPP_C.retiuneEditor_C_0`, `retinueEditor_C` with `squadID`, `retinue`, `selectedRetainer`, the `recruit_nobles` event, `Squad.squadType` (enum value 3 = Retinue), `rallyingStatus`, `maxSize`, `ID`, `assignedRecruits`, `equippedRecruits`, `PawnCPP:updateRecruitmentPool`, `getRecruitmentPool`, `getSquadByID`, `GetSquadUnits`, `getOrderedSquadList`.
- **Missing in 0.8.111:** `RTSMultiEngineCPP.squads` (the RTS class now has a `SquadComponent` component instead, whose reflected properties are only `PlayerSquadUIOrder` and `OwnerEngine`), `RTSMultiEngineCPP:updateSquadEquipmentStats`, `PawnCPP:addRetinueSquad` (a new `PawnCPP:InitializeEmptyRetinueSquad(Region)` exists), `PawnCPP:getAllSquads`.
- Result: the native bridge cannot find `RTS.squads` (the Lua side stops with "RTS.squads FProperty not found", main.lua:1946). Recruit relay and fill do not work. Panel, selection and delete may still work. Not tested.
- This is the best evidence that squad storage was moved in the engine code between 0.8.104 and 0.8.111. Our baron-model note says "squads live in native storage"; this adds that the storage is now behind `SquadComponent`.

## Risk review
- Native DLL (12.8 KB). It was not run. From strings: reads and writes only its own `native_bridge.cfg` and `.status` in its folder. It writes raw game memory (`TArray` realloc) at addresses that Lua gives it. A wrong address or layout gives a crash. In 0.8.111 the Lua precheck should stop it before any write, but this is not tested. The strings "PATCHED before ProcessEvent" and "RESTORED editor" suggest it still holds old code that patched the editor object and called `ProcessEvent`. The v1.4 Lua says it never calls that path any more (main.lua:1878-1890). This is read from strings, not from disassembly.
- Lua: `io.open` for the cfg and status files only (main.lua:1967, 1981). No network, no `os.execute`.
- Wide use of `pcall` hides errors. The author used log traces (`P`), not our `HarnessLog`.
- License: none given. The mod needs the companion AdaptiveRetinue (not included) for the extra squads.

## Lessons for us
- Squad steering: **no move or attack call** appears in the code. All squad calls are selection, delete and recruit. This agrees with baron-model.md. It also confirms that `Squad` values from Lua are copies and cannot be written (our S11 note said so for `getSquadByID`).
- The only known route to write squad data is native code against the squad array, and in 0.8.111 that array is behind the C++ `SquadComponent`. We should not build on it.
- Jmap leads (not used by this mod, not tested, flagged as new): `SquadComponent:SetPushStance(Squad, NewStance, bChangedByMorale, bPlayVoiceline)` and `SetBehaviourStance(Squad, NewStance, bPlayVoiceline)` are reflected. `EBehaviourStance` is Neutral, Aggressive, Defensive. `EPushStance` is GiveGround, StandGround, Push, MissileAlert, Balanced. `SquadComponent:RequestDisbandSquad`, `RequestRemoveSquad`, `GetSquad`, `GetSquadUnitCount`, `getSquadLeader`. Also `PawnCPP:measureSquadPower(squadID, onlyMelee)`, `measureSquadPowerFromTemplate(UnitTemplate)`, `getSquadsNearPos`, `RTSMultiEngineCPP:FindGoodSquadMoveTargetNear(Location)`. A stance call on an AI squad is a possible weak steering tool. `measureSquadPower*` returns a float: a test can use it to compare armies.
- `squadType` 3 = Retinue. `ESquadType` is None, Militia, Mercenaries, Retinue, Bandits, Wildlife, Merchants, Raiders. Useful for filtering census data.
- Retinue limit: the mod assumes 36 per squad (`maxSize` 36); see larger-formations.md for the 12/24 limits in code.

## Test idea for the harness
Scenario `squad-stance-ai`: after `lord_spawn_army` and a challenge (HarnessLords), call `SquadComponent:SetBehaviourStance` with `Aggressive` and then `Defensive` on one AI squad (handle `{Value=id}`), read `Squad.behaviourStance` through `SquadComponent:GetSquad`, and check the AI debug log for a changed decision. First only the read-back; battle effect second. Never call a function that saves.
