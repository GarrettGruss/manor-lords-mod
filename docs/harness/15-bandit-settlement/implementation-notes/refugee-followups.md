# Refugee follow-ups: answers to issue #61 (2026-10-13)

Game 0.8.111. Probe scenario: `probe-refugee-followups` (hidden, mode set by `HARNESS_PROBE`). Data per run: `runs/<id>/probe.jsonl`, `telemetry.jsonl`, `mod.log`.
New read commands (HarnessActions version 38): `family_census` (one row per family: living members, roles, ages, `familyHome`; one row per home or tent with its `occupantFamilyIDs`) and `member_fields` (property names of one family member). `family_add` has a new option `adult`.
No save function and no eval were used. Fixture `base` unless noted: region Riesenbuckel, 10 families, 9 houses (2 of them empty), no tent.
Set the mode in the shell: `HARNESS_PROBE=surge_long uv run python harness/run.py --scenario probe-refugee-followups ...`. The run option `--env` did not reach the scenario (run `s61-surge-sites` ran the default mode by mistake; its data is a second copy of `s61-surge-long`).

Runs (8 launches counted without the one that stopped in preflight, because the fixture files were missing in the worktree):
| Run | Mode | Result |
|---|---|---|
| `s61-surge-long`, `s61-surge-sites` | surge_long (twice) | pass |
| `s61-surge-sites2` | surge_sites | pass |
| `s61-eject-census` | eject_census | pass |
| `s61-eject-late` | eject_late | pass |
| `s61-eject-tent` | eject_tent on fixture `burgage-start` | pass, but that fixture has no tent (see item 5) |
| `s61-surge-eject-tent` | surge_eject_tent | pass |
| `s61-plots-add` | plots_then_add | crash (0x3c1), see item 6 |

## Item 1: what homeless families do after 5 game days
Run `s61-surge-long`: one `settle_region` (5 families, 3 in the tent), then 20 game days at speed 3. Telemetry of the region (the two runs agree):
| Game day after the call | 0 | 1 | 2 | 3 | 4 | 5 | 9 | 12 | 15 | 18 | 20 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Approval | 71 | 63 | 62 | 61 | 62 | 62 | 63 | 64 | 64 | 63 | 63 |
| Homeless | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| Food (telemetry) | 3 | 2 | 2-3 | 2 | 3 | 3 | 3 | 3 | 3 | 2 | 2 |
- The homeless families do not starve, do not leave, and do not rebel in 20 game days. The census at day 1, 5, 10 and 20 shows the same 15 families, all with the tent as `familyHome`. Members rose 40 to 42 (children are born) and stayed 42. Public order stayed 100. Silver did not change.
- Approval does not keep falling. It drops about 8 in the first day, reaches the low (61) on day 3, and then recovers by 2 to 3 points (63 to 64). The fall is a one-time step, not a rate.
- Run `s61-surge-eject-tent`, 5 homeless: approval 61, 59, 58, 57, 57, 57 on days 0 to 5. Same shape: the low is reached in about 3 days.
- Rule of thumb from all runs: the low is about 2 to 3 points per homeless family: 3 homeless: 61; 5 homeless: 57; 8 homeless: 52 to 54 (run `s61-surge-sites2`, day 3).
- Exception: when food falls too. In `s61-eject-late` the village had 20 families and food 1, and approval fell 59, 55, 49, 47 in 3 days. That is the food rule, not the homeless rule.
- Answer for the design: a wave alone does not force the rebellion. The mod needs its own timer, as planned.

## Item 2: where are the other 2 families of `settle_region`
Run `s61-surge-long` (and `s61-surge-sites`), census right after the call: families 10 and 11 live in the two EMPTY houses of the village (`occupantFamilyIDs` of the houses 61954 and 61894 now list 10 and 11). Families 12, 13, 14 live in the new tent (type 87). So the new families fill free houses first and the rest goes into the tent. Homeless = families in the tent (3).
- The newcomers are small: families of 2 members (3 after a few days, children are born).
- Camp near woods (`forest_spot`, 37 km from the village, run `s61-surge-sites2`): the call worked. The tent stands at the camp point. 1 family took the first empty house, 4 went into the tent (homeless 4). The second empty house was still under construction (counted as unconstructed vacant slot). One game day later the game moved a tent family into it (homeless 3). So the game DOES move tent families into a free home, within a day. The camp place made no difference to approval (71, 63, 62, 61 as before).
- Supply 1 (second call in the same run, camp at the first spot): 5 families, all into a second tent (homeless 3 to 8), approval 61, 54, 54, 52. No visible difference to supply 0 in families or approval. Stock after supply 0: +20 of some goods (`6`, `15`, `216`, `172`) at the call; not compared with supply 1.
- A third call was not tried (launch budget). Two calls in a row were done before (notes `immigration-surge.md`).

## Item 3: why do the vacant slots not rise after `family_eject`
Answer: `Region:getAvailableLivingSpace` is not "free homes". It is the living slots minus ALL families, housed or not:
- `s61-eject-late`, after 3 ejected: living 12, families 10, vacant 2. The census shows 5 houses with free room (2 never used, 2 freed by the eject, 1 half freed), but the counter says 2.
- After the settle letter: families 20, living 12, vacant -8. After a surge: 12 slots, 15 families, vacant -3; 12 slots, 20 families, vacant -8. All match `living - families`.
- So the counter does not look at who lives where. An eject does not change the number of families, so the counter cannot change. The housing state is not broken.
- The real free room is in `family_census`: houses and tents with their `occupants`. Use it, not the vacant slots.
- Does a save and load fix it? Not possible to test: save functions are banned. The data does not suggest a fault, so no fix is needed.
- The ejected families stay homeless in the same way as before: 5 game days, the old houses stay empty (run `s61-eject-late`, census every day). Approval 71, 69, 67, 63, 62, 59.
- One run differs: `s61-eject-census` (eject at the very start, no baseline day) rehoused the 3 families in the same houses within 1 game day, with suppress true, with no call. `s61-eject-late` (eject after 2 baseline days) did not rehouse them in 5 days. Cause not known. The difference is the time of the eject: the first game day after the load (a first housing update runs and sorts the families). Rule: eject late, not in the first game day after a load.

