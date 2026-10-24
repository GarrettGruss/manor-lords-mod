# Route B: edit the tooltip widget (tasks 3.1 to 3.3)

Run `ord-h-193058`. Pictures `evidence/o5`, `o6`.

## Verdict

**Works.** From Lua the mod can add a row with its own text and value, relabel a row and change the sum. A hook on `updateContents` adds the row again each time the tooltip opens. No pak.

## 3.1 Widget and rows

- Widget: `/Game/UI/Tooltips/BigTooltip_ApprovalAndPublicOrder` (class `BigTooltip_ApprovalAndPublicOrder_C`), one instance kept by the game instance. Variables: `recentFactors_VB`, `pastFactors_VB` (vertical boxes of rows), `current_sum_txt`, `past_sum_txt`, `none_txt`, `showDetails`.
- A row is `approvalFactorWidget_C` (`/Game/UI/Tooltips/approvalFactorWidget`) with the text blocks `DescriptionText` and `ValueText`. Read: child 0 = "Unemployment | -10%", child 1 = "Administrative Buildings | +10%".
- Native `updateContents` runs each time the tooltip opens (moving the cursor away and back): it clears and rebuilds the rows. So a row that the mod adds is lost at the next open.

## 3.2 Add, relabel, change the sum (tooltip open, paused)

- `library:Create(controller, approvalFactorWidget_C, controller)`, `recentFactors_VB:AddChildToVerticalBox(row)`, `row.DescriptionText:SetText(FText("Bandit fear"))`, `row.ValueText:SetText(FText("-40%"))`, `ValueText:SetColorAndOpacity(...)` (red): all ok. Children 2 to 3.
- `row0.DescriptionText:SetText(FText("Raid fear"))` relabels a native row. `tip.current_sum_txt:SetText(FText("-50%"))` changes the header sum.
- Picture `o5-route-b-added-row.jpg`: "Raid fear -10%", "Administrative Buildings +10%", **"Bandit fear -40%"** (red), header "Recent Factors -50%". The new row has no little arrow image and sits a bit left of the native rows (the arrow is an image in the row; not copied).
- The row text is the mod's own string. The values are text only: the sum in the header must be written by the mod.

## 3.3 Survives a refresh? Hook

- The change is lost when the tooltip opens again (native rebuild; checked: after the cursor left and came back there were 2 native children again).
- **Hook:** `RegisterHook("/Game/UI/Tooltips/BigTooltip_ApprovalAndPublicOrder.BigTooltip_ApprovalAndPublicOrder_C:updateContents", pre)` fires once for each open (the log shows `pre updateContents`, `pre getColorForValue` for each row, `pre togglePastDetails`). The post callback never fired (no `post` line for any of the 7 functions hooked). The pre callback runs before the rebuild, so a row added there is cleared at once.
- Working recipe: in the **pre** callback take `self:get()`, then `ExecuteWithDelay(60, ...)` and `ExecuteInGameThread` to add the row and set the sum after the rebuild. Result (picture `o6-route-b-hook.jpg`): each open shows "Bandit fear (delayed hook) -40%" and the header "-50%" without any manual call. A first try with a direct add in the post callback did nothing (the post hook did not run).
- One row was added for each open (no duplicates in two opens).
- Not tested: the delay under a slow frame (60 ms is a guess; the row shows late if the frame is long); the tooltip while the game runs and the list changes; the `pastFactors_VB` and TAB details; hooking when the class is not loaded yet (the instance exists once the HUD has built; `NotifyOnNewObject` is the usual route); a controller player.

## Safety

All steps inside `pcall`; no `params` or struct with soft objects was read; no save.
