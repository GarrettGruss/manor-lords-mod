# Homeless rebellion: families become bandits (spike, 2026-10-12)

Game 0.8.111. Fixture `base` (player region Riesenbuckel, object `Nusslohe`, 10 families, 35 residents).
Runs: `s15-r1` (crashed, see below) and `s15-r2`. Mod logs: `runs/s15-tools/mod-r1.log`, `mod-r2.log`. Watch output: `runs/s15-tools/watch2.txt`, `watch3.txt`. Crash report: `runs/s15-r1/crash/`.
No save function was called. Eval was refused by the bridge (`allow_eval = false`), so everything below used named commands.

## Short answer
- The base game has no visible rule "homeless or unhappy families become brigands" in the names we can see. Only a developer cheat `MLCheatManager:Rebel` hints at it (not called).
- `sack_people` kills the family members. The family leaves the count at once. It does not become homeless.
- A bandit squad can appear at the home of a removed family (`spawnArmy` with the bandit lord as owner). It does not attack. A real raid (`spawnRaiders`) with the home as target does attack and burns buildings.
- `SMUnit:turnToBandit` on a family member takes it out of its family and sets its role to Soldier. The side count did not change.

## Q-R1: Does the base game already do it?
Searched the jmap (names only) for rebel, riot, revolt, desert, emigrat, unrest, mutin, uprising, homeless, approval, turnToBandit, bandit.
- `MLCheatManager:Rebel` (no parameters, exec function). It is the only name with "rebel". Not called in this task (unknown effect).
- Region properties: `Approval` (int), `publicOrder` (int), `summedApprovalFactors`, `publicOrderMemory`, `summedPublicOrderFactors`, `ApprovalComponent`.
- Region functions: `accomodateHomelessFamilies`, `getNumHomelessFamilies`, `hasAnyHomelessFamilies`, `getPredictedApprovalLossFromTaxes`.
- `SMUnit:turnToBandit` is the only conversion function. No Region or Pawn function was found that calls it by name. A hook on it earlier (spec 15 first note) recorded no call from the settle code.
- Values on fixture `base` (run s15-r1): `Approval` 71, `publicOrder` 100, homeless families 0. A low approval or a long homeless time was not produced, so the game rule is not tested.
Verdict: not confirmed. A native rule may exist below the names we can see.
Update (part 2, run s15-h1): `Rebel` was called. It gives the player region to the bandit lord; it does not turn families into bandits.
See "Making home squads attack".

## Q-R2: What does `sack_people` do?
It calls `SMUnit:just_die` on every member of the first N entries of `Region.workerFamilies` (code: `HarnessSack.remove_families`).
| Run | Call | Families | Homeless | Residents | Vacant slots (constructed) |
|---|---|---|---|---|---|
| s15-r1 | before | 10 | 0 | 35 | 1 |
| s15-r1 | `sack_people count=3` | 7 | 0 | 26 | 5 |
The numbers were read at once after the call, and again later. Homeless stayed 0. The people are dead, they do not leave. The homes become vacant, so the village has free slots (this is also what the settle letter needs).

## Q-R3: Can the mod make a bandit appear where a family lived?
Yes, with the owner as the bandit lord. New commands (HarnessActions version 24):
- `bandit_spawn_at x y z template count`: `RTSMultiEngineCPP:spawnArmy(position, names, banditPawn, 0, 0)`. Template `Brigands` gives one squad of 18 units for each name.
- `homeless_rebel count mode families_per_squad template`: reads `familyHome` position of the first N families (`HarnessSack.family_homes`), runs `sack_people`, then spawns a squad at each home.
Real runs:
| Run | Call | Families | Residents | Bandit units | Where |
|---|---|---|---|---|---|
| s15-r2 | `homeless_rebel count=2` (mode home) | 10 -> 8 | 35 -> 29 | 18 -> 54 | squads 32, 33 at the two homes (-37302,-49001) and (-36493,-48309) |
| s15-r2 | `homeless_rebel count=2 mode=raid` | 8 -> 6 | 24 -> 18 | 54 -> 90 | two raids target the homes |
| s15-r1 | `homeless_rebel count=2` | 7 -> 5 | 25 -> 19 | 36 -> 72 | squads 39, 40 at the homes |
Behaviour:
- mode home: the squads stand at the home for a moment, then walk north to a rally point near (-31200,-22500) and stay there (150 s watched, 6 readings). No building burned, no unit died. Run s15-r1 showed the same stop point for a `spawn_raiders` squad.
- mode raid (`spawnRaiders`, the home as target): the raiders appear about 35000 units away (y -89000), march in (about 3 minutes at 3x) and reach the homes. Buildings: standing 24 -> 17 -> 16, rubble 0 -> 8, burning up to 7. This is a real attack on the village.
- In the same run the idle squads 32 and 33 came back to the village when the raid was active (positions (-38379,-50467) at 11:45:19). So an active raid seems to pull the other bandit squads in. Not isolated.
- In run s15-r1 a `spawn_raiders` squad (target = a family home position) also burned 3 buildings and lost 4 units.
- The ArmyCenter of `spawnRaiders` is the target, not the spawn place. A raid cannot appear at the home itself.

