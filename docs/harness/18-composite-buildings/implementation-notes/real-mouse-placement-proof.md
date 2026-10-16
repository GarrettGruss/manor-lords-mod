# Real-mouse placement proof (issues #115 and #104, 2026-10-15)

The user reconnected a mouse. `s115_input_env.py` shows SM_MOUSEPRESENT 1. No save function was called.

## Result
- `getMouse3d` returns real terrain points again (Z about 3091 to 3258). A white ghost follows the cursor.
- Scenario `place-building`, run `20261015-203710-6b45`: FAIL. The old default click point (0.65, 0.65) now lies over the sawpit in fixture `base`. The ghost is orange (blocked) there, so nothing is placed.
- Fix: `DEFAULT_PLACE_FX/FY` in `harness/runlib/actions.py` is now (0.35, 0.3), an open meadow. Run `20261015-204114-d883`: PASS (one more hitching post, cursor restored).
- The MCP `run_scenario` tool does not list `place-building` (hidden scenario). Use `uv run python harness\run.py --scenario place-building`.

## Game round of #104 (run `s115-st4`, `--keep-open`, pak `stable4`)
1. Ghost of row 125 at (0.35, 0.3): white, a box shape (screenshot `ghost` and `g125`).
2. `s94_drive.py place 125 0.35 0.3` (real click): the player region Nusslohe got a master of type 125, 2 parts, `maxHp` 150, not constructed.
3. After 14 game days at speed 3 the master is `constructed: true`. Four days were not enough.
4. Master reads `animalSpaceCache` stableMax 4 (stableCurrent 0).
5. Oxen: `spawnAnimal(12)` four times (harness spawn, not a purchase). After 2 more game days: stableCurrent 4, four `VAMP_Ox_C` in `animals`, realPos values pairwise more than 50 units apart, all within about 600 units of the master.
6. Screenshot `runs/s115-st4/screenshots/stable125_4oxen.png` shows the two-shed stable placed by the click. The oxen are not in view: they walk away to work (as in the baseline). So "4 oxen at rest spots" is still not seen. Positions come from the work AI.
- Git-ignored screenshots: `runs/s115-st4/screenshots/` (ghost, ghost2, placed125, after14, stable125_4oxen).
- The run ended with a harness_error (paks-remove, file in use because the game stayed open). The pak was removed by hand after the game was closed. `~mods` is empty.

## Open
- Buying 4 oxen (`order_oxen` adds only one) and where idle oxen stand (run unpaused at night).
- A scenario for the row 125 round that does not need `--keep-open` tools.
