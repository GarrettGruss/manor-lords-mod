# Silver field and the HUD number

Question (owner review of PR #322): why did the HUD silver show 0 before and after a tribute?

Spike (2026-10-19, `--keep-open` run `20261020-035504-56ae`, new game):
- The HUD number is `TreasuryNumeric` (MLNumericTextBlock) in `W_HUD_LordPanelV2`. `GetTargetValue` gives its value.
- After the tribute, `playerRef.silver` was 800 and the HUD value was 0.
- Calling `updatePlayerStats` on the lord panel set the HUD value to 800. So the HUD shows `playerRef.silver`: the feature uses the right field.
- `set playerRef.silver = 1000`, then 4 s unpaused, did not change the HUD (it stayed 800). The panel updates on its own event, not on a timer. A direct write raises no event.

Result:
- Cause: the HUD did not refresh. The tribute field is correct.
- Fix in the feature: after a tribute, and when the menu silver text changes, call `updatePlayerStats` on `W_HUD_LordPanel_V2_C` (in `pcall`). `TributeInfoText` now reads "Tribute: 200 silver (you have <n>)". No new widget element, so no re-cook.

Spec impact: the text of `TributeInfoText` changes, and the HUD is refreshed after a tribute. The spec does not state the exact text. Add one sentence to the menu requirement of `mod/liege_influence` at the next spec edit. The behavior of silver and influence did not change.