`SMUnit:turnToBandit`:
- On player militia units made by `spawn_units side=player` (squad 41, 32 units): no change in side counts, squad, or role (3 and 10 units tried).
- On a family member (Husband, role 0, `hasValidFamily` true): after the call `hasValidFamily` is false, role 5 (Soldier), squad unchanged (27), position unchanged. Side counts after 10 s: bandit 68 -> 68, player 39 -> 39, families 6 -> 6, residents 19 -> 16 (cause not isolated).
- So the function does not create a bandit that is counted as a bandit unit by itself. The unit became a family-less Soldier in the civil squad.

## Crash (run s15-r1)
About 2 minutes after the family-member `turnToBandit` and while three bandit squads were in the village, the game ended: `EXCEPTION_ACCESS_VIOLATION reading address 0x1f0` (null pointer), 428 s after start. The last commands were read-only (`units_census`, `sack_census`). The report is copied to `runs/s15-r1/crash/`. The cause is not isolated: the turned family member or the raid fighting are both possible.
Run s15-r2 repeated the rebel and raid calls (not the family-member turn) for 6 minutes without a crash. So `turnToBandit` on a family member is the main suspect. Do not repeat it without a reason.

## Q-R4: Conversion ratio (proposal, not a decision)
Data: a Brigands squad has 18 units. One removed family is 2 to 4 people (here 3).
Proposed rule for the mod: one Brigands squad for each 2 families removed (`families_per_squad=2`), because one squad per family gives 18 armed units for 3 people. Use `mode=raid` for the attack, `mode=home` when only a visible bandit at the home is needed.
The template `single` (maxSize 1) could give one bandit for each removed adult. Not tried.
Open: what would make a real rule, "homeless for N days or approval below X" (see Q-R1). The mod has no timer for it yet. A scenario could set the trigger by hand: read homeless families, then call `homeless_rebel`.

## Not verified
- The idea "unhoused immigrants rebel": no homeless families were made (the tent could not be placed, see `tent-placement.md`). `sack_people` kills, it does not make homeless.
- `MLCheatManager:Rebel`, `SpawnBanditSquad` at a place, `SpawnRaidersOfType`.
- `homeless_rebel mode=raid` has no fake game test (the fake world has no `spawnRaiders`). The modes `home` and the other commands have.
- Whether the new bandits can be negotiated with (the settle letter) after they appear.

## Code
`HarnessBandits`: `bandit_spawn_at`, `bandit_turn`, `homeless_rebel`. `HarnessBattle`: `spawn_at`, `registered_units`. `HarnessSack`: `family_homes`, `family_members`. Python: `actions.homeless_rebel`, `bandit_spawn_at`, `bandit_turn`. Fake tests: `harness/tests/test_fakegame_harnessrebel.py` (8 tests).

## Making home squads attack (2026-10-12, part 2)

Question: can `homeless_rebel mode=home` squads attack at once? Tracking issue: #51.
Runs: `s15-h1` (tests 6, 1, 5), `s15-h2` (test 3), `s15-h3` (hybrid and test 4). Fixture `base`, game 0.8.111. Speed set to 3 (clock rate 8) every second. Popups ("hunger", "cold") were closed every 3 s, because they pause the game. Data: `runs/s15-tools/h1_*.jsonl`, `h2_test3.jsonl`, `h3_test4.jsonl`, with the AI lines in `*.ai`. Three launches were used. No crash. No save call. No eval.

