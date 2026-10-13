# Tent as a home by a live slot limit (part 6, plan step 8)

Game 0.8.111. Runs: `s15-t1` (fixture `manor-bailey`), `s15-t2` (fixture `base`). Both with `HARNESS_ALLOW_UNSAFE=1`, keep-open.
Mod logs: `runs/s15-tools/mod-s15t1.log`, `mod-s15t2.log`. No crash. No save function called.
Tool: new unsafe command `building_stat_vector_write` (HarnessHousing, HarnessActions version 32). Fields: `type`, `field` (`occupantTypes` or `workerTypes`), `component` (X, Y, Z, W), `value` (0 to 100).

## Short answer
Not possible with a live write of the row. The write works, but the game does not read the row again for buildings that exist.

## Q1: Does the write change the vacant slots at once?
No.
- `manor-bailey` has a tent (type 87) with 5 families. Region Hochweg: families 5, homeless 5, living 0, vacant -5.
- Row 87 `occupantTypes` was written 0 -> Y=5. `building_stat type=87` read back Y=5 (the write is real). Vacant stayed -5. `accommodate_homeless` changed nothing.
- Y=5 for 60 s of game time at 8x (about 15 game days): vacant -5 all the time.
- X, Z and W set to 5 too: vacant unchanged (the later -4 came from a family that died of hunger, a popup `hunger` shows; not from the write).
- Control on fixture `base` (9 plots, living 11, vacant 1): row 3 `occupantTypes.Y` 1 -> 2 and -> 3 (read back): living stayed 11, vacant stayed 1. So the game does not read this row live for existing buildings. Each building keeps its own copy, or the value is cached.
- Also the tent is not counted in the living space at all (living 0 with a tent that holds 5 families).

## Q2: Do families move in through immigration?
No. Vacant slots never rose above 0, so there was no room. Not tried: the settle letter path (it needs a vacant slot too).

## Q3: What happens when the limit goes back to 0?
Nothing. The 4 or 5 families stayed in the tent (they were already homeless). All four components were set back to 0 and read back. Row 3 was restored to Y=1.

## Not verified
- A tent or plot placed after the write may read the new row. No tent could be placed (see `tent-placement.md`), and no burgage plot was placed in this spike.
- Fallback from the plan: change the row in a pak (`harness-pak-mod`) and compare a game with and without it.
