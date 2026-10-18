# M09: refugees

Feature folder: `refugees`. Batch 4. Built new. `mod/RefugeeWaves` (spec 15) is only a reference.

## Goal
A lost vassal sends refugees to the home region. The player must house and feed them, or they become bandits.

## Player rules (from M00)
- A wave size is 30% to 60% of the lost vassal's population.
- Refugees lower approval while they stay.
- Refugees eat food from the home stores.
- The player must house them. Housed refugees become villagers (workers and mouths).
- Refugees with no home after 1 to 2 game months become bandits (through M04).
- Refugees wait in the game's homeless tent (building type 87).

## Current state
Iteration 01 is done: `refugees_vassal_lost` sends a wave (5 family steps) through settleRegion to the home tent camp. Iteration 02 (housing and timeout) is next.

## Proven building blocks
- Refugees lower approval (71 to 59 in 5 days): `docs/harness/15-bandit-settlement/implementation-notes/homeless-refugees.md`.
- Refugees eat food (not measured per family): same note.
- Lua can house refugees (5 to 0 homeless in 12 days): `docs/harness/15-bandit-settlement/implementation-notes/refugee-cycle.md`, `refugee-followups.md`.
- Lost-vassal refugees through `settleRegion` (5 families per call): `immigration-surge.md`, `refugee-waves-mod.md` in the same folder.
- Homeless tent: `docs/harness/13-mod-inspection/implementation-notes/ml-homeless-tent.md`, `docs/harness/15-bandit-settlement/implementation-notes/tent-slot-limit.md`.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-bandits-refugees.md`.
- Mod state: M01.

## Tunables (M00)
- Wave share: 30% to 60% of vassal population.
- Time until a refugee with no home becomes a bandit: 1 to 2 game months.
- Approval penalty per refugee (to measure).

## Dependencies
- M07 (a vassal is lost), M04 (refugees turn into bandits).

## Open questions
1. How does a wave of N families arrive, if each call gives 5 families? Repeat calls over days?
2. Does the tent slot limit cap the wave size?
3. Does the player see an alert for the wave? M00 does not say.
4. Does the game count refugees as villagers in the food model, or does the mod charge food?
5. What does the loss of a vassal region do to its people who are not refugees (killed, or taken)?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | refugee-wave | A lost vassal sends a wave sized by its population. | done, PASS (#200) |
| 02 | housing-and-timeout | Housed refugees become villagers. Unhoused ones turn into bandits after the timer. | not started |
