# Refugee cycle (part 8, 2026-10-12)

Game 0.8.111, fixture `base` (Riesenbuckel, 10 families, 35 residents). Scenario: `probe-refugee-cycle` (hidden). Runs: `s15-cyc1` (5 raid squads), `s15-cyc2` (2 raid squads). Both ended `pass`, no crash.
Data: `runs/<id>/probe.jsonl`, `scenario.log`, screenshots `plots_placed.png`, `plots_end.png`. No save function and no eval were used. Day = 1 game day, read at speed 3.
Columns: F families, H homeless, Res residents, Vac vacant constructed slots (unconstructed), Appr approval, Bg burgage plots built / all.

## Step 1 and 2: start and eject 5 (both runs identical)
| Step | F | H | Res | Vac | Appr | Bg |
|---|---|---|---|---|---|---|
| start | 10 | 0 | 35 | 1 (1) | 71 | 8 / 9 |
| after 1 day | 10 | 0 | 35 | 2 (0) | 71 | 9 / 9 |
| eject 5 | 10 | 5 | 35 | 2 (0) | 71 | 9 / 9 |
- Vacant slots stayed 2 after the eject. Same oddity as before: freed homes are not counted.
- The fixture has 9 burgage plots (not 0).

## Step 3: immigration
- Natural: 3 game days after the eject, no family arrived (F 10, Res 35). Approval 71, 67, 63, 59.
- Settle path (`spawn_raid`, tag `attacking`, letter `+20`): families rose 10 to 17 (+7) in BOTH runs, with 5 squads (arrived within day 1) and with 2 squads (arrived on day 2, none on day 1). So the count is not 1 per squad. +7 matches neither the squads nor the 2 vacant slots. Cause open.
- The new families are homeless in effect: Vac fell to -5, Res rose 35 to 43 (then +1 a day), H stayed 5 (the new families are not counted as homeless; living slots 12 for 17 families, so about 5 are without a slot too). Silver 83 to 63. Bandit units 0 after.
- Approval kept falling: 54 after the settle.
- Open: where the 7 new families live. `getNumHomelessFamilies` stayed 5.

## Step 4: accommodate_homeless
No change in both runs (H 5, F 17, Vac -5). There was no free slot, so nothing to do. Earlier runs (with free slots) rehoused at once.
(To see it work after a settle, settle fewer families, or run it before the settle.)

## Step 5: 5 burgage plots without the mouse
Method: `open_burgage_tool` (placePlotType 3, placeFieldMode), `plot_field_place` (5 plots from `runlib/plotgeom.py`, first spot of `tent_find_spot`, plots face the village centre), `commit_plots`. 30 timber given first (18 to 48).
- `plot_field_place` and the commit worked. Burgage count (all) 9 to 14 at once; unconstructed vacant slots 0 to 5. No crash. Plots had no check for road; builders did start (so the spot was near enough to a road or the game did not need one).
- Per game day after the commit (same in both runs, +-1 day):
| Day | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Bg built | 9 | 9 | 9 | 9 | 10 | 10 | 11 | 11 | 12 | 12 | 12 | 12 | 14 | 14 | 14 |
| Homeless | 5 | 5 | 5 | 5 | 4 | 4 | 3 | 3 | 2 | 2 | 2 | 2 | 0 | 0 | 0 |
| Appr | 55 | 57 | 57 | 57 | 57 | 57 | 59 | 58 | 59 | 60 | 60 | 61 | 62 | 65 | 66 |
- Homeless families moved into each new plot BY THEMSELVES, as it was finished: homeless fell by the number of plots finished (4, 3, 2, 0). The last two finished between day 11 and 12 and housed 2 families. Homeless 0 on day 12. Final: F 17, Res 56, Vac 0, Appr 66 (rising as families were housed).
- A plot took about 2 game days of building each; the 5 plots were done in 12 game days with the available builders.
- Unlike step 4, no call is needed. `accommodate_homeless` is not required for new plots.
- Screenshot `plots_end.png`: the camera was not on the plots (shows the build tool still open "Plot Points 0/4"). The row position was not checked on screen.

## Answers
- Do new families arrive without the letter? No (3 days).
- Does the letter give families when vacant slots did not rise? Yes: +7, even with only 2 vacant slots. The rule "+1 per squad" is wrong for this case.
- Do homeless families move in by themselves? Yes, into finished plots; not into free slots after a settle (no free slots then).

## Open
- Why +7. Try 1 squad, and a fixture with 0 vacant slots.
- Where the 7 new families are housed; they were not counted homeless.
- A check of the placed row on screen, road need, bad spots.
