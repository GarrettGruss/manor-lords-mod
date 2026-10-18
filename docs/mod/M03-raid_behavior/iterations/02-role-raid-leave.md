# M03 iteration 02: role-raid-leave

Branch: `feat/M03-raid_behavior-02-role-raid-leave`. Issue: #168.

## Goal
A Hussite role raid (M05.02, `spawnArmy` squads) ends like a native raid. It leaves the map after enough loot or enough losses, and after a time limit.
Native raids (`spawnRaiders`) and the M04 bandit raids are not changed (M00 decision 31).

## Problem
`spawnArmy` squads follow the base bandit AI. They do not obey move orders (`docs/harness/15-bandit-settlement/implementation-notes/homeless-rebellion.md`). The native line "enough looted. Leaving map." does not come for them in a reliable way.

## User idea (2026-10-18, primary approach)
1. Spawn the role raid as the army of an AI lord (the baron model) that is at war with the player, not as plain bandit squads. Proven pieces: `lords_state`, `lord_declare_war`, `lord_declare_peace` (spec 10 spike S11), `spawnArmy` with an owner pawn.
2. The mod tracks the raid units in Lua. It checks whether they are inside the battle area (the battle marker, or a radius around the village or the target region).
3. While they are inside, the mod withdraws goods from the player's stores (a plunder tick). The total is managed by the mod. It may scale with raid size and difficulty.
4. When that amount is reached (or a time limit or loss limit is hit), the mod declares peace between the lord and the player. The units then leave the map. If they do not walk off, the mod removes them at the map edge.
The user believes (a) the baron AI is hard-coded not to plunder the player, so the Lua plunder tick is the plunder, and (b) declaring peace forces the army to leave.

## Spike first
Verify in the real game before any feature code:
- S1: does an AI lord army at war (with a challenge on the player region) move to and fight at the village?
- S2: does `declarePeace` make the army walk off the map? How long does it take?
- S3 (brief): does the lord army loot or burn by itself?
Notes go to `../implementation-notes/iteration-02-role-raid-leave.md`. If the lord route is not feasible, fall back to: a mod "leave" that zeroes the loot of each unit and removes the units with `just_die` (proven in `kill_units`), at the map edge when they stand there, or at once.

## Acceptance criteria (ranges; thresholds are in `config.lua`, TBD)
- A1: a role raid reaches the leave state when the loot taken is at least `leave_loot_per_raider` x the raiders at the start. Loot per raider: 3 to 10.
- A2: a role raid reaches the leave state when the share of lost raiders is at least `leave_loss_share` (0.4 to 0.7).
- A3: a role raid reaches the leave state at `max_days` after the spawn (15 to 40 game days), also when no other rule fired.
- A4: after the leave state, no raider of the raid stays on the map within 1 to 3 game days (the mod removes them at once). The loot they carry is counted as carried out, not returned to a store.
- A5: native raids (roles off) and bandit raids are not touched: the leave rules never fire for them.
- A6: the village population after the raid is more than 0. No game crash.

## Plan
- Pure rules in `raid_behavior/rules.lua` (leave decision), tested without the game.
- The leave action in `raid_behavior/init.lua`, on the scheduler (no new `LoopAsync`).
- Scenario `raid-behavior-role-leave` plus the fake tests.

## Result
Partly done (2026-10-18). Code and fake tests are done; the real-game run is open because the harness run cap was reached.
- Spike (notes `../implementation-notes/iteration-02-role-raid-leave.md`): the lord route is not feasible as a carrier (a challenge hands the player region to the lord, run `20261018-015009-371a`; without a challenge the lord army does not attack, run `20261018-015705-ee48`). `declarePeace` removes a lord-owned army within 60 game seconds. Peace with the bandit lord only steers a role raid away (run `20261018-020315-51c8`).
- Mechanism built: loot to 0, then `just_die`; config `raid_behavior.leave` (loot 4 per raider, loss share 0.5, 25 days). 5 new fake tests pass.
- Open: scenario `raid-behavior-role-leave` in the real game (A1 to A6).
