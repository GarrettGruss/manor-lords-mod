# Part A: gun-like look and the recruit screen

Date: 2026-10-18.

## Look (no new assets)
- The held weapon mesh comes from `VAMP_Variations` of the item (a name, for example `MGGN_Weapon_Crossbow`). The `handCannon` clone still shows the crossbow. No firearm mesh name is known in the item table (no gun, musket, pistol or cannon in item names or variations).
- Pak asset names (`pakmod.py find`): no firearm mesh and no firearm effect. Gun sounds exist: `NotStronghold/Sound/Battle/ArrowDraw/Battle_Game_Weapon_Aim_Pistol_Holster_Pull_Out_Draw_Gun_Handling_Light_1`, two `Game_Weapons_Foley_Gun_Handling_Light_Metal_Rattle_..._Dry_Bright` files, `Sound/Battle/ArrowHits/BulletImpact_GUNS03_59_5` and `Trample/BulletImpactBody_BW_54388`. Smoke effects exist: `Assets/Explosions/Particles/P_Smoke4_2` and `P_Smoke5_2`. A torch projectile mesh exists: `ManorLords/Projectiles/torchProjectile`. The voice tag `eng_kabooka` is the English militia voice, not a gun.
- Projectiles are native: `PMaster:shootProjectile` and `RTSMultiEngineCPP:updateProjectileManager`. We found no data field that picks the projectile. It follows the weapon stance.
- Verdict: a true gun look is BLOCKED without new assets. A stand-in is the crossbow mesh. Gun sounds and smoke exist but nothing in data connects them to a unit. That is not tested.
- A screenshot of the spawned squad was not useful (the UE4SS console covered the game window in the run).

## Recruit screen
- The player recruit panel `W_HUD_ArmyRecruitPanel` holds 5 fixed cards (`W_HUD_ArmyRecruitCardV2`): `Recruit_Foot`, `Recruit_Spear`, `Recruit_Pole`, `Recruit_Bow`, `Recruit_Crossbow`. Each card has a `unitType` name. Read in the live game (run `20261018-112958-4404`): `militiaFoot`, `spearMilitia`, `militiaPole`, `bowMilitia`, `crossbowMilitia`.
- The screen does not list the rows of `DT_UnitTemplates`. It has 5 widgets. A new row does not appear by itself.
- Verdict: recruitable BLOCKED by data alone. Two routes, both untested (no mouse): (a) a widget pak that adds a sixth card with `unitType` set to the new row (spec 16 widget pak method); (b) write `unitType` of an existing card to the new row name. The native click handler may use `unitType`, or a fixed index. That is not known.
- `minHouseLv`, `cost` and the recruit stock are native.
