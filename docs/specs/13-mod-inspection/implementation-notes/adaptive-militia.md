# AdaptiveMilitia 1.1 (inspection note)

Date: 2026-10-11. Source: `C:\Users\garre\Downloads\AdaptiveMilitia 1.1 370 1.1 2026-09-13T16-17Z ihTXA3pYm`. Nothing was run.
Files: `enabled.txt`, `README.txt`, `scripts/config.lua`, `scripts/main.lua`. Comments are in Russian. Line numbers are per file. The README and a header say "Version 1.0" while the folder name says 1.1.

## What it does for the player
It removes the game's cap on militia squads. The game lets the player raise a free number of militia squads (5). Above that, the mod adds squads with hotkeys: Ctrl+F1 footmen (`militiaFoot`), F2 spearmen (`spearMilitia`), F3 polearm (`militiaPole`), F4 archers (`bowMilitia`), F6 crossbow (`crossbowMilitia`). F5 is avoided (quick-save). The army bar cards shrink when there are many squads. (README.txt)

## How it works
- Count: sum of squads from `PawnCPP:getAllCommandedSquads()` whose `squad.unitType` is a militia name (main.lua:34).
- Below the limit the game does the work. At the limit the first press is absorbed by the game, later presses call `PawnCPP:addMilitiaSquad(region, FName(unitType))` on the region the player looks at (`updateCurrentRegion`, `getCurrentRegion`, main.lua:73-116). The region must have `ownerPawn.isMainPlayer`, else a message is shown with `playEventMessage`.
- Hooks (RegisterHook) on two Blueprint events, registered 5 s after each save load:
  - `/Game/UI/HUD/addSquadCard.addSquadCard_C:BndEvt__addSquadCard_unitButton_..._OnButtonReleasedEvent__DelegateSignature` (the recruit button; main.lua:124-129).
  - `/Game/UI/Army/skillButton.skillButton_C:BndEvt__Button_44_..._OnButtonReleasedEvent__DelegateSignature` (disband, button id 0 or 12; main.lua:137-145).
- Load detection: hook on `/Script/ManorLords.PawnCPP:playCinematicSequence` (main.lua:165). Hooks are removed and added again on the second load.
- Cards: `MainUICPP_C.unitCards[i].thumb:SetDesiredSizeOverride({X, Y})` (main.lua:50-62), from 83 x 166 down to 60 x 120.
- No DataTable, no save call.

## Game version and signs it is stale
Target 0.8.104. Against the 0.8.111 jmap:
- Present: `PawnCPP:addMilitiaSquad(Region, unitType)`, `PawnCPP:canAddNewMilitiaSquad() -> Bool` (new find: this is probably the function that enforces the limit), `updateCurrentRegion`, `getCurrentRegion`, `playCinematicSequence`, `Squad.unitType`.
- **Missing: `/Game/UI/HUD/addSquadCard` (no object with this name), `/Game/UI/Army/skillButton`, and `MainUICPP_C.unitCards`.** The army UI was rebuilt. The jmap has `W_HUD_ArmyPanelV2` (with `AddSquadButton` click event), `W_HUD_ArmySkillButtonV2`, `W_HUD_ArmyUnitGrid`. So both hooks and the card code fail in 0.8.111. The hotkeys still call `addMilitiaSquad`, but the "first press is absorbed" logic depends on how the new UI works.
- Verdict: stale in its UI part, probably usable as an idea only.

## Risk review
Pure Lua. No file, network or process access (grep). The hotkeys write game state (new squads, with their equipment cost handled by the game). A failed hook only logs. License: none given ("Standalone original code").

## Lessons for us
- Raids and enemy scaling: none. Unit stats: none.
- Squad creation: `addMilitiaSquad(region, template)` is a reflected call that makes a squad for a pawn in a region. We have not tried it for an AI pawn. It could give an AI lord a militia squad drawn from a region (cost, recruits and equipment rules unknown). Compare with `spawnArmy` (no recruits).
- `canAddNewMilitiaSquad` is a candidate for a hook that lifts the cap in a clean way (post-hook that changes the return value). UE4SS return override from Lua is not verified.
- Writing to `Squad` structs is not needed here: all changes go through game functions. This is the approach we should use.
- The UI rebuild shows that BP UI hooks break across versions. Prefer `/Script/ManorLords.*` C++ functions for harness commands.

## Test idea for the harness
Scenario `militia-cap`: call `addMilitiaSquad` for the player 6 times (6 > the free limit 5) in a region the player owns. Assert (range): the number of militia squads is 5 or 6 or 7 after each call and that `canAddNewMilitiaSquad` flips to false at the cap. This tells if the cap lives in the UI or in the function. Run it on a private save copy.
