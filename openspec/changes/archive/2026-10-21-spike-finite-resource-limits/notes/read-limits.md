# Read limits (task 1.1)

Probe: `harness/scenarios/probe_finite_limits.py` (hidden, read only in steps `classes` and `buildings`). Runs `20261021-050946-ee6d`, `-051805-9226`, `-051859-f8a3`, `-052032-51df`, `-052220-1d6f`. Fixture `base` (region Nusslohe, map Jagged_Cliffs), slot 1. No save call.

## Facts
- The fixture has no mine and no deposit: `RTSMultiEngineCPP.deposits` is empty, the count of `DepositDecal`, `Ore` and `ResourceNodeProperties` objects is 0, and no `ResourceNode` clump is iron or salt (35 nodes: berries, fish, stone, mushrooms, eel). No other fixture was checked.
- The amount of one deposit unit: the resource clump classes `Resource_Iron_C`, `Resource_Salt_C`, `Resource_Clay_C` (`engine.ironResourceBP`, `saltResourceBP`, `clayResourceBP`) have the int properties `amt`, `capacity`, `Type`. Class defaults (iron and salt): `amt` 10, `capacity` 0, `Type` 14 (iron ore) and 145 (salt). So the per-deposit amount is `amt` on the clump, and the engine array `deposits` (struct `Ore` with `amt`) is the other candidate. Neither was read on a live mine.
- `Region` (`BP_Region_C`) has no property or function with "unlimited", "infinite", "deposit" or "resource" in its name. Its limit functions are only `setProductionLimit`, `setProductionUnlimited`, `isProductionLimited`, `getProductionLimit` and the crafting-consumption twins.
- A building has `IsMineBuilding`, `getNearestResource`, `CanLimitProduction` and the bool `workAreaLimited`. These are the next things to read once a mine exists.

## Not verified
Where a mine stores its remaining deposit; the finite flag `bIsLimitedResource` (known only from an old jmap note, no live object found).
