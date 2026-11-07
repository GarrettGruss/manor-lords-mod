# Spike: a native retinue squad of 5 men (change add-contract-retinue-reward, #591)

Probe: mode `rinit`, `rhire`, `rbound`, `rsquads`, `rtype`, `rsq`, `runits`, `rpaths` of `mod/shared/HarnessLoanProbe` (command `loan_probe`), test scenario `harness/scenarios/probe_retinue_native.py`.
Fixture `manor-bailey` (a built manor, 5 bound retinue men in squad 22, limit 12, hire cost 50 silver). All runs on slot 2 (config.json checked).

## Results
| Question | Answer | Run |
|---|---|---|
| Can a script add a native retinue squad? | Yes. `PawnCPP:InitializeEmptyRetinueSquad(region)` with the real region object (`ManorCore.player_region()`) adds an empty squad (id 24, 0 men) to `commandedSquads`. The earlier failure (iteration 03) came from passing the region as a string. | 20261106-235527-c84c |
| Can the player recruit into it with the native cost? | Yes. After the call, `SMBuildingMaster:hireExtraRetinue()` hires into the NEW squad (bound list of the manor = the new squad only), 50 silver for each man, the same call that the retinue editor uses. Five calls give 5 men (squad 24: 5 living men, silver 100000 to 99750). The limit is the native limit of 12 for each squad (`getModularGarrisonLimit`), not 36. | 20261106-235727-0c5c |
| Does it survive a save and a load? | Yes. Guarded `save_game` (keep=True), then a load in a second run: squads 22 (5 men) and 24 (5 men) are both there, the same ids. `getBoundRetinue` has the 5 men of squad 24 and one more `hireExtraRetinue` gives 6 men, 50 silver. The save folder had the kept slot `saveGame_60`; it was deleted after the check. | 20261106-235727-0c5c (write), 20261106-235907-dbcf (read) |
| Can a squad be told as retinue from unit properties? | No. All human units are `VAMP_DefaultUnit_C`. No property of a unit or of the pawn or manor with "Retin", "Retain", "Noble", "Compan" or "SquadT" in its name differs (only `targetSquadSize`). `getSquadStatus` differs (`status_ready_to_rally`, `status_missing_recruits`, `status_moving`) but it changes with the squad state. | 20261107-000736-08cb, -001044-e724 |
| Read `squadType` of `getSquadByID`? | Hangs: the command got no answer (dangerous list: do not read Squad structs). Do not use. | 20261107-001147-9019 |

## Consequences for the design
- Reward: a native squad (`InitializeEmptyRetinueSquad`, then 5 `hireExtraRetinue`). The game saves and loads it. The mod needs no respawn code. The mod pays the 5 men (it adds back the silver that the hires cost), the player pays the normal cost to grow the squad.
- The native hire stops at 12 men for each squad. The owner expected 36. Native recruiting cannot go above 12 (code constant, see iteration 02). This is an owner question.
- The mod must know which squads are retinue squads, because no safe read tells it. The mod keeps a saved list of retinue squad ids (`retinue_squad_ids`). The ids are stable across a load. The ids come from: the bound squad of the manor (read at each tick), and the squads that the reward makes.
- Loan return of a native retinue squad: the same native route (a new empty squad, then one `hireExtraRetinue` for each loaned man, silver refunded).
