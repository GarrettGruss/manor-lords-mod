# DepositDecal check (run 20261022-024931-f585, slot 1, noop, read only)

- Class `/Script/ManorLords.DepositDecal` exists (a DecalActor subclass). Struct `SavedDeposit` also exists.
- Live objects of `DepositDecal` in the loaded map (Jagged_Cliffs): 0. Also 0 for subclasses, `ResourceDeposit`, `BP_Deposit_C`.
- CDO fields (own): `depositedGood` (Good struct: Type 0, amt 0, belongsTo invalid), `Limit` = 1, `depositType` = "None", `bRichDeposit` = false, `Decal` (DecalComponent).
- So an amount-like field exists in the class (`Limit`, `depositedGood.amt`), but no instance was readable. No region or ResourceNode link field on the class.
- Other counts: `ResourceNode` 35, `Resource` 277 (Resource_Stone_C etc.).
- Salt deposit in Nusslohe: not matched (no instances).
- Open: instances may exist only at some game state (for example the deposit map mode) or not in this save. A mod that does FindAllOf("DepositDecal") may find none here.

## Resource objects (run 20261022-025607-3ef9, slot 1, Jagged_Cliffs, read only)

Retry after a guard abort in run 20261022-025243-51f5 (slot 0 fixture files were in the save folder).

- `FindAllOf("Resource")` returns 278 objects (277 before). All are actors under `ResourceNode_*` or the level.
- Per class (count, amt min..max, capacity max, Type):
  - Resource_Stone_C 44, amt 2..144, cap 0, Type 15
  - Resource_Fish_C 22, amt 0..35, cap 35, Type 30
  - Resource_Berries_C 24, amt 1..7, cap 17, Type 171
  - Resource_Mushrooms_C 64, amt 0..2, cap 8, Type 279
  - Resource_Eel_C 6, amt 65, cap 65, Type 32
  - Resource_Handcart_C 21-22, amt 1, cap 0, Type 218
  - FallenTreeBP_C 96, amt 1..20, cap 0, Types 16, 237, 257
- `Resource` fields: `Region` (BP_Region_C), `belongsTo`, `resType`, `DisplayName`, `amt`, `Type` (good id), `capacity`, `Inventory`, `iconTint`, `bSeasonal`, tree fall fields. No rich flag. No iron or salt class, no value near 1194.
- `Resource` functions: TreeHitGroundEvent, startFalling, setFalling, removeResource, getMaster.
- `ResourceNode` (35) fields: resourceClumps (list of Resource), ResourceZoneDecal, PaperMapDecal, masterPtr, and so on. No amount.
- After 1 game day (clock 8214 to 8251): `DepositDecal` count still 0.
- Conclusion: salt and iron deposits are not `Resource` actors here. Stone `amt` is a per-actor amount.
