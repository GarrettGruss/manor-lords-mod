# M06: sack-and-terms

Feature folder: `sack_and_terms`. Batch 3.

## Goal
A lost battle sacks the town instead of deleting the game. The invader offers tribute terms. A fortified vassal can become the fallback capital.

## Player rules (from M00)
- Losing the main battle triggers a sack. The town loses a share of buildings, stockpiles and people (20% to 50%). The game continues.
- Repeated sacks inside a short window can still end the game.
- Tribute terms: the invader offers a one-time payment, hostages, or vassalage with yearly tribute.
- Fallback capital: before or during a battle, pay to move families, grain and the best units to a fortified vassal. It becomes the fallback capital.
- Later layers (deferred, no spec): the manor holds while the town falls; occupation; liberation.
- Vassals expect protection. A vassal that is not protected may submit to the invader (M07).

## Current state
Not started. The first part (sack and terms in the home town) does not need vassals. The fallback capital waits for M07.

## Proven building blocks
- Sack by share of buildings, stock and families (`HarnessSack`): `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md` (50% buildings, 49.4% stock, 40% families).
- The game ends when the village has population 0: `docs/harness/10-invasion-testability/implementation-notes/spike-S8.md`. The sack must keep people alive.
- Burn to ruins and partial rebuild cost: `spike-S6.md`, `spike-R8.md`.
- The player ends a raid with a letter and pays 20 silver: `docs/harness/15-bandit-settlement/implementation-notes/homeless-rebellion.md` part 4.
- Silver payments by game calls: `docs/harness/10-invasion-testability/implementation-notes/spike-P5.md`. The game does not check the cost.
- Settled second region grows: `docs/harness/10-invasion-testability/implementation-notes/dynamic-lords.md`.
- Owner change of a region: `baron-model.md` in the same folder.
- Review: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-raids.md`.
- Mod state: M01.

## Tunables (M00)
- Sack share: 20% to 50% of buildings, stockpiles and population.
- Window for repeated sacks (M00 gives no number).
- Terms: payment amount, hostage count, yearly tribute share.

## Dependencies
- M01, M02 (great raid result, ransom demand).
- M07 for the fallback capital. M08 for the yearly tribute term.

## Open questions
1. How large must a sack be to feel fair? (M00 open question 11.) The user decides by play.
2. What counts as a "lost battle"? There is no captain. M00 gives no rule.
3. What are hostages in a game without captives? M00 removes captive raids. Does a hostage term make sense?
4. What is the window and the count of sacks that ends the game?
5. How do families, goods and units move to the fallback capital? Only toy results exist (`InvasionStandIn`).
6. What does the player pick: terms before or after the sack?
7. Win condition and the end of the great raid (M00 open question 6).

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | sack-after-defeat | A lost battle runs `HarnessSack` rules and the game continues. | not started |
| 02 | tribute-terms | One-time payment and yearly tribute terms. | not started |
| 03 | fallback-capital | Move to a fortified vassal (needs M07). | not started |
