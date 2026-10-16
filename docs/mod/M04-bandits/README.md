# M04: bandits

Feature folder: `bandits`. Batch 2.

## Goal
Families turn into bandits when Public Order is low (decision 6). The player fights the bandits or pays coin to bring them back.

## Player rules (from M00)
- Villagers become bandits for two reasons: low Public Order, and refugees with no home (the last reason belongs to M09). The M00 cause "low regional wealth" is replaced by Public Order (decision 6). The user can reverse this.
- Public Order is the native value `Region.publicOrder` (decision 2). Approval stays a separate game value.
- Conversion ticks once per season (winter, spring, summer, fall). Public Order below 75%: 10% chance. Below 50%: 25%. Below 25%: 50%. These are starting tunables and will change.
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
- `Region.publicOrder` reads and writes: `docs/harness/07-feature-test-kit/implementation-notes/actions-catalog.md`, `docs/harness/04-telemetry-and-assertions`. (`regionalWealth` also reads and writes: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-bandits-refugees.md`.)
- Approval reads fine and the game recalculates it every 1 to 3 days (same review). Whether approval still triggers bandits is open question 4.
- Event messages and HUD: `docs/harness/02-save-autoload/implementation-notes/in-game-messages-and-hud.md`.
- Mod state: M01. Combat levers for bandits: M05.

## Tunables (M00)
- Public Order thresholds (75%, 50%, 25%) and chances (10%, 25%, 50%) per season tick.
- Buy-back price.
- Carry cap (M03).

## Dependencies
- M01 mod-state. M03 (bandit plunder behavior). M05 (armor makes militia beat bandits).
- Feeds M09 (refugees with no home) and M12 (path effects).

## Open questions
1. What is the buy-back price? The game does not check it, so the mod must set it. M00 gives no number.
2. Which 30-day homeless timer does the game use? (Spike 8 in `feasibility-summary.md`: open.)
3. Where do the bandits camp, and how long do they stay before a raid? M00 gives no rule.
4. Is the chance per family or per region, per tick? M00 and the decision do not say. Also: does the old approval cause stay beside Public Order?
5. Do captured bandits (oppression path) need a new mechanic? Decide with M12.
6. What does the player see when families turn? A banner, or nothing? M00 does not say.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | low-order-bandits | Low Public Order turns families into bandits through `homeless_rebel`. | not started |
| 02 | season-tick | Seasonal tick with the 75, 50 and 25 percent thresholds. | not started |
| 03 | coin-buy-back | Pay coin to bring bandits back. | not started |
