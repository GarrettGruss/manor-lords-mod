# Evidence

Test scenario `vassals-wipe` (`mod/InvasionMod/scenarios/vassals/vassal_wipe.py`), run `20261022-043309-1c2b`, fixture `base`, slot 0, verdict pass. Pictures are compressed to at most 1280x720 (JPEG, about 145 KB each).

| File | Moment |
|---|---|
| `01-village-before-sack.jpg` | The vassal village of 5 buildings, 10 game days after the handover, before the sack. |
| `02-village-of-rubble.jpg` | After the sack: 4 of 5 buildings are ruins, all villagers are deleted, the refugee banner shows. |
| `03-village-after-restore.jpg` | 20 game days after the restore (100 silver, 5 families, goods spawned). |

Limits: the camera shows the village site from far away, so single ruins are hard to see. The AI did not rebuild in 20 game days (standing 4, rubble 4 from day 5 to day 20; metrics `standing_day5` to `standing_day20`).
