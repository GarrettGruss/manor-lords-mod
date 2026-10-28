# Homeless rebellion in fixture playtest-noai (2026-10-24)

Probe: worktree C:\Users\garre\development\manor-lords-mod\.claude\worktrees\rebel-noai, harness/scenarios/probe_rebel_noai.py (hidden, uncommitted).
Data: runs/<id>/probe.jsonl in that worktree. Times t = clock seconds after the `homeless_rebel count=2 mode=home` call (game seconds, as in the legacy notes).
Runs: 20261024-183715-cb95 (watched 1900 s, killed by my tool timeout, no summary.json), 20261024-184819-6fe5 (pass), 20261024-185248-8b6d (pass).
Failed setup runs (clock would not start after pre-run pause): 20261024-183014-fd46, 183136-c436, 183550-5886. Cause: my probe called pause first; the stock time-advance test passes in this fixture (183418-d5c5).

## Setup facts
- No player soldiers exist: the census at start is 195 units, all side "civil". No player squad. The owner's "left soldiers" idea cannot apply to this save. Distance to player squads is therefore not measurable (d_nearest_player empty).
- Player pawn / village centre: (-37161, -53167).
- No Outlaws pawn at start. `spawn_bandit_camp` made it: +18 units, one camp squad (id 19), far away (run 1 (62042,2883), run 2 (5587,-67703), run 3 (-42958,61804)), 45000 to 115000 from the village. Camp squad id 19 stayed at its camp all run. It never joined the rebels.
- `homeless_rebel count=2`: families 5 -> 3, squads 20 and 21 (18 Brigands each) at the two homes (-38338,-49536) and (-39196,-49493), 3800 and 4200 from the village centre.

## Timeline (squads 20 and 21; no waypoint, no wait)
| Event | 183715-cb95 | 184819-6fe5 | 185248-8b6d |
|---|---|---|---|
| AI: "on enemy territory (raiding): Riesenbuckel" first seen | <=37 | <=35 | <=32 |
| first building burning | 37 | 108 | 69 |
| max burning / rubble | 2 / 3 at 108 | 3 / 3 at 143 | 4 / 5 at 105-141 |
| "enough looted. Leaving map." first seen | 108 | 202 | ~141 |
| squads at map edge (y -88700) | 286 | 312 | 268 |
| standing buildings 17 -> | 14 | 14 | 12 |
After the leave, the AI repeated "enough looted" every cycle until the end of each watch (to 1900, 720, 670 s). No second attack, no return.
Squad paths: they walked 2000 to 7000 units around the village burning, then south/west to the edge. They were never near (-31000,-22500).
The camp squad (19) did not move more than a few hundred units, AI line "Can raid = 0" for it.

## Answer
No. The squads do not go to player soldiers first (there are none). They do not wait. With AI opponents 0 there is no "targetEnemyArmy / move to enemy army / baiting" line at all, and no 90 s walk to the waypoint. The squads see themselves already "on enemy territory (raiding): Riesenbuckel" within 35 s, burn within 30 to 110 s, say "enough looted" 108 to 202 s after spawn, and leave by 270 to 310 s.
The legacy 480-550 s wait in fixture base is therefore tied to something that playtest-noai lacks: a neighbour AI lord's army (the AI waited to bait/hunt it). That fits the legacy log lines ("enemy army is a neighbour lord"). Owner's soldier hypothesis is not supported: there are no soldiers in the save, and the wait vanished.

## Not done
- Control with demobilized/far soldiers: skipped, there are no soldiers.
- The loop ran 20 steps in runs 2 and 3 (about 700 s), 52 in run 1 (1900 s).
## Saves
Hash/diff of %LOCALAPPDATA%\ManorLords\Saved\SaveGames against backup C:\Users\garre\development\backups\saves-20261023-rebel-noai: identical. No save call used.