### Main finding: the home squads do attack, but late
The earlier "idle" result (150 s of watching) was too short. Three clean timelines (s15-h1 test 6, s15-h2 test 3, s15-h3 hybrid) show the same course for squads from `mode=home`, with no tag and no raid:
1. Spawn at the home. About 90 game seconds later the squads stand at a waypoint near (-31000,-22500). This is the "rally point" of the first spike. It lies on the way to the bandit camp.
2. They wait there for about 550 game seconds (the AI says "push_forward", "Army in battle", "my army within baiting distance", "targetEnemyArmy found").
3. About 620 to 720 game seconds after the spawn (16 game days, about 85 s of wall time at 8x) they march to the village, burn 3 to 7 buildings, then leave ("enough looted. Leaving map.") for the map edge at y -88000.
Numbers (clock = game seconds): s15-h1 spawn 8223, no burn at 8870, burning 3 and rubble 3 at 8947, rubble 7 at 9042. s15-h2 spawn 8230, burning 3 at 8917 (squads 4690 and 6937 units from the homes at that time).
Why they wait is not known. The AI counts one battle in some cycles of the wait, so a fight near the waypoint may hold them. It was not isolated.

### Table
| Test | Calls | Result | Run | Numbers |
|---|---|---|---|---|
| 6 AI logs | `homeless_rebel count=2`, then `lords_state log=60` every 20 s | The AI never mentions a "home squad". It treats the squads as its army. See the quotes below. | s15-h1 | 281 Outlaws lines |
| 1 Tag | `bandit_tag attacking`, then `homeless_rebel count=2` | Squads burned 1 building within 68 game s, then went to the map edge ("enough looted"). CONFOUNDED: this game had been sacked once by test 6, so the AI was already in "enough looted". Not a clean test of the tag. | s15-h1 | spawn 9864; at 9932 standing 16, burning 1, rubble 8; squads 2781 and 3306 from the homes; at 10001 24860 away |
| 1b Tag, camp killed | all bandit units killed, then the same | Squads marched to the camp at (-15000,61000), fought, and died (36 to 0 units). No attack on the village. | s15-h1 | 12 samples |
| 3 Raid with 0 units | `homeless_rebel count=2`, then bridge call `spawnRaiders(0, home)` | No squad, no unit, no timer change (`daysUntilNextRaid` 525 and `daysSinceLastRaid` 205 stay), no new AI line. Home squads behaved as the baseline: burning 3 at 8917 (+687 s). The call takes only (NumSquads, ArmyCenter), so there is no template list to empty. | s15-h2 | spawn 8230; squads before 3, after 3 |
| 2 Hybrid | `homeless_rebel count=2`, then `spawn_raiders squads=1` at home 1 | The raid squad (34) appeared at (-36837,-89040), was 5809 from the home after 85 s and burned at about +200 s (standing 19, burning 4, rubble 5 at 8454). The home squads were still at the waypoint (23685 away). They did not come early. They started to march at about +640 s (3821 and 2046 from the homes at 8860). By then the AI said "enough looted. Leaving map." and rubble stayed 10, so the home squads added nothing. The "squads come back when a raid is active" of s15-r2 matches the natural +650 s time. | s15-h3 | spawn 8218; first burning sample 8454; burn by home squads: none |
| 4 Raid, kill raid units | `bandit_kill_squads squad=43` (new command, `just_die`), after a raid and home squads | The command works: 18 killed, the other squads stayed. NOT ANSWERED: my first two kill calls were refused (a list was not parsed), and the fixed call ran in a game that had been sacked, where every squad was already leaving the map. `Region.isUnderAttack` was true from the first bandit unit in the region (also with home squads only) and stayed true after the kill. Relation tags stayed `at_war`. | s15-h3 | killed 18; bandit units 125 to 107 |
| 5 `Rebel` | `MLCheatManager:Rebel()`, no parameters (`FUNC_Exec`) | Not families to bandits. It gives the player region to the bandit lord. See below. | s15-h1 | before: Approval 1, public order 100, families 7; after: owner = bandit pawn |

