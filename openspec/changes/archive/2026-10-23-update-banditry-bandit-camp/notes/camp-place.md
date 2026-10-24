# Camp place and runs

`spawnBanditCamp()` has no argument. The game picks the place. The mod reads the new camp site (`HarnessEncampment.encampment_sites` type 100) and logs it (`camp_at`, `camp_distance` from the player pawn).

| Run | Fixture | Verdict | Leave | Camp distance (game units) | Pawn created |
|---|---|---|---|---|---|
| 20261024-021832-7861 | base | pass | 9 families, 1 camp, 18 units | 42450 | no |
| 20261024-025922-6009 | base | pass | 9 families, 1 camp, 18 units | 48617 | no |
| 20261024-024700-6523 | base | crash after the camp and a camera move (pawn teleport), before speed 1 | 9 families, 1 camp | 113450 | no |
| 20261024-023731-9476 | playtest-noai | pass | 4 families, 1 camp, 18 units | 66315 | yes |
| 20261024-023120-48a6 | playtest-noai | harness_error (bridge timeout after the leave; camp was made, distance 89338) | 4 families | 89338 | yes |

Other non-pass runs: 20261024-021558-0d65 (base, crash at set_speed 3 before the leave, no camp code run), 20261024-023450-ffd2 (noai, bridge timeout before the leave), 20261024-025606-f3e0 (base, close_popups timeout at start). Several games ran on the PC at the same time.

Result: the camp appears 42000 to 113000 game units from the village (random, not on a chosen border point). The mod cannot choose it. Owner question 2: a follow-up can try to move the camp.
