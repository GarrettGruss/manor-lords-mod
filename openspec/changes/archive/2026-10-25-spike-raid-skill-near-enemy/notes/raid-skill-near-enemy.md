# Skill 19 next to an enemy building

Probe: `harness/scenarios/probe-raid-near` (hidden). Game 0.8.117, fixture `playtest-noai` (no AI lords, no bandit camps), game thread calls through the bridge. Switches: `HARNESS_PROBE_FLAG` (false, true, none), `HARNESS_PROBE_TARGET` (camp, village), `HARNESS_PROBE_MODE` (near, click), `HARNESS_PROBE_BUILD_DAYS`, `HARNESS_PROBE_SUPPLY`, `HARNESS_PROBE_OFFSET`. Eval was refused (`allow_eval = false`, not changed), so reads use only structured ops.

## Verdict
Turning on skill 19 next to an enemy building does NOT start a visible raid. It does start something native: the squad walks by itself into the enemy village and stops there with a flame on its banner. After 180 to 400 game seconds next to built enemy buildings, no loot, no fire, no unit moved, and `PawnCPP:isAnySquadRaiding` stayed false. Flag false and flag true behave the same. Turning it off removes the flame and nothing else changes. This is the same result as in peacetime.

## How the squad got there
- No Lua call moves a player squad (formALineArmy is ignored, see the archived steering notes). I tried a real right click again (`click` mode, `steer_cursor` plus `order_with_mouse`): the click point was not the planned one (8710, 3506 instead of a point 600 units away) and the squad did not move. Not usable without more work.
- What works: `ctx.bridge.centre_camera_on(x, y)` moves the player pawn (the camera). `spawn_units("player", "spearMilitia")` then spawns a 32-man player squad at the pawn. So a squad stands 50 to 2 000 game units from the target. Squad ids were 20 in every run.
- A rival village: `spawn_ai_lord`, `lord_relations`, `lord_found_village(lord, region, supply=2)`, `lord_declare_war(lord, 0)`, then `lord_start_ai(lord, 1, can_build=True)` and 12 game days (`run_game_days(12, speed=3)`). It gave 12 buildings of the lord, 7 of them built (`IsConstructed`), region `waldbrand`. The village lies around world (0, 0) to (6 000, 4 000), not at the region actor point (-48 273, -15 185) that `encampment_regions` prints. Use the building positions.
- A bandit camp (`spawn_bandit_camp`) is NOT usable as a raid target: its `SMBuildingMaster.Region` is invalid and its owner is the bandit pawn. Skill 19 on a squad 1 650 units from the camp: the squad did not move (run raidnear-1).

## Runs
| Run | Setup | Skill 19 | Result |
|---|---|---|---|
| raidnear-1 | camp, brigands killed, squad 1 654 units away | on, flag false, 180 s | `active` true, squad did not move, `isAnySquadRaiding` false, camp parts 17 all the time |
| raidnear-3 | village (frames only), squad 2 088 away | none (control) | squad stays still 180 s |
| raidnear-2, -4, -6, -8 | village, lord without building (frames), flag false | on | squad leaves at once, walks about 50 km in 40 s to near (900, -900), stops. No raid |
| raidnear-7 | same, flag true | on | same move to (813, -1106), flame on the banner, no raid |
| raidnear-9 | supply 2, 400 s | on, flag false | stops 90 units from a frame, no raid in 400 s |
| raidnear-10 | lord built for 12 days (7 built buildings) | on, flag false | moves to (930, -306), no raid in 300 s |
| raidnear-12 | click mode, flag false | on | the click did nothing, then the same move, no raid in 240 s |
| raidnear-13 | camera on a built building (squad 934 away at start) | on, flag false, 240 s | squad ends 55 units from the built building (717, -1024), no raid. `IsSkillActiveForSquad` true, `isAnySquadRaiding` false |

The squad stops at a point near the village center (several hundred to 1 300 units from the buildings), not at one chosen building. The stop points differ by run (329 to 960 in x, -1 200 to -300 in y).

## Evidence
`evidence/` (see its README). The banner flame shows skill 19 is active. The control run shows the squad does not move without the skill.

## Not verified / open
- Why no raid starts. The native mod waits until 75% of the men stand within 30 m of the building (3 000 units, the mod says 30 m). In run raidnear-13 the squad stood 55 units from a built building and still no raid started. Open: the squad may need the `rallied` state (set by a real mouse click), a real armed unit type, or a building with goods. Not tested: `retinue` squads, a squad that was rallied by the mouse, goods in the enemy storehouse (the lord village has few goods), an enemy village with families.
- The enemy buildings are mostly small work sites and clearings: the pictures show little to burn. A big built village may behave differently.
- Loot carried by the squad units was not read.
- No crash. No save call. Eval stayed off.
