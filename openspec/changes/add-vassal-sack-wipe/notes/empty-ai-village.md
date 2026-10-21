# Empty AI village (task 1.1, design questions 1 and 6)

## Question
What does an AI (vassal) village do when all its villagers are dead? Does it stay, decay, get removed, crash, or change owner? How can the mod sack houses in an AI village?

## Method
Hidden test scenario `mod/InvasionMod/scenarios/vassals/probe_wipe.py` (`probe-vassal-wipe`, new game, slot 2, nothing saved). It claims a free region as the player, settles it, hands it to the vassal lord (Aldric), and lets it grow 6 game days. Then it collapses houses (`collapseBuilding`), kills villagers, and reads the region every 2 game days for 10 days. The spike commands are in `features/vassals/probe.lua` (`probe_region`, `probe_collapse`, `probe_kill_villagers`). Remove them after the spike. Killing villagers is for the test only (owner rule, 2026-10-20).

## Runs
| Run id | Verdict | What it shows |
|---|---|---|
| 20261021-050845-d295 | crash | `core.remove_families(region, 1000)` on an AI village: access violation in UE4SS during the kill |
| 20261021-051155-a6a4 | crash | a kill of 1 family worked (families 5 to 4, people 10 to 8). The next call with count 1000 crashed (access violation, `0xffffffffffffffff`) |
| 20261021-051425-aec2 | pass | members collected first, then killed: all dead. 3 houses collapsed before. Watched 10 game days |
| 20261021-052018-be14 | pass | same, all 5 buildings collapsed before. Watched 10 game days |

## Results (runs aec2 and be14)
- Kill method that works: collect the member objects of the families first, then call `just_die` on each valid, living member. `core.remove_families` walks `region.workerFamilies` while the deaths change that array. It crashed the game 2 of 2 times when it killed more than one family in one call on an AI village. It is the helper that the sack of the player region uses (`HarnessSack.remove_families`). Not checked: whether it crashes there (the sack kills only a share of the families).
- At 0 villagers: families 0, population 0, members alive 0 (read at once and at every step for 10 game days).
- The region stays. The owner is the vassal lord pawn before and after, for all 10 days (aec2 and be14). `isSettled` stays true. The building count does not drop by itself.
- No decay, no removal, no crash in 10 game days. The region does not get new villagers by itself (families 0 at day 2, 4, 6, 8, 10).
- The AI keeps running its build loop. In be14 (all buildings ruins) the construction log shows `AI_build failed to find place` for LoggingCamp, BurgagePlotTool and Sawpit. In aec2 (2 ruins) no new log line appeared. In aec2 standing buildings went 12 to 13 at day 2 (a site finished); in be14 they stayed 0.
- The mod registry (`vassals_state`) did not change: `lost` 0, the slot kept, the region still owned by the lord. The vassals feature has no check for villagers, so a wipe is not a "lost vassal" today. The mod must do that itself.

## Sack of houses in an AI village (question 6)
`building:collapseBuilding()` works on an AI village, called from a mod command with the region object found by name. aec2: 3 calls, `standing` 14 to 12, `rubble` 0 to 2 (the third result showed later or was a site). be14: 5 of 5 standing buildings became rubble (`standing` 0, `rubble` 5). `HarnessSack.sack_buildings` cannot do this because `playerRegion` refuses a region that the player does not own. The mod needs a version that takes a region by name (as `probe_collapse` does).

## Not verified
- Longer than 10 game days (no season or year change).
- A bigger village (be14 grew only to 5 buildings in 6 days, aec2 to 14).
- Whether the lord stays active in the long run (the logs show it still tries to build).
- Fire (`StartFire`) as the method in an AI village.
- Picture evidence (not taken).
