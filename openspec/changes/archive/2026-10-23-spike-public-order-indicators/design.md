# Design: Spike public order indicators

## Method
1. Read the notes of #403 and `DANGEROUS_ACTIONS.md` before any bridge call.
2. Route A. Read `summedPublicOrderFactors` and `publicOrderMemory` of the region (plain structs only). Append one entry (copy a native one, change the type and value). Open the tooltip. Poll the lists for several ticks to see if the game clears or rewrites the entry. Record the enum value and the label that show.
3. Route B. Find the tooltip widget class: list widget classes while the tooltip is open, and hook the function that builds or shows it. Try to add a child text row, and to change a label and a value. Check that the change survives a tooltip refresh.
4. Route C. Only if A and B fail: search extracted data for a factor label table or string table. Note why a pak cannot add a row (native enum), or what it could do. Do not build a pak unless a real option is found.
5. Top bar check: write a known `publicOrder` value and read the percentage on the top bar (picture).

## Opening the tooltip without a mouse
The owner said the mouse is not connected. Plan:
- Find the widget function that shows the tooltip on hover (hook the tooltip event once, or search the top bar widget functions with `list_functions`). Call it from Lua or the bridge on the game thread.
- If no function works, mark the picture task as "needs the owner" in `tasks.md`. The owner hovers the icon while the run is paused and the harness takes the screenshot.
- The owner may be playing. Do not run the game until the owner says it is free.

## Safety
- Never call a save function. Do not use `Request Autosave`.
- Check `DANGEROUS_ACTIONS.md` before bridge calls.
- Do not read struct values with soft object fields (`getItem`, `RowStruct`).
- Do not pass a Lua string to a UFunction with an `FName` argument on an object that may lack it. Read the name lists first, or skip the call.
- Never write a `Tags` array through the bridge `set`.
- Edits to lists and widgets are single-player experiments. Back up saves before each run.
- Raw Lua eval is allowed for spikes only. A feature must later use named commands.

## Outcomes
For each route: works (row visible, kept for several ticks), partly works (visible but cleared or wrong label), or fails. The owner decision at the end picks the route for the follow-up change.
