# M08: tribute

Feature folder: `tribute`. Batch 4.

## Goal
Vassals send supplies to the home region. They expect protection. Failed protection lowers loyalty.

## Player rules (from M00)
- A vassal sends tribute worth 10% to 30% of its production.
- Vassals are the permanent source of iron, salt and other finite goods (M10).
- Vassals expect protection from the empire and from bandits. A vassal the player failed to protect loses loyalty.
- More vassals give more tribute but split the player's forces.
- A neglected vassal may pay tribute to the invader.
- Tribute to the liege gives influence (M11, backlog and TBD: decision 9).
- Vassal policies and the path change the tribute rate (M12).

## Current state
Not started.

## Proven building blocks
- Silver, wealth and influence payouts by game calls: `docs/harness/10-invasion-testability/implementation-notes/spike-P5.md`.
- `GiveItemByID` adds goods to a store with space: `docs/harness/10-invasion-testability/implementation-notes/spike-S6.md`.
- Review of vassal tribute (goods transfer between regions is unknown): `docs/mod/M00-invasion-mod/implementation-notes/feasibility-vassals.md`.
- Production read under another owner is not tested: `docs/harness/10-invasion-testability/implementation-notes/dynamic-lords.md`.
- Mod state with region Tags: M01.

## Tunables (M00)
- Tribute share of vassal production: 10% to 30%.
- Loyalty loss for a failed defense.
- Tribute period (game month or season; M00 gives none).

## Dependencies
- M07 vassals, M02 invasion (raids on vassals).
- Feeds M10, M11.

## Open questions
1. Can Lua read the production of a vassal region? If not, tribute must be a mod rule (a formula on population).
2. Can goods move between regions? If not, tribute pays as silver, wealth or goods created at the home region.
3. How is loyalty lost: by each raid, by each loss, or by time without help?
4. What does the player see when tribute arrives?
5. What happens when a vassal's loyalty is zero? (M00: it may submit to the invader.)

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | tribute-payout | A vassal pays a share of its production each period. | not started |
| 02 | protection-and-loyalty | Failed protection lowers loyalty and tribute. | not started |