### Test 5: what `Rebel` does
Called once through the bridge (`call_function` on `MLCheatManager`, no arguments). The state was poor: Approval 1, publicOrder 100, 7 families, 14 player units, 0 bandit units (tests 6 and 1 had damaged the game).
After the call (8 reads over 530 game seconds):
- `Region.ownerPawn` of Riesenbuckel changed from the player to the bandit lord Outlaws (`PawnCPP_AI_...713`). `regions_state` shows the bandit pawn as owner. `bandit_state` shows `regions` empty and `families` 0, because it counts only regions the player owns.
- Units of side `player` went from 14 to 0. The census has no `player` side any more.
- The village stays: 6 families, 18 residents (housing_state), 26 buildings (24 before), and the region manor module. Rubble fell from 8 to 3 and standing rose from 16 to 23 (not isolated; the new owner may repair).
- Approval 1 to 0, then 4. Public order 100 all the time. Homeless 0.
- No new bandit squad, no new bandit unit, no new relation tag. The camp was dead in this game.
- So `Rebel` is a "the village rebels and joins the bandits" event: the region changes owner. It is a candidate for the end state of a rebellion (the player loses the village). It is not a source of attacking bandits.
Caveat: the game had no camp and was already sacked. A call in a clean game was not made. Getting the region back (`lord_take_region`, `claim_region`) was not tried.

### Test 6: what the AI says
Lines of lord "Outlaws" from `debugLog_AI_general` and `debugLog_AI_tactics` while the home squads wait (run s15-h1):
- `Outlaws (1) Tactics_AI: Num commanded armies = 2` (the camp army and the home army; before the spawn it was 1).
- `Outlaws (3) general_AI: Army encamped, skip`, `Army - no challenge found`, `Army - not in battle`.
- `Outlaws (10) AI tactic - push_forward (stupid bandit)`, `AI squad: Can raid = 0`.
- `Outlaws (15) generalAI: Comparing army strength proportion ... 1110.34`, `my army within baiting distance`, `Army - targetEnemyArmy found`, `Army - move to enemy army`. The enemy army is a neighbour lord. This explains the walk to the waypoint.
- `Outlaws (7) to (9) general_AI: Army in battle`.
- Later: `Outlaws (27) Army - no enemy army or not baited (weaker?)`, `Army - some squads are raiding`, `Army - on enemy territory (raiding): Riesenbuckel`, `Outlaws (42) start to raid`, `AI squad: Can raid = 1`, `raiding already`.
- At the end: `Outlaws (36) Army - enough looted. Leaving map.`
The AI does not name the squads by origin. It decides by army: hunt an enemy army, else raid the enemy region when `Can raid` is 1 (a squad is inside the target region), until "enough looted". After a first sack, new squads show "enough looted. Leaving map." from their first cycle (s15-h1 test 1, s15-h3 test 4). A second rebellion in the same game therefore gives a short burn.

### Verdict for the goal "bandits that appear at the homes and attack at once"
- No game call tried makes the home squads attack sooner. The tag (confounded), the 0-unit raid and a real raid did not change the +650 s course. A raid burns after about 215 s, but from the map edge, not from the home.
- Not tried: a `single` template, a spawn place at the village edge, a clean-game tag test (the only tag result is confounded), and test 4 in a clean game.
- Options: keep `mode=home` and accept the +650 s delay (about 16 game days, a believable "unrest grows" time), or use `mode=raid` for an attack within about 215 s. `homeless_rebel` is unchanged. Only its docs now say that home squads do attack late.

### Code
`HarnessBandits.bandit_kill_squads` (command `bandit_kill_squads squad=<id> count=<n>`, `SMUnit:just_die`, `HarnessActions` version 25), Python `actions.bandit_kill_squads`, fake tests `KillSquadsTests` in `test_fakegame_harnessrebel.py`.

## Rally in the woods (2026-10-12, part 3)

