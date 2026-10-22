# Soak plan (task 1.1)

Sources: `soak-results.md` and `open-items.md` in the archived change `2026-10-15-legacy-10-invasion-testability`.

## Known facts
- Short runs (600 to 1000 s) hold 7.9 game s per wall s. Memory is flat.
- Run `soak-long3`: village defeated at day 350 (cold). Feeding stops hunger, not cold.
- Run `s53-soak730-full3` (12000 s, keep-approval): 333 days, no crash, rate 1.11 on average (2.53 in the first hour), memory 4612 to 1603 MB. The game overwrote the Approval write (read back 36 to 59).
- A test scenario cannot chain runs. Save rules forbid ad hoc saves.

## Owner decisions (issue #286)
- Q1: 333 game days is enough proof for Q1 (2026-10-19). Full 730 days is not needed.
- Q2: no periodic raid in the soak (2026-10-20). Task 2.2 is not needed.

## Plan
1. Add a sample of unit count and building count every 120 wall s to `soak-days` (task 1.2). Rows go to `scenario.log` and the run notes.
2. Run 1: `HARNESS_SOAK_WALL_S=12000`, `HARNESS_SOAK_KEEP_APPROVAL=1` (variables exported in the shell, not `--env`). Expect about 333 days. Read the units, buildings and rate columns for the cause of the falling rate.
3. Run 2 only if run 1 is not clean (crash, kill from outside) or needs a variation. Cap: 2 runs.
4. Decide Q1 state from the numbers and update `criteria.json` only if the state changes.
