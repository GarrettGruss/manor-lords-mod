# Design: Remove vassal loyalty

## Context
- Loyalty drives four things today: the tribute share (0.10 to 0.30), the policy change at each season (+3, 0, -5), the gift order, and the submission and return of a vassal. A raid result and the law Trade Pacts also change it.
- The owner decided that a vassal survives or dies and that tribute does not matter for AI regions (2026-10-20, item 10). Lua still simulates the tribute for the player.

## Decisions
- The tribute share is a fixed value (`tribute.share`, default 0.20). At loyalty 50 the old share was 0.20, so the tribute of a vassal with 5 families stays 20 goods (policy `fair`).
- The policies `light`, `fair` and `heavy` stay and only scale the tribute (0.5, 1.0, 1.5). They are gated by the tech tree as before.
- The submission feature is removed completely. A submitted vassal no longer exists as a state.
- Trade Pacts keeps its effect `tribute_share` +0.25, so no law is left empty. The effect kind `vassal_loyalty` is removed from the tree loader. A tree file with an unknown effect kind fails to load, as before.
- The text in `design/mod/` is the owner's. This change does not edit it.

## Open questions
| # | Question | Who decides | How it is answered |
|---|---|---|---|
| 1 | The gift order has loyalty as its only effect. Drop it, or replace it by another effect (for example a one-time tribute bonus)? This design drops it. | Owner | Task 1.2, on the spec pull request |
| 2 | Trade Pacts now has one effect (+25 percent tribute). Is that enough, or should the law get a new effect or be dropped? | Owner | Task 1.2 |
| 3 | `design/mod/invasion-mod.md` and `design/mod/decisions.md` mention loyalty. Does the owner update them? | Owner | Task 1.2 |
| 4 | Old saves hold `loyalty` and `submitted` in the registry. Does the mod ignore them without a crash, and does a vassal that was submitted come back as a normal vassal? | A spike | Task 1.1 |
