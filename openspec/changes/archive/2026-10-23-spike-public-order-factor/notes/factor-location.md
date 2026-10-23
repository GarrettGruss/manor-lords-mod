# Factor location (static search, task 1.1, question 1)

No game was run. Sources: the UE4SS jmap (read only), `modtools/work/ua-scan` (DT_Approval strings), the legacy notes `homeless-rebellion.md` and `jmap-findings.md`.

## Findings

- The factors are an ENUM plus a CONFIG float array in native code. They are not a data table row, not a `buildingStats` field and not a curve.
  - Enum `/Script/ManorLords.EApprovalFactorType`, 34 values (0 to 33, then `MAX`). It includes `unemployment` (17), `patrols` (18), `administration` (19), `no_administration` (20), `taxation` (24), `homelessness` (5), `drinking` (16), `unburied` (23), `missingEntertainment` (22), `MissingAmenities` (31).
  - `/Script/ManorLords.ApprovalSettings` (a `DeveloperSettings` class, config) has `ApprovalFactors`, a `float[34]` indexed by that enum. Default values (jmap CDO): unemployment -1.2, administration +1.0, no_administration -1.2, patrols 0.0, homelessness -5.0.
  - Per-region entries are structs `ApprovalMemory` {Type (enum), day, expirationDay, count, past, effectByPopulation}. Region has `summedApprovalFactors`, `summedPublicOrderFactors` and `publicOrderMemory`, all `Array<ApprovalMemory>`, plus ints `Approval` and `publicOrder`. Public order uses the SAME enum type as approval.
  - `ApprovalComponent` has `ApprovalDataTable` (null on the class default; set in `BP_Region`). Pak asset `/Game/ManorLords/Database/Approval/DT_Approval` has only approval LEVEL rows: `approvalImpression_Reviled..Revered` and `approvalEffect_PublicOrder`, `_Influence`, `_Morale`, `_Families`, `_TaxCollection`, `_CannotFormMilitia`, `_RegionalWealth_*`. So approval level feeds public order through a table, but the per-cause factor values are not in a table.
- "Unemployment -10% order" and "manor +10% order" are not named in the jmap. `unemployment` is an enum factor. The manor effect is probably native code (maybe `administration`); not proven.
- Building data: `BM_HuntingCamp` only has a name `unemploymentCull` (a worker rule, not a factor). No building field for order was found.

## Verdicts

- New factor row by pak: NO. The enum is native and fixed at 34, and the values are a config array, not a data table. A new enum value cannot be added by pak.
- Building that applies an existing negative factor: UNKNOWN. No data field found. Possible only through native logic (e.g. unemployment from idle workers, `no_administration` without a manor).
- Pak change of values: POSSIBLE but untested. `ApprovalSettings` is a config class (`[/Script/ManorLords.ApprovalSettings]` in `Game.ini` style config, or its CDO). This changes the weight for ALL regions, not a chosen amount.
- Lua at run time: LIKELY. `ApprovalSettings` CDO `ApprovalFactors` could be written (class default write), and `summedPublicOrderFactors` entries are plain structs (no soft refs). Whether public order is recomputed from them each poll is untested (`Region.Approval` writes are overwritten per poll, per the design).

## Next tests for the lead (game needed)

1. Read the CDO: bridge `get_property` on `/Script/ManorLords.Default__ApprovalSettings` `ApprovalFactors` (read only). Then set `unemployment` (index 17, 0-based) to -50 in a single-player run, wait one poll, read `publicOrder` and `summedPublicOrderFactors` on the player region; revert. Use a scratch test scenario or a spike, no save.
2. Read the entries: `get_property` on the region `summedPublicOrderFactors` before and after step 1 (check that `Type` unemployment appears).
3. Write test: append an `ApprovalMemory` entry to `publicOrderMemory` in Lua and check it affects `publicOrder` after a poll.
4. Pak option (config values): try a `Game.ini` or CDO-default patch; run `uv run python harness\run.py --scenario <spike scenario> --pak <pak> --max-runs 1000` only when the scenario exists. Existing smoke run for a baseline: `uv run python harness\run.py --scenario smoke --max-runs 1000`.
5. Take a tooltip picture (`BigTooltip_ApprovalAndPublicOrder`) with `ctx.screenshot` for question 4.
