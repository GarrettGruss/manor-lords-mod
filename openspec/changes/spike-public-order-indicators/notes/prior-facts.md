# Prior facts (task 1.1)

Read: the notes of #403 (`openspec/changes/archive/2026-10-23-spike-public-order-factor/notes/`: `factor-location.md`, `game-tests.md`, `game-tests-2.md`, `tick-write.md`), `docs/wiki/concepts/engine-limits.md` ("Public order factors") and `DANGEROUS_ACTIONS.md`.

## What is known

- Factors are the native enum `EApprovalFactorType` (34 values) with weights from config. Public order uses the same enum as approval. A pak cannot add a factor.
- `Region.summedPublicOrderFactors` is renewed by the game each day. A fresh fixture shows Type 17 (unemployment) -10.0 count 1 and Type 19 (administration) +10.0 count 1, window day to day+5. The tooltip in `reference/order-tooltip.png` shows "Unemployment -10%" under "Recent Factors -10%": that is the Type 17 entry.
- `publicOrderMemory` entries can be appended safely, but the game rewrites `effectByPopulation` to a small per-person value and never lists the entry in `summedPublicOrderFactors`. `publicOrder` stays equal to the control.
- A per-tick `Region.publicOrder` write holds. The top bar shows the written value.
- `publicOrder` reads 0 or 100 for about 12 percent of samples (transient values).
- Owner decision 2026-10-23 (#403): the mod writes its own order value every tick (route A of that spike).

## What the asset says (static, `modtools/work`, pak `pakchunk0_s17`)

The tooltip is the widget `/Game/UI/Tooltips/BigTooltip_ApprovalAndPublicOrder` (class `BigTooltip_ApprovalAndPublicOrder_C`).

- Functions: `Construct`, `updateContents`, `togglePastDetails`, `doesPlayerPressTAB`, `getColorForValue`, `ApplyPlatformLimits`.
- Variables: `region` (object), `factorsToDisplay`, `showDetails`, `ShowPastMemoryDetails`.
- Containers: `recentFactors_VB` (the "Recent Factors" list), `pastFactors_VB` ("Lingering Memories"), `LastYearFactorsParent`, text blocks `current_sum_txt`, `past_sum_txt`, `none_txt`, `pst_none_txt_1`, `name_txt_1`, `descr_RichTxt`.
- `updateContents` calls `getSummedFactorsRecentPast` (a function on the region or pawn, with the output arrays recent and past), loops the `ApprovalMemory` entries, makes one row widget with `WidgetBlueprintLibrary:Create` for each entry (class `approvalFactorWidget_C`), and calls `AddChildToVerticalBox`. It clears with `ClearChildren` and shows `factor_none` when a list is empty. Text comes from the data table `DT_Translation_Approval` through `getTranslatedTextFromDataTable`.
- The row widget `/Game/UI/Tooltips/approvalFactorWidget` (class `approvalFactorWidget_C`) has a variable `approvalFactor` (an `ApprovalMemory` struct, exposed on spawn), two text blocks `DescriptionText` and `ValueText`, and an arrow image. `Construct` sets the texts from `approvalFactor.type` (enum name to the translation table) and `effectByPopulation`.

So there are two places for a custom row: the data list that `getSummedFactorsRecentPast` returns (route A), and the row widget list that `updateContents` builds (route B).