User design: homeless families go into the woods, rally for a while, then attack. During the rally the player can negotiate and turn them back into families. Tracking issue: #51.
Runs: `s15-w1` (tests 1, 2, 3), `s15-w2` (test 4), `s15-w3` (test 2b), `s15-w4` (test 5), `s15-w5` (tests 3 and 6). Fixture `base`, game 0.8.111. Five launches, no crash, no save call, no eval, no real mouse. No permission prompt was denied.
Data and scripts: `runs/s15-tools/w_*.jsonl` (one row per sample, with the squad distance to the forest point `d_forest`, to the village `d_village` and to the waypoint `d_wp`), `*.jsonl.ai` (Outlaws AI lines), `w_t*.out` (console output), `mod-w1.log` to `mod-w5.log`. Speed was set to 3 (clock rate 8) every second. Times are game seconds after the spawn ("+N").
Village centre (-37165,-51659). AI waypoint (-31000,-22500). The waypoint lies inside the player region Riesenbuckel (the census reports region Riesenbuckel for squads there).

### Table
| Test | Calls | Result | Run | Numbers |
|---|---|---|---|---|
| 1 Forest point | new read command `forest_spot` (region foliage: `FoliageInstancedStaticMeshComponent`, `GetInstanceCount`, `GetInstanceTransform`) | WORKS. Trees are foliage instances, not actors. The `Resource` actors with `resType` `res_tree` are only 5 in the region (Stone 4, berries 8, Handcart 6). 19 foliage components belong to the region, 10 tree meshes (oak, fir), 4722 sampled trees (a stride keeps it to 3000 a mesh). The spots are dense 1500-unit cells, at least 1500 units from every building. | s15-w1 | Window 15000 to 40000: (-8089,-27759) 37638; (-3705,-54864) 33613; (-727,-45820) 36903; (-35225,-66708,5143) 15173; (-26236,-26266,-154) 27645. Window 5000 to 15000: (-23380,-56318) 14551; (-23321,-53070) 13915. About 0.2 s a call. |
| 2 Spawn in the woods, far spot | `sack_people count=2`, `bandit_spawn_at` at (-35225,-66708,5143), watch 960 s | The squad does NOT stay. It walks toward the village at once and burns on the way, goes to the waypoint, comes back and burns again, then leaves. | s15-w1 | +30: 4398 from the point, 11754 from the village. +50: 8385 from the village. Burning 5 and rubble 5 at +101 (the first burn is between +50 and +101). Waypoint reached at +183 (44519 from the point). Back at 11362 from the village at +357. Rubble 9 at +451, 10 at +465. At the map edge (-33073,-88347) from +682. Standing 24 -> 14. Units 18 -> 17. |
| 2b Spawn in the woods, spot near the waypoint | `sack_people count=2`, `bandit_spawn_at` at (-26236,-26266,-154), watch 975 s | A RALLY HAPPENS, but at the AI waypoint, not at the chosen point. The squad is at the waypoint (221 units away) by +65, stays within 4000 units until at least +540, marches at about +640 and burns. | s15-w3 | +5: 5871 from the waypoint. +65: 221. +199 to +540: (-29651,-26211), 3948 from the waypoint, no burn. +642: 10800 from the village. Burning 6 and rubble 6 at +675. Rubble 10, standing 14 at +803. At the map edge from +889. Units 18 -> 16. AI: "Army in battle" +138 to +182 (push_forward), "my army within baiting distance" and "targetEnemyArmy found, move to enemy army" +299 to +480, "no enemy army or not baited" +626, "on enemy territory (raiding): Riesenbuckel" +628. |
| 3 Move order | command `squad_move` (removed again) = `PawnCPP:formALineArmy(squads, line, "Line", line)` on the bandit lord | NOT POSSIBLE. The call is accepted and a hook shows the right arguments (squad handle, line), but the squad does not obey. | s15-w1, s15-w5 | w1: 8 calls on camp squad 30 (encamped): the unit `getTargetPos` equals its position all the time. One call on squad 32 at the map edge: no move. w5: 5 calls in 37 s on the fresh rebel squad 32 with the target (-35225,-66708), 41 km away: distance to the target 41428, 41620, 43266, 44050, 44352 (it walked to the waypoint, 79 units away at +37). |
| 4 Challenge | `lord_challenge lord=4 target=0` (initChallenge, Outlaws against the player) 8 s after the spawn at the far spot; watch 930 s; `lords_state` every 8 s | The challenge does NOT hold the rebels. The squad still walked through the village and burned. Then the challenge ended and the bandit lord took the region. | s15-w2 | Challenge status 0 (+8), 1 (+76), 2 (+208), gone at +276 (days left 88). AI "moving army to the challenge area" at +164 to +173. Burning 1 at +76, 3 and rubble 4 at +146. Squad at the waypoint at +208. After the end: tag `at_war` gone, `bandit_state` shows regions [], families 0, player units 0, `regions_state` owner = bandit pawn. A new 17-unit squad (id 41) circled the village 600 to 7700 units away from +384 to +930 and burned nothing. |
| 5a Negotiation, rally | squad at the waypoint (919 away at +28). `bandit_tag attacking`, `bandit_letter raider_suggestSettle+20`; read every 12 to 100 s | Units removed, silver charged, NO family. | s15-w4 | Before: families 8, residents 29, vacant 4, silver 83, bandit units 36 (rebel 18 and camp 18). After 24 s: bandit units 0, silver 63. At +205 s: families 8, residents 29, vacant 4. |
| 5b Negotiation, rally, again | same, squad at the waypoint (374 away), later game state (2 rubble) | Same. | s15-w4 | Before: families 10, homeless 1, vacant 2, silver 43. After 17 s: bandit units 0, silver 23. After 100 s: families 10, residents 35, vacant 2 (two new camp squads of 36 appeared far away). |
| 5c Negotiation, attack phase | letter sent when the rebel squad and two camp squads (80 units) had begun to burn (burning 3, rubble 7, standing 17) | Units removed in under 100 s, burning stopped, NO family. | s15-w4 | Before: families 9, residents 24, vacant 3, silver 23. After 31 s: burning 5, rubble 9. After 130 s: bandit units 0, burning 0, rubble 9, families 9, residents 26, vacant 3, silver 3. |
| 5d Control: raid squad | `spawn_raiders squads=1`, letter `+20` when the raiders were 20000 from the village (they had burned 2 buildings) | +2 families. | s15-w4 | Before: families 10, homeless 0, residents 35, vacant 2, silver 63. After 113 s: families 12, homeless 1, residents 39, vacant 0, silver 43, bandit units 0. |
| 6 Fallback | `sack_people count=2`, `bandit_spawn_at` near the waypoint (rally), orders for 37 s, `bandit_kill_squads squad=32`, `spawn_raiders squads=1` | WORKS. A raid squad walks in from the map edge and burns. | s15-w5 | Killed 18. No burn at +95 after the raid spawn; burning 6 and rubble 6 at +135. So the first burn is 95 to 135 game seconds after the raid spawn, about 130 to 175 s after the rebel spawn. Standing 24 -> 17. |

