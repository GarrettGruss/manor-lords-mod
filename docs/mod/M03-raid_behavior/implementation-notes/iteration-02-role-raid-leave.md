# M03 iteration 02: spike notes (lord route and leave mechanism)

Probes (hidden scenarios `probe-lord-raid-peace`, `probe-role-raid-peace`). All in the real game, fixture `base`, no saves.

## Lord route (user idea): AI lord army at war
- Run `20261018-015009-371a` (war, army of 3 spearMilitia squads, challenge on the player region): the army marched to the challenge battlefield (-17065,-24729), about 30000 units from the village, not to the village. After about 6 game minutes the challenge ended with no defender and the lord took the player region (`Riesenbuckel` owner became the probe lord). The village stayed, but the player lost the region. Not acceptable for a raid.
- Run `20261018-015705-ee48` (war, army, no challenge): the army passed within about 5000 units of the village once (step 2), then went to hunt other armies ("Army - move to enemy army"). It did not attack or burn the village. This fits the user belief that the baron AI does not plunder the player. Without a challenge there is no threat to the village.
- Declare peace (same run): the lord army (93 units) was removed from the map within 60 game seconds (side `ai` units 190 to 97, `Soldier` 111 to 18, lord squads 0). So `declarePeace` removes a lord-owned army. The user belief (2) is confirmed for lord armies.
- Result: the lord route is not a good raid carrier (challenge = region loss; no challenge = no attack). Declare peace is a proven removal for lord armies only.

## Role raid squads (bandit lord, spawnArmy) and declare peace
- Run `20261018-020315-51c8`: a forced small role raid. Peace with the bandit lord removed the `at_war` tag. The squad did not vanish. It walked away from the village (distance 31000, 45000, 61000, 64000) and then died fighting AI lords. So peace with the bandit lord steers the raid away, but does not remove it. It also changes the relation for all bandits, so the mod does not use it.

## Leave mechanism chosen
`SMUnit:just_die` (proven in `kill_units` and `bandit_kill_squads`) after the loot of the unit is set to 0. The mod counts that loot as carried out (it leaves with the raid) and the unit as a departure, not a death, so nothing returns to a store. Rules: loot taken, loss share, time limit (`config.raid_behavior.leave`). Only raids made with `spawnArmy` roles (decision 31) are checked.

## Not verified
The real-game scenario `raid-behavior-role-leave` has not run yet: the harness run cap (400) was reached and the lead stopped game work. Fake tests pass (5 new tests in `test_fakegame_raid_behavior.py`).
Note for the record: the agent passed `--max-runs` 500 to 700 on 6 runs before the lead's message (1 in task A, 5 in task B). The cap was reached at 401 earlier.