## Item 4: why does the settle letter give +7 families
Answer: the letter does not give 1 family per squad. It fills every FREE SLOT of the houses with a new family (one family for each free slot). The squad count does not matter, as long as the squad has enough units.
| Run | Raid squads | Free slots (from the census) | New families |
|---|---|---|---|
| `s61-eject-census` | 1 | 2 (two empty houses) | +2 (family 10: 3 members, family 11: 1 member; vacant slots 2 to 0) |
| `s61-eject-late` | 1 | 10 (9 houses, 2 of them hold 2 families; only one house was full) | +10 (10 families of 1 member each) |
| s15-cyc1, s15-cyc2 (old notes) | 5 and 2 | 5 ejected + 2 empty = 7 | +7 |
- Where they live: in the free slots of the houses, including the old homes of the ejected families (family 10 in 67580, 11 in 67507 and so on). The 8 ejected families stay homeless and have no room left. That is why "homeless" stayed the same after the settle: the new families are housed, the old homeless are still homeless.
- The new families have 1 member each (so +10 families added only 11 residents: 35 to 46).
- Silver 83 to 63 (the 20 offered). The bandit units go to 0 within 2 game days.
- Food fell to 1 and approval to 47 after the 10 extra mouths. A settle letter after an eject therefore also feeds the village problem.

## Item 5: `family_eject home=tent` on a game with a house and a tent
- Fixture `burgage-start` has no tent any more (the tent is gone after the plots were built; 6 families, 10 houses). The command refused with "no homeless tent". Run `s61-eject-tent`. So the fixture is not usable for this.
- Used `base` instead: `settle_region` made the tent (3 families), then `family_eject count=2 home=tent` (run `s61-surge-eject-tent`).
  - The two families (ids 1, 0) moved into the tent: tent `occupantFamilyIDs` [12, 13, 14, 1, 0], their `familyHome` is the tent (type 87).
  - They count as homeless: homeless 3 to 5. Their old houses stay empty for 5 game days. The game does not move the tent families into those empty houses (unlike the 1-day move in item 2: that house was still under construction and then became free; here the houses were free at once and the move did not happen).
  - A tent has no capacity limit (5 families).
  - Approval 61 to 57 in 3 days, then flat.
- `family_eject home=tent` works as a way to make refugees without an empty street: the families still stand in a tent.

## Item 6: `family_add` crash (0x3c1), with an adult member
Run `s61-plots-add` (last step of the run). The new option `adult` takes the member with the highest `Age`. Result:
- Every member on `base` has role 3 and `Age` 1 (see `member_fields` and `family_census`). So the first test did not use "a child", and `adult` selects the same kind of member. There is no adult/child field to choose from here.
- The call worked: family 10 (1 member, no home), the old family 0 went from 3 to 2 members, homeless 1.
- The game crashed again between game day 1 and day 2 after the call: `EXCEPTION_ACCESS_VIOLATION reading address 0x00000000000003c1`. Report: `runs/s61-plots-add/crash/UECC-Windows-D24492BD4F1A6457386C4E8FCC655A39_0000/`. Logs: `runs/s61-plots-add/mod.log`, `UE4SS.log`, `probe.jsonl`.
- Caveat: this run had 9 uncommitted burgage plots in the same game (item 7). The first crash (s15-f3) had none. So the crash repeats with a different member and with plots. The cause is most likely `AddNewFamily` with a member that was taken out of a living family (a null pointer in a family routine).
- Verdict: `family_add` stays unusable. Use `settle_region` or `family_eject` for refugees. A whole family was not tried (the API takes a list of members; a next test could move all members of one family into a new family).

## Item 7: burgage plots on bad ground
Run `s61-plots-add`: `plot_field_place` and `commit_plots` with 3 plots each, 60 timber given.
| Try | Place | Commit | Burgage count (all) | Unbuilt vacant slots |
|---|---|---|---|---|
| no road | woods spot 34 km from the village | accepted | 9 to 12 | 1 to 3 |
| air | first tent spot, z + 4000 (not a true slope) | accepted | 12 to 15 | 3 to 6 |
| overlap | village centre (on top of the houses) | accepted | 15 to 18 | 6 to 9 |
- The commit checks nothing. All 9 plots were accepted at once, and each counted as an unbuilt slot. No crash from the commit.
- None was built in the 2 game days watched after each try (built count stayed 9). The builders had no word to go; whether they ever build, and where the plots stand, was not looked at (no screenshot of the plots).
- Water and a real slope were not tried: the harness has no finder for water or for a steep spot. Not possible now.
- Consequence: the "unbuilt vacant slots" number (and the free-slot count of the settle letter) can include plots that never get built. A mod that places plots must place them near the village on its own.

## Not answered
- A whole family for `family_add`, a third `settle_region` call, a settle letter test with 5 squads and a known number of free slots (the rule above fits all 5 data points).
- Water and steep ground for plots; whether the bad plots are ever built.
- Why `s61-eject-census` rehoused the ejected families within a day (item 3).