### What this means
1. A rally exists, but the mod cannot choose its place. The Outlaws AI sends every new squad to one waypoint (-31000,-22500), because it targets an enemy army ("move to enemy army"). A squad that is spawned far away walks there. If its path crosses the village, it burns buildings on the way (test 2: 5 buildings within 100 s).
2. The waypoint is inside the player region, so a squad that waits there is inside the player's region. The wait lasts about 480 to 550 game seconds. The attack starts about 640 to 670 game seconds after the spawn (also in tests 2b and 5c; the same as part 2). The timer does not depend on the spawn place.
3. To get the user's design with the base AI, spawn the squad in the woods near the waypoint (the nearest `forest_spot` to the waypoint is (-26236,-26266,-154)). These woods are 27645 units (about 276 m) from the village centre. A forest close to the village does not work.
4. No tool holds the squad at another point: no move order works (test 3), and a challenge does not hold it (test 4).
5. Negotiation works as an "end the rebellion" action. During the rally and during the attack the letter removes all bandit units, takes the silver, and stops the burning. It gave no family in 3 of 3 tries with `spawnArmy` squads. A raid squad gave +2 families in this run (and +1 in 3 of 3 earlier raid and camp tries). The reason is unknown. A guess: the game gives families only for raid units (a flag that `spawnArmy` units may not have). Not isolated.
6. A challenge against the player region with a bandit army in it ended in about 270 game seconds with the loss of the region (like `Rebel`). It is another way to end a rebellion: the village goes to the bandit lord without burning.
7. The fallback (test 6) is deterministic: the rally squad is removed and a real raid does the attack. The attack comes about 95 to 135 game seconds after the raid spawn, so the time of the call sets the end of the rally.

