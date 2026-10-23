# Design: Spike scenario template menu

## Method
1. Find the widgets and the data source (questions 1 and 2). Read the menu widget classes and the `gameSetup` object through the bridge (`find_objects`, `list_subclasses`, `inspect_object`), with the screen open. Reuse `HarnessGameSetup` and the notes of #358. Do not read struct values with soft object fields.
2. Extract the template data and widget assets with `harness/tools/pakmod.py` (skill `harness-pak-mod`, wiki `docs/wiki/workflows/pak-mods.md`). Find the template list (data table or asset) and how the 5 pictures and the difficulty banners map to it.
3. Test question 1. Route A: Lua at run time (add an entry or widget after the screen loads, hook with `NotifyOnNewObject`). Route B: a pak that adds a row or asset. Pick the route by what step 2 shows. Record a picture of the screen if it works.
4. Test question 2 with the same two routes: hide a row (widget visibility or data), add a row (clone a row widget and bind a mod value). Check that a changed value reaches the mod (a read in Lua, not a save).
5. Question 3: read where the mod code uses game settings (grep `gameSetup`, raid code, bandits). Then run an A/B per setting with skill `harness-ab-testing`. Change one setting at a time, from the lowest to the highest value. Use a test scenario that starts a game with that setting and measures: raids per period, bandit camp count, vassal and sack events (telemetry). Assert ranges, not exact values. Use a harness suite for repeats (small sample, report the spread). Settings with no code link and no A/B effect are marked "native only".
6. Write `notes/<topic>.md` per topic and a recommendation.

## Safety
- Never call a save function. Visiting the setup screen changes `menu.sav`: back up the save folder and `menu.sav` first, and restore them after each session. The launcher hash guard only reports after the fact.
- Do not write the `Tags` array or `region.regionName` through the bridge. Do not read soft object struct fields. Check `DANGEROUS_ACTIONS.md` before each new bridge call or write.
- The AES key must never be printed or written outside `modtools/work/aes_key.txt` and `.env`. Grep each diff for it before a commit.
- Single-player only. Cap the number of runs. Raw Lua eval only for experiments, and no test scenario depends on it.
- Do not edit game files other than the planned deploy folder and pak install folder.

## Risks
- A pak that changes the menu may crash the game at load. Test in a private run first.
- Pak assets that name new templates may need an engine class that Lua cannot make. Then the verdict is "needs a pak and a native asset" or "not possible".
