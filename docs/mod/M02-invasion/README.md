# M02: invasion

Feature folder: `invasion`. Batch 1.

## Goal
Schedule the raids. Show a countdown and a size estimate to the player. Run the great raid clock.

## Player rules (from M00)
- Raids come on a telegraphed schedule. The player sees a countdown and a size estimate (pillar 4, "Dread from knowing").
- Two raid types only: plunder (minor) and subjugation (major).
- Early raids hit vassals first. Plunder raids hit the main town during the whole game.
- A countdown runs to the great raid. The great raid is a subjugation raid on the main town. Its goal is to destroy the town. The clock is visible.
- Main raids come from spring to autumn. Winter rides are rare but possible.
- Before a raid, the Hussite captains can demand a ransom. The term belongs to M06 (sack-and-terms).
- Difficulty tiers change the raid count and size, when subjugation starts, how often raids come, the spawn side and the carry caps.
- Raiders pick their own targets. The mod does not steer them.

## Current state
Not started. The stand-ins `RaidStandIn` and `InvasionStandIn` exist but use invented rules. They are not part of the mod.

## Proven building blocks
- Raid timer write and spawn (`TemporalComponent.daysUntilNextRaid`): `docs/harness/10-invasion-testability/implementation-notes/spike-S1.md`. The base game also sets a random timer after each raid (208 and 353 days seen). The mod must own the timer.
- Countdown banner `PawnCPP:playEventMessage`: `docs/harness/10-invasion-testability/implementation-notes/spike-S9.md`. The banner fades. Call it again each game day.
- Raid size in squads of 18 (`spawnRaiders`): `docs/harness/10-invasion-testability/implementation-notes/spike-S2.md`.
- Typed squads with `spawnArmy`: `docs/harness/10-invasion-testability/implementation-notes/spike-S7.md`, `spike-C1.md`.
- Subjugation by an AI lord (`spawnNewAILord`, war, `initChallenge`) took a region: `docs/harness/10-invasion-testability/implementation-notes/baron-model.md`, `dynamic-lords.md`.
- Review of the raid mechanics: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-raids.md`.
- Mod state: M01 (`docs/harness/24-mod-save-state/README.md`).
- Row ids: `docs/harness/23-row-id-range/README.md`. Proposed block: building ids 1200 to 1299 (rule in `feature-breakdown.md`). Upgrade ids 117 to 999 are shared.

## Tunables (M00 balance targets, first guesses)
- First minor raid: day 30 to day 90.
- Warning time before a raid: 2 to 8 game weeks.
- Great raid countdown: 3 to 5 game years.
- Raid size per tier, in squads of 18.
- Season weights (spring to autumn high, winter low).

## Dependencies
- M01 mod-state (the schedule and the clock must survive a load).
- Feeds M03 (starts the raid), M06 (great raid result), M07 (vassal targets).

## Open questions
1. Do writes above 730 days to the raid timer hold? The great raid clock of 3 to 5 years may need a mod-owned clock, with the game timer used only to spawn. Not tried (spike-S1).
2. How is the size estimate shown: a banner line, or a pak widget? M00 gives no UI.
3. How exact is the estimate: exact squads, or a range?
4. Which AI is reused for subjugation, and does it take only a vassal region? (M00 open question 5.)
5. The game has no captain concept. What ends the great raid? The goal "destroy the main town" must come from the mod (M06).
6. Win condition (M00 open question 6): what does the player reach after the great raid? It blocks the final shape of the great raid.
7. Can `spawnRaiders` take a spawn centre on any map edge, for the spawn side per tier?
8. How is "order" measured and shown? (M00 open question 7.) The countdown does not need it.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | first-scheduled-raid | The mod owns the raid timer. One scheduled minor raid with a daily countdown banner and a size estimate. | not started |
| 02 | great-raid-clock | The great raid clock survives a load. Season weights. | not started |
| 03 | subjugation-raid | A subjugation raid on a vassal region (needs M07). | not started |
| 04 | tiers | Difficulty tiers. | not started |
