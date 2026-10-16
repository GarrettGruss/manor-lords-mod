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
- Difficulty (decision 8) is an integer from 1 to 3. It scales the raid size. Raid count, subjugation start, raid frequency, spawn side and carry caps per tier stay as first guesses.
- Raiders pick their own targets. The mod does not steer them.
- Win condition (decision 1): during the great raid the player must survive waves of attackers until the relief army arrives. Then a very large battle follows. The liege sends reinforcements under the player's control. This win is a mod rule (goals = Endless).
- Raid size (decision 8): unit count = base size multiplier times difficulty. Small = 1, medium = 2, large = 3. Difficulty is an integer from 1 to 3 for now.
- Hussite raid composition (decision 7): existing units only. Melee: tier I brigands and spearmen, tier II axe and sword infantry, tier III retinue and poleaxe infantry. Ranged: tier I bows, tier II crossbows. No handgunners.
- One custom raid widget (decision 4) shows all raid information: countdown, size estimate and more. It is a pak widget (harness spec 16). The banner stays a fallback.

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
- Row ids: `docs/harness/23-row-id-range/README.md`. Confirmed block (decision 3): building ids 1200 to 1299. Upgrade ids 117 to 999 are shared.

## Tunables (M00 balance targets, first guesses)
- First minor raid: day 30 to day 90.
- Warning time before a raid: 2 to 8 game weeks.
- Great raid countdown: 3 to 5 game years.
- Difficulty (integer 1 to 3) and base size multipliers (small 1, medium 2, large 3). Units = multiplier times difficulty.
- Number of waves of the great raid, and the wave spacing (open).
- Relief army arrival time (open).
- Season weights (spring to autumn high, winter low).

## Dependencies
- M01 mod-state (the schedule and the clock must survive a load).
- Feeds M03 (starts the raid), M06 (great raid result), M07 (vassal targets).
- The relief army of the great raid is owned by M02 for now. M11 (liege influence) is backlog (decision 9).

## Open questions
1. Do writes above 730 days to the raid timer hold? The great raid clock of 3 to 5 years may need a mod-owned clock, with the game timer used only to spawn. Not tried (spike-S1).
2. Answered (decision 4): one custom pak widget shows all raid information. Open: which widget layout, and where it opens.
3. How exact is the estimate: exact squads, or a range?
4. Which AI is reused for subjugation, and does it take only a vassal region? (M00 open question 5.)
5. The game has no captain concept. The great raid ends when the relief army arrives and the very large battle is won or lost (decision 1). The mod must run this end (M06).
6. Answered (decision 1): survive waves until the relief army arrives, then a very large battle. Open: how many waves, how long, and when the relief army arrives. See the new questions 9 to 11.
7. Can `spawnRaiders` take a spawn centre on any map edge, for the spawn side per tier?
8. Answered (decision 2): order is the native Public Order. The countdown does not need it.
9. How is the difficulty (1 to 3) chosen: by the player at start, by the mod over time, or per raid?
10. When does the relief army arrive, and how big is the very large battle? How are the player-controlled reinforcements spawned?
11. How many waves does the great raid have, and how big is each wave?
12. Which raids are small, medium or large? Who decides the base size multiplier?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | first-scheduled-raid | The mod owns the raid timer. One scheduled minor raid with a daily countdown banner and a size estimate. | not started |
| 02 | great-raid-clock | The great raid clock survives a load. Season weights. | not started |
| 03 | subjugation-raid | A subjugation raid on a vassal region (needs M07). | not started |
| 04 | difficulty | Difficulty 1 to 3 and the size multipliers. | not started |
| 05 | raid-widget | One custom pak widget for all raid information (decision 4). | not started |
| 06 | great-raid-waves | Waves of attackers until the relief army arrives, then the very large battle (decision 1). | not started |

## Follow-up decisions (2026-10-16)
See M00 "User decisions", items 11 to 15. They override the open questions above where they answer them.
- Difficulty (1 to 3) is picked by the player at the start.
- Great raid: 1 x difficulty waves, every wave large. A large army is 15 units (soldier or squad: open).
- A large army is 15 squads (playtest value). Normal raid size (small, medium, large) is random for now.
- The final very large battle and the relief army (15 squads, player-controlled) are not scaled by difficulty for now.
