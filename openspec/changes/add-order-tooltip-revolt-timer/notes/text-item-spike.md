# Spike: a text item with no value

Run `20261106-235911-9a02` (slot 1, fixture `playtest-noai`, scenario `order-tooltip-revolt-timer`).

- The row widget `approvalFactorWidget_C` can show a plain text line: write the whole text in `DescriptionText`, collapse `ValueText` and the arrow image. The text is not clipped (`Revolt blocked: 2 of 4 armed homes` fits the tooltip). See `evidence/tooltip-timer-blocked.jpg`.
- `DescriptionText` has no callable `SetColorAndOpacity` (first run `20261106-235642-5ad1`: error `attempt to call a TrivialObject value`, the tooltip did not update). The call is now wrapped in `pcall`; the text keeps the game colour (dark brown, as the native "Lingering Memories" text). The spec says so.
- So no fallback was needed. `order_tooltip.text_items = false` still gives the label and value shape.
- The native "Lingering Memories / None" section stays below the mod rows (it was there before this change).

# Cost of the armed count
Metrics of the same run, 5 families: first read after the cache expired 5 ms CPU (`os.clock`), cached read 2 ms (the same call also reads the family count and the pawn). The tooltip opened with no visible lag. The cache keeps the count for 3 real seconds.

# Other
- The first issue (#583) and pull request (#584) were lost when the bot account was suspended. The issue is #586 and the spec pull request is #588 (branch `spec/add-order-tooltip-revolt-timer-v2`).
- The save-folder guard of the runs reported `saveGame_60` files that belong to another agent's fixture, not to this run.
