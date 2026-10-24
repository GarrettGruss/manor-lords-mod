# Evidence

JPEG pictures, at most 1280x720, taken with `runlib.screenshot.capture_game_window` from a hold run (a scratch test scenario that keeps the game open; not committed) on fixture `base`, run `ord-h-193058` (slot 2). The tooltip was opened with the real mouse (`osinput.hover_at`). Windows of other programs may touch the picture edge.

| File | What it shows |
|---|---|
| `o1-tooltip-baseline.jpg` | The Public Order tooltip of the unchanged game: Unemployment -10%, Administrative Buildings +10%, Lingering Memories none |
| `o2-route-a-append.jpg` | Route A: an entry appended to `summedPublicOrderFactors` (Type 23) shows as "Unburied Bodies -40%", header -40% |
| `o3-top-bar-77.jpg` | Top bar after a per-tick write of `Region.publicOrder = 77` (game running, camera over the village): 77% |
| `o5-route-b-added-row.jpg` | Route B: a row "Bandit fear -40%" added from Lua, "Raid fear" relabel, header -50% |
| `o6-route-b-hook.jpg` | Route B with a hook: the row "Bandit fear (delayed hook)" is added each time the tooltip opens |
| `o7-route-a-past-and-memory.jpg` | Route A with `past = true`: "Lingering Memories -20%" and the TAB hint (details not opened) |
