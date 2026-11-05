# Loan units: findings (spike-loan-units, #568)

Probe: `mod/shared/HarnessLoanProbe` (command `loan_probe`), test scenario `harness/scenarios/probe_loan_units.py`. Fixture `playtest-noai`, slot 1. Units come from `spawn_units` (player, `spearMilitia` 32 men, `retinue_tier1` 36 men). Runs (all slot 1, config.json checked): loan-sq-plain, loan-remove (harness bug: mode name with underscore, no result), loan-remove2, loan-respawn, loan-lose, loan-fam-plain, loan-sq-far. No crash.

## Squads
| Method | Works | Result |
|---|---|---|
| Hide: `SetActorHiddenInGame(true)` + `SetActorEnableCollision(false)` | Visual only | 32 men invisible (picture), banner icon stays. Squad stays commanded (`commandedSquads` 1), census still counts 32 player units for 2 game days. The player can still order it. Show restores everything (same units, same ids). |
| Move the actor away (`K2_SetActorLocation` z -50000) | Visual only | Actor moves, `realPos` (the game position) does not. Same as hide. Restore works. |
| `PawnCPP:addRemoveSquadRequest({Value=id})` | Yes | Within 3 game s: `commandedSquads` 1 to 0, the units leave the unit list, no bodies (dead count stays 24), no crash. Squad id is gone. |
| `just_die` on all units (`clear_battle`) | Yes | Squad leaves `commandedSquads` (0). 36 bodies stay (dead 24 to 60) and stay after 2 game days. Bodies can be hidden (earlier spike). |
| Respawn after removal (`spawnArmy`, `spawn_units`) | Yes | New squad (new id 21) with the full template size (36 retinue, 32 militia), commanded 1, after 2 game days gap. Experience can be written back (`set_squad_experience`, 5 read back). |
| Transfer to another pawn and back | Not tested | `PawnCPP:SetOwner`, `getSquadOwner` exist; no setter for the side of a unit was found earlier. Not needed: remove + respawn is equal. |

Verdict squads: loan = `addRemoveSquadRequest` now, and `spawnArmy` of the same template after N days (write down template, count and mean experience; set experience on the new men). The new squad is "equal", not "the same units": names, individual gear, per-man experience and the squad id are not kept. Hide is not a loan: the squad stays under control.

Lose fallback: `addRemoveSquadRequest` is the cleanest (no bodies). `just_die` leaves bodies to hide. Both safe in these runs. What is lost: the men, their experience. Nothing else was seen to change (silver, stock not read).

## Villagers
- Hide on 6 members of 2 families: hidden 6 of 6, but the people keep walking (`realPos` changes over 2 game days) and so keep working and eating. Hide is cosmetic. Show restores. No crash.
- No reflected call takes villagers out of the simulation. `just_die` (`ManorCore.remove_families`) removes them with bodies. `settleRegion` adds families with extras (camp, ox, supplies; accepted 2026-11-04). Immigration also refills about every 3 game days.
- Verdict: no real loan for peasants. Use the lose path (remove, re-add with `settleRegion` or let immigration refill).

## Save and load (reasoning, no save call)
- Hide and actor moves are run time flags on objects. After a load the objects are new: hidden men would show again. Loan must not rely on them.
- A removed squad is absent in the next save. The mod must keep the loan record (template, count, mean experience, return day) with the ModState pattern, and call `spawnArmy` at the return day, also after a load. Spawning after a load worked in earlier spikes (rebel squad).

## Not verified
- A real rallied retinue or militia squad (named nobles, gear, recruitment pool): `addRemoveSquadRequest` on it, and refunds or recruit slots. Only spawned squads were tested.
- Removal of a militia squad made of villagers (does the family record stay).
- Transfer to another pawn.
- Save and load of the loan record (reasoning only).
