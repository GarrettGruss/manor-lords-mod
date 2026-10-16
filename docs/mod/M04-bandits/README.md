# M04: bandits

Feature folder: `bandits`. Batch 2.

## Goal
Villagers turn into bandits when approval is low or regional wealth is low. The player fights the bandits or pays coin to bring them back.

## Player rules (from M00)
- Villagers become bandits for three reasons: low approval, low regional wealth, and refugees with no home (the last reason belongs to M09).
- Low approval: below a threshold (example 30%), 1 to 3 families per month turn into bandits.
- Low regional wealth: below a threshold (to be tuned), 1 to 2 families per month turn into bandits, even when approval is fine.
- The change uses the `homeless_rebel` route: the mod removes the families and bandits appear at their homes. No `turnToBandit`. No `Region:AddNewFamily`.
- Bandits raid the home region and the vassals, like small local raids (plunder type, carry cap about 5 grain: see M03).
- The player can fight them, or pay coin to bring them back to the village.
- Oppression path: bandits are cheaper to fight, captured bandits become forced labor. Prosperity path: bandits are cheaper to bring back, returned bandits work at once (paths belong to M12).

## Current state
Not started.

## Proven building blocks
- `homeless_rebel` removes families and bandits appear: `docs/harness/15-bandit-settlement/implementation-notes/homeless-rebellion.md`, `bandit-settlement.md`.
- Coin buy-back through the negotiation letter, with conditions (hand-set "attacking" tag, free home slots, no price check by the game): `homeless-rebellion.md` part 4.
- The player fights bandits with normal squads: `docs/harness/10-invasion-testability/implementation-notes/spike-C1.md`.
- `regionalWealth` reads, writes and holds: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-bandits-refugees.md`.
- Approval reads fine. The game recalculates it every 1 to 3 days: same review.
- Event messages and HUD: `docs/harness/02-save-autoload/implementation-notes/in-game-messages-and-hud.md`.
- Mod state: M01. Combat levers for bandits: M05.

## Tunables (M00)
- Approval threshold (example 30%) and rate (1 to 3 families per month).
- Regional wealth threshold (to tune) and rate (1 to 2 families per month).
- Buy-back price.
- Carry cap (M03).

## Dependencies
- M01 mod-state. M03 (bandit plunder behavior). M05 (armor makes militia beat bandits).
- Feeds M09 (refugees with no home) and M12 (path effects).

## Open questions
1. What is the buy-back price? The game does not check it, so the mod must set it. M00 gives no number.
2. Which 30-day homeless timer and approval threshold does the game use? (Spike 8 in `feasibility-summary.md`: open.)
3. Where do the bandits camp, and how long do they stay before a raid? M00 gives no rule.
4. Is the wealth threshold absolute or relative to population?
5. Do captured bandits (oppression path) need a new mechanic? Decide with M12.
6. What does the player see when families turn? A banner, or nothing? M00 does not say.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | low-approval-bandits | Low approval turns families into bandits through `homeless_rebel`. | not started |
| 02 | low-wealth-bandits | Same rule for low regional wealth. | not started |
| 03 | coin-buy-back | Pay coin to bring bandits back. | not started |