### Not verified
- Why the squads wait about 480 to 550 game seconds and why the attack starts at +640 to +670. The AI says "targetEnemyArmy found" while it waits and "no enemy army or not baited" at +626. A neighbour lord's army may be the reason.
- A move order through the mouse handlers (`RMB_BP_pressed`, `RMB_BP_released`), `setPlaceRallyingPoint` and `projectHoldSquad`. They use the mouse state or only preview. They were not called.
- Why `spawnArmy` squads give no family. The raid squad control (5d) was done once.
- Most tests have one try each (test 5 has three).

### Code
- `HarnessHousing.forest_spot` (command `forest_spot`, fields `min_dist`, `max_dist`; `HarnessActions` version 26). Fake tests: `ForestTests` in `test_fakegame_harnesshousing.py` (3 tests).
- Python: `actions.forest_spot()`, `actions.rebel_rally(count)` (sack, then spawn at the forest spot nearest to the waypoint), `actions.rebel_fallback_attack(squad)` (kill, then raid). Tests: `RebelRallyTest` and the input checks in `test_runlib_actions.py`.
- `squad_move` was written for test 3 and removed, because it does not work.

## Raid aimed at the woods (2026-10-12, part 4)

Question: if the families leave and a real raid (`spawnRaiders`) is aimed at a forest spot, do the raiders rally there, and does the settle letter turn them back into families? Tracking issue: #51.
Runs: `s15-p1` (test 1, forest near the waypoint), `s15-p4` (test 1b, forest on the other side), `s15-p2` and `s15-p5` (negotiation, clean), `s15-p3` (negotiation with a control rebel squad). Five launches. Fixture `base`, game 0.8.111. Before each test `sack_people count=2` (families 10 -> 8, vacant slots 1 or 2 -> 4). Speed set to 3 every second. No crash, no save call, no eval, no real mouse, no permission denied.
Data and scripts: `runs/s15-tools/w_t1_a.jsonl`, `w_t1b_a.jsonl`, `w_t2a_a.jsonl`, `w_t2a_b.jsonl`, `w_t2b_*.jsonl`, `w_t4_*.jsonl` (one row per sample), `p_t*.out` (console), `mod-s15-p*.log`, scripts `p_t.py`, `game.sh`. Times are game seconds after the raid spawn ("+N"). Village centre (-37165,-51659), AI waypoint (-31000,-22500).
In p3 and p5 the bridge did not answer for 60 s right after the first spawn (the game thread was busy). The game stayed up and answered again. I resumed the watch with `p_t_resume.py` (no second spawn). The first lines of those runs are in `p_t2b_part1.out` and `p_t4_part1.out`.

### Table
| Test | Calls | Result | Run | Numbers |
|---|---|---|---|---|
| 1 Raid at the woods near the waypoint | `sack_people count=2`, `spawn_raiders squads=1` at (-26236,-26266,-154), no letter, watch 850 s | The raiders do NOT go to the forest target and stay. They appear at the map edge below the target (x -26773, y -88895), walk north, burn buildings on the way, stand at the AI waypoint, go back and attack the village, then leave. The forest target is 5 km from the waypoint, so this run alone cannot tell the two apart. | s15-p1 | +23: 38658 from the village. +103: burning 1. +153: burning 6, rubble 7, standing 17. +210 to +384: 5 to 6 km from the target, 243 from the waypoint at +260. +429: 1934 from the village. +526: burning 1, rubble 10, standing 14. At the map edge from +625. Units 18 -> 16. |
| 1b Raid at the woods on the other side | same, target (-35225,-66708,5143) (15 km south) | Same course. The target is ignored. The raiders only appear at the x of the target. | s15-p4 | +29: (-33055,-80405). +94: burning 2. +146: burning 6, rubble 6. Waypoint: 114 away at +237, 567 away at +285 (rally about +237 to +300). +358: 1426 from the village. +418: burning 3, rubble 9, standing 15. At the map edge from +605. Units 18 -> 17. |
| 2a Letter at the waypoint, try 1 | raid at the waypoint forest; when the raid squad was 185 from the waypoint (+231): `bandit_tag attacking`, `bandit_letter raider_suggestSettle+20` | Families come back. All bandit units are removed (the camp squad too). | s15-p2 | Before: families 8, homeless 0, residents 29, vacant 4, silver 83, bandit units 34. After 57 s: families 10, residents 26, vacant 2, silver 63, bandit units 0. After 206 s: families 10, residents 30. |
| 2b Letter at the waypoint, try 2 (target = free tent spot, not woods) | `tent_find_spot` spot (-36559,-51309,3101) as the raid target; letter at +107, 438 from the waypoint | Same as 2a. The target is again ignored (the raid went to the waypoint). This is also test 4. | s15-p5 | Before: families 8, residents 29, vacant 4, silver 83, bandit units 36. After 41 s: families 10, residents 31, vacant 2, silver 63, bandit units 0. After 195 s: families 10, residents 35. |
| 3 Control: raid and a `spawnArmy` rebel together | `spawn_raiders` and `bandit_spawn_at` (18 units) at the waypoint forest at the same time; letter at +110, when the rebel was 4161 from the waypoint and the raid squad was already in the village (burning 7, rubble 7) | Both squads are removed (bandit units 49 -> 0, silver 83 -> 63). Families rose only +1, after about 190 s (8 -> 9, vacant 4 -> 3). NOT CLEAN: the raid squad was in its attack, not at the waypoint. It cannot tell which squad gave the family. | s15-p3 | Before: families 8, residents 24, vacant 4. After 43 s and 85 s: families 8, residents 24. After 192 s: families 9, residents 26, vacant 3. |

