# M03 iteration 02: role-raid-leave

Branch: `feat/M03-raid_behavior-02-role-raid-leave`. Issue: #168.

## Goal
A Hussite role raid (M05.02, `spawnArmy` squads) ends like a native raid. It leaves the map after enough loot or enough losses, and after a time limit.
Native raids (`spawnRaiders`) and the M04 bandit raids are not changed (M00 decision 31).

## Design (user decision 2026-10-18, replaces the silent-removal design)
1. A Hussite role raid is the army of an AI lord ("Hussite Raiders") at war with the player (`features/invasion/lord_raid.lua`; `spawnArmy` with the lord as owner, `HarnessLords`).
2. The challenge battlefield is moved to the player manor with `HarnessBattlefield.battlefield_anchor` (issue #99): the army marches to the manor and stands there.
3. Plunder is a mod tick: once a game day, goods leave the village stores for each raider that stands within `plunder.battle_radius` of the manor (`raid_behavior`).
4. The raid leaves when the loot goal (`leave.loot_per_raider` for each raider), the loss share or the time limit is reached. The mod declares peace; the game removes the lord army.
5. If a challenge is won, the region goes back to the player at once (guard in `raid_behavior`).
6. Fallback (when the lord raid cannot start, or `lord_army.enabled = false`): bandit squads. They leave as follows (user decision): peace with the bandit lord makes them walk away, and the mod removes a unit only in a quiet spot, at least `leave.quiet_distance` from the player pawn or at the map edge, never in view. The loot leaves with the unit.

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
- A4: after the leave state, no raider of the raid stays on the map within 1 to 3 game days (peace removes a lord army; the fallback removes units in a quiet spot). The loot they carry is counted as carried out, not returned to a store.
- A5: native raids (roles off) and bandit raids are not touched: the leave rules never fire for them.
- A6: the village population after the raid is more than 0. No game crash.
- A7: the player still owns a region after the raid, and a lord raid took goods from the stores (plundered more than 0).

## Plan
- Pure rules in `raid_behavior/rules.lua` (leave decision), tested without the game.
- The leave action in `raid_behavior/init.lua`, on the scheduler (no new `LoopAsync`).
- Scenario `raid-behavior-role-leave` plus the fake tests.

## Result
Result: PASS in the real game (2026-10-18). Notes: `../implementation-notes/iteration-02-role-raid-leave.md`.
- Scenario `raid-behavior-role-leave`: difficulty 1 `20261018-040610-b669` pass (lord raid, 32 raiders, plundered 128 = 4 per raider over days 208 to 212, peace on day 212, raid ended day 214, region kept); difficulty 2 `20261018-040850-367c` pass.
- Anchor spike `probe-lord-raid-anchor` `20261018-035856-248b`: the army stood within 1300 units of the manor for 14 game minutes; the challenge stayed open, no region transfer in that time.
- Earlier fallback design in the real game (bandit squads, quiet-spot removal): run `20261018-035536-1237` (leave on day 213 by losses, units removed day 214, war restored). The run ended as harness_error only because of a string metric (fixed).
- Regression: `invasion-raid-composition` difficulty 1 `20261018-041117-2d31`, difficulty 3 `20261018-041304-1c3e` pass (a boot crash `20261018-041200-e3d8` before the retry).
- Not verified: the guard that gives a won region back (no run lost the region); loss and time reasons for a lord raid; a lord raid on a save with several raids in one session.
