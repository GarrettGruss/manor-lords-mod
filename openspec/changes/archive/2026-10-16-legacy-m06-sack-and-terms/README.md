# M06: sack-and-terms

Feature folder: `sack_and_terms`. Batch 3.

## Goal
A lost battle sacks the town instead of deleting the game. The invader offers tribute terms. A fortified vassal can become the fallback capital.

## Player rules (from M00)
- Losing the main battle triggers a sack. The town loses a share of buildings, stockpiles and people (20% to 50%). The game continues.
- Repeated sacks inside a short window can still end the game.
- Tribute terms: the invader offers a one-time payment, or vassalage with yearly tribute. Hostages are dropped (decision 8).
- Sack uses the native sack and loot mechanics (decision 8). Sack size is proportional to the difficulty (integer 1 to 3), on top of the raid size (M02).
- Great raid end (decision 1): the player survives waves until the relief army arrives, then fights a very large battle with the liege's reinforcements under the player's control. M02 runs the waves. M06 defines what a lost battle is and what the sack does.
- Fallback capital: before or during a battle, pay to move families, grain and the best units to a fortified vassal. It becomes the fallback capital.
- Later layers (deferred, no spec): the manor holds while the town falls; occupation; liberation.
- Vassals expect protection. A vassal that is not protected may submit to the invader (M07).

## Current state
Iterations 01 and 02 done (2026-10-18). Terms notes: `implementation-notes/iteration-02-terms.md`. Iteration 01: a lost battle sacks the town. Notes: `implementation-notes/iteration-01-sack.md`. The first part (sack and terms in the home town) does not need vassals. The fallback capital waits for M07.

## Proven building blocks
- Sack by share of buildings, stock and families (`HarnessSack`): `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S6.md` (50% buildings, 49.4% stock, 40% families).
- The game ends when the village has population 0: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-S8.md`. The sack must keep people alive.
- Burn to ruins and partial rebuild cost: `spike-S6.md`, `spike-R8.md`.
- The player ends a raid with a letter and pays 20 silver: `openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/implementation-notes/homeless-rebellion.md` part 4.
- Silver payments by game calls: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-P5.md`. The game does not check the cost.
- Settled second region grows: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/dynamic-lords.md`.
- Owner change of a region: `baron-model.md` in the same folder.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-raids.md`.
- Mod state: M01.

## Tunables (M00)
- Sack share: 20% to 50% of buildings, stockpiles and population.
- Window for repeated sacks (M00 gives no number).
- Terms: payment amount, yearly tribute share.
- Sack share per difficulty step (difficulty 1 to 3). M00 gives 20% to 50% as the range.

## Dependencies
- M01, M02 (great raid result, ransom demand).
- M07 for the fallback capital. M08 for the yearly tribute term.

## Open questions
1. How large must a sack be to feel fair? (M00 open question 11.) The user decides by play.
2. What counts as a "lost battle"? There is no captain. M00 gives no rule.
3. Answered (decision 8): hostages are dropped. Terms are a payment or vassalage.
4. What is the window and the count of sacks that ends the game?
5. How do families, goods and units move to the fallback capital? Only toy results exist (`InvasionStandIn`).
6. What does the player pick: terms before or after the sack?
7. Answered (decision 1): survive waves until the relief army arrives, then the very large battle. Open: what happens if the player loses that battle (a sack at difficulty size, or the end of the game)?
8. Does the sack size scale linearly with the difficulty, for example 20% at 1 and 50% at 3?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | sack-after-defeat | A lost battle runs `HarnessSack` rules and the game continues. | done, see the iteration file |
| 02 | tribute-terms | One-time payment and yearly tribute terms. | done, see the iteration file |
| 03 | fallback-capital | Move to a fortified vassal (needs M07). | done, PASS (#205) |
| 04 | sack-target | The sack hits the region under attack or the home region, not the first player region. | done (#224) |

## Follow-up decisions (2026-10-16)
See M00 "User decisions", items 11 to 15. They override the open questions above where they answer them.
- Sack size grows linearly with difficulty for now. Logarithmic is possible later; decided in playtests.

## TBD values (M00 decisions 27 to 30, 2026-10-17)
- Loss of the great raid's final battle: TBD. Leave open. M06 has no rule for it for now. This answers open question 7 as "TBD".
- Scaled counts and shares round up. The relief army at difficulty 2 is 8 squads.
