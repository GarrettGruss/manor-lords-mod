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
Iteration 01 (low-order-bandits) is done: the Public Order debuff and the conversion through `homeless_rebel` work in the real game. Iteration 02 (season-tick) is done: the roll runs once per region at each season change, and the last season is saved in ModState. See `iterations/`. Iteration 03 is not started.

## Proven building blocks
- `homeless_rebel` removes families and bandits appear: `openspec/changes/archive/2026-10-15-legacy-15-bandit-settlement/implementation-notes/homeless-rebellion.md`, `bandit-settlement.md`.
- Coin buy-back through the negotiation letter, with conditions (hand-set "attacking" tag, free home slots, no price check by the game): `homeless-rebellion.md` part 4.
- The player fights bandits with normal squads: `openspec/changes/archive/2026-10-15-legacy-10-invasion-testability/implementation-notes/spike-C1.md`.
- `Region.publicOrder` reads and writes: `openspec/changes/archive/2026-10-15-legacy-07-feature-test-kit/implementation-notes/actions-catalog.md`, `openspec/changes/archive/2026-10-15-legacy-04-telemetry-and-assertions`. (`regionalWealth` also reads and writes: `openspec/changes/archive/2026-10-15-legacy-m00-invasion-mod/implementation-notes/feasibility-bandits-refugees.md`.)
- Approval reads fine and the game recalculates it every 1 to 3 days (same review). Whether approval still triggers bandits is open question 4.
- Event messages and HUD: `openspec/changes/archive/2026-10-15-legacy-02-save-autoload/implementation-notes/in-game-messages-and-hud.md`.
- Mod state: M01. Combat levers for bandits: M05.

## Tunables (M00)
- Public Order thresholds (75%, 50%, 25%) and chances (10%, 25%, 50%) per season tick.
- Buy-back price.
- Carry cap (M03).

## Dependencies
- M01 mod-state. M03 (bandit plunder behavior). M05 (armor makes militia beat bandits).
- Feeds M09 (refugees with no home) and M12 (path effects).

## Open questions
1. Answered (iteration 03, TBD): 10 silver per family times a multiplier (Iron Hand 1.25, Amnesty 0.5). Open: why the letter gives no family in about 1 of 5 tries.
2. Which 30-day homeless timer does the game use? (Spike 8 in `feasibility-summary.md`: open.)
3. Where do the bandits camp, and how long do they stay before a raid? M00 gives no rule.
4. Is the chance per family or per region, per tick? M00 and the decision do not say. Also: does the old approval cause stay beside Public Order?
5. Do captured bandits (oppression path) need a new mechanic? Decide with M12.
6. What does the player see when families turn? A banner, or nothing? M00 does not say.

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | low-order-bandits | Low Public Order turns families into bandits through `homeless_rebel`. | pass (see iteration file) |
| 02 | season-tick | Seasonal tick with the 75, 50 and 25 percent thresholds. | pass (see iteration file) |
| 03 | coin-buy-back | Pay coin to bring bandits back. | pass (see iteration file) |

## Follow-up decisions (2026-10-16)
See M00 "User decisions", items 11 to 15. They override the open questions above where they answer them.
- The chance is rolled once per region at each season tick.
- Low approval lowers Public Order (a debuff). It does not convert villagers by itself. Debuff size per approval step: open tunable.
- Public Order debuff = (100 - approval) x difficulty. Approval 65 gives Public Order 65 at difficulty 1.

## Values (M00 decisions 28 to 30, 2026-10-17)
- Bandit raid size uses the same random class weights as M02 (small 50%, medium 35%, large 15%). TBD, tuned in playtests.
- Scaled values round up.
