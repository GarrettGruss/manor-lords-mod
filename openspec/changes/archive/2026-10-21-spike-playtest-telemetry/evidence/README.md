# Evidence: spike-playtest-telemetry

Pictures from the test scenario `probe-playtest-menu`, run `ptt-menu-1` (slot 2). Other windows (the UE4SS console of another slot) cover part of the game: the pictures were taken on slot 2 and are not clean. Clean pictures need slot 0 later. Both were converted to JPEG (quality 70, at most 1280x720).

| File | Step | What it shows |
|---|---|---|
| `menu-typed.jpg` | `menu-typed` | the report widget with the text box (text set by Lua, then " +typed" typed with `WM_CHAR`), the check box ticked, the button "Create report" |
| `menu-unticked.jpg` | `menu-unticked` | the same widget after `SetIsChecked(false)` |
