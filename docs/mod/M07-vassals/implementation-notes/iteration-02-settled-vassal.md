# M07 iteration 02: notes (spike: does a handed-over lord grow, does it declare war)

## Method
New game on Jagged Cliffs (0 AI lords), scenario `vassals-settled-vassal`: the player claims a free region (`layClaim` + `finalizeClaim`), settles it (`settleRegion`, supply 2), and the mod hands it over: `spawnNewAILord` (can build), `addPawnRelations`, `startAI(1, true)`, then `lord_receive_region` (clear owner, lord claim and finalize, the route of spike S13). 20 game days at speed 2.

## Findings
| Question | Answer | Evidence |
| --- | --- | --- |
| Does the handover work? | Yes, 11 of 11. The lord owns the region, the 4 or 5 buildings and 5 families stay. | runs of 2026-10-18 |
| Does the lord grow? | Depends on the region state. 4 buildings after the settle call: 4 -> 13 or 14 in 5 of 5 runs. 5 buildings (a building existed before the settle call): no growth in 6 of 6 runs. | The AI log of the stalled runs: `AI_build failed to find place: LoggingCamp / BurgagePlotTool / Sawpit`. The 5 building case was always Eichenhau (it has one pre-existing building in some map seeds). The 13/14 case also appeared in Eichenhau and Goldhof. |
| Is the lord at war with the player? | Yes, in every run. The war starts about 12 s after the handover, not at the spawn or the handover (status read right after both: no enemy, no tag). Relation tag `at_war`, and the player is in `enemies` of the lord. | `mod.log` lines `VASSALS lord Aldric is at war with the player` |
| Does peace hold? | Yes. `declarePeace(player)` once; no new war in 20 game days (7 of 7). | `peace_calls` = 1 in every run |

The user expected no war. The war is real, so the mod declares peace (`vassals.keep_peace`, default on). Cause not isolated: the AI lord may hate the player as its default enemy, or the claim over a player settled region may count as an attack. Not tested: a lord that is never given a region.

## Design in the code
- Poll every 2 s; the region scan runs every 3rd poll (6 s). A player-owned region that is not the home region becomes a slot; when settled, it is handed over (3 attempts).
- Home region: the owned region with most buildings at the first scan, saved (`vassals_home_region`).
- ModState keys per slot: `handed_day` (day + 1, because a new game starts at `daysTotal` 0), `handed_buildings`, `stalled`.
- Stall check 10 game days after the handover: fewer than 3 new buildings sets `stalled`. M08 must not count on buildings of a stalled vassal (use a formula on families).
- `buildings` counts use `GetBuildings`, which returns a plain Lua table: `#list`, not `GetArrayNum` (bug found by a run).

## Open risks
- A spawned lord may not survive a save and load (not testable: save calls are banned). `vassals_state` shows `lord` by name; if the lord is missing after a load, the slot keeps its name and the war watch returns nil.
- Eichenhau-like regions with a pre-existing building stall. A later iteration could clear the building or hand the region over before the settle call.
- Lord numbers are indexes of `FindAllOf` and can change; the mod looks the lord up by name each time.