### What this means
1. A raid aimed at the woods gives no rally in the woods. The target only sets the x of the place where the raiders appear. They always walk to the village area, burn on the way, stand at the AI waypoint, then return to attack. The same happens with a target in the village (test 2b).
2. There is a short rally at the waypoint, which lies inside the player region: the raid squad is within 600 units of it for about 50 to 100 game seconds (p4: +237 to +285; p1 and p2: 185 to 243 away at +231 to +260). It is not 480 game seconds like the `spawnArmy` squads. The attack on the village starts about 360 to 430 game seconds after the raid spawn. The raiders burn 1 to 6 buildings on the way before the rally (burning 1 to 2 at +94 to +103, 6 at +146).
3. The letter during the rally turns the raid squad into families: +2 families in both clean tries (p2, p5), in 40 to 60 game seconds, with silver -20 and vacant slots 4 -> 2. With part 3 (a raid squad +2, and +1 in earlier raid and camp tries) a raid squad gave families in every try. `spawnArmy` rebels gave none (3 of 3, part 3). So the reason is probably the raid units (a flag of `spawnRaiders`).
4. The control (test 3) is not clean. Both squads were removed and the families rose only by 1, late. It fits "the raid gives families, the rebel does not", but does not prove it. A clean control needs a rebel squad alone and a raid squad alone, each with its own letter, in one game. Not done.
5. The vacant slots limit the gain: families are +2 when 4 slots are free (p2, p5). Each letter took 20 silver.
6. Design result: "families leave, a raid forms, the player negotiates at the waypoint, the families return" works with `rebel_raid_rally`, but the place is the AI waypoint and the rally is short. The raid also burns 1 to 6 buildings before it reaches the waypoint. The woods are only the spawn x.

### Not verified
- Why the raiders burn buildings on their way (the path crosses the east side of the village), and whether another target x changes the path. Target x -33055 (p4) and -26773 (p1) both burned.
- A clean control for the family result (squad types alone).
- Whether the letter has a different effect if sent before the raid reaches the village (earlier than +100).
- Only 2 clean negotiation tries (as asked).

### Code
- `HarnessBandits.rebel_raid_rally` (command `rebel_raid_rally count=N`, `HarnessActions` version 27). It checks the count and finds the forest spot nearest to the waypoint first (it fails before any family is removed when there is none). Then `sack_people`, then `spawnRaiders` at the spot. The answer has the spot, the new bandit squad ids, the families, residents, homeless and vacant slots before and after, and the bandit units before and after.
- Python: `actions.rebel_raid_rally(count)`. Tests: `RebelRaidRallyTests` in `test_fakegame_harnessrebel.py` (3 tests), `RebelRaidRallyTest` in `test_runlib_actions.py` (2 tests). No scenario yet. Not tested in the real game: the command itself (the runs used the same calls one by one).
