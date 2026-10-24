# Q1: rallied militia, deaths, bodies and items

Run `mc-1` (fixture `playtest-noai`, kept open, game 0.8.111, eval enabled in the game copy of UEBridge `settings.lua` and restored to `false`). The village is Riesenbuckel.

## Setup
30 spears (133) and 30 large shields (271) were added to the storehouse with `addToInventory`. Then `PawnCPP:addMilitiaSquad(region, FName("spearMilitia"))` made squad 19 (10 men, 12 to 16 later: the squad grows with the population). In about 6 game days the homes held one spear and one shield per man (12 of 30, later 16 of 30). Same result as the earlier spike.

## Rally: no reflected call found
| Try | Result |
|---|---|
| `PawnCPP:selectSquad({Value=19}, false, false)` | Works. `selectedSquads` is 1. A squad handle is a struct `{Value = id}`. The field is readable: `SMUnit.assignedSquadID.Value`. |
| `HandleClicked()` on the widget `Skill_Rally` (class `W_HUD_ArmySkillButtonV2_C`, `SkillType` 11) | Calls only `PawnCPP:setPlaceRallyingPoint()` (a hook saw it). It starts a rally-point placement mode. No unit changes. |
| Cursor on the ground (`ProjectWorldLocationToScreen` and `SetMouseLocation`; `getMouse3d` agrees), then `LMB_BP_pressed` and `LMB_BP_released`, also with a 0.3 s gap | No effect. The placement is native code that reads the real mouse button. |
| `SquadComponent:SetSkillActive(handle, 11, true, true)` | Returns false. The same call with skill 9 (sprint) returns true and `IsSkillActiveForSquad` becomes true, so the call is valid but Rally is not a toggle skill. Sprint was set back to false. |
| `SquadComponent:CanRallySquad(handle)` | true |
| `IsSkillVisibleToPlayer(handle, n)` for n = 1 to 14 | Only 11 (Rally) is visible for a militia squad. |

A real rally needs the real mouse: one click on the ground after the Rally button. `harness/runlib/osinput` can do it. The lead asked for no mouse, so it was not done. The units stayed `isSoldier = false`.

## Equip and unequip on a living unit
- `SMUnit:equip(itemId, true, false)` puts the item into its slot: 133 goes to slot 1, 271 to slot 2 (read with `GetEquippedID(slot)`, slots 0 to 3).
- `SMUnit:unequip(slot)` returns true and clears the slot (slot 1 went from 133 back to 0). So a mod can remove a weapon from a living unit.
- Equip changes no stock: homes, storehouse and `getStockOfGoodIncludingEquipped` were the same after 16 units got spear and shield.
- The gear is cosmetic for a villager. After about 1 game day most units were back in civilian gear (slots 1 and 2 empty). Only 2 of 13 still showed 133 or 271.
- Argument counts from the bridge errors: `equipFromTemplate` 3, `GetItemEquipmentSlot(item, out)`, `isEquipped(slot)`.

## Death of 3 militia men (`just_die`)
Before: squad 19 = 16 men, families 8, residents 24, `Region.corpses` 0, homes 16 spears and 16 shields (store 14).

| After `just_die` on 3 units | |
|---|---|
| Bodies | 3 (`dead = true`), all 3 in `Region.corpses` |
| Squad size | 16 to 13 |
| Residents | 24 to 21 |
| Families | 8 to 8 (the family record stays) |
| Home stock | 16 to 13 sets after about 1 game day. Storehouse 14 to 17. Region stock stayed 30 / 30. |

The weapons of a dead man went back to the storehouse. None were lost. The bodies carried no militia gear, because the units had only civilian gear (see the revert above). A body with real rallied gear was not tested, because no rally was possible.

## Hide the bodies
`SetActorHiddenInGame(true)` on the bodies and `Region.corpses:Empty()` (3 to 0): no crash in about 9 game days, and none in 20 more game days.

## Disband (dismiss)
- `SquadComponent:RequestDisbandSquad({Value=19})` and `PawnCPP:disbandSquad({Value=19})` return without error and do nothing (`commandedSquads` stays 1, the men stay in the squad).
- `HandleClicked()` on `Skill_Disband` did not remove the squad either (probably a confirm step in the UI).
- Home weapons stayed 16 / 16. Whether weapons go back to homes on a real disband is not verified.

## Not verified
Real rally (needs the real mouse), items on the body of a rallied man, weapons on a real disband, whether hidden bodies are invisible (no picture).
