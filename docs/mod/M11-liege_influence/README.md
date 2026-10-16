# M11: liege-influence (backlog, TBD)

Feature folder: `liege_influence`. Status: backlog, TBD (decision 9). Not in the batch order.

Decision 9 (2026-10-16): the liege is an off-screen concept. For now only a custom menu represents the liege. Nothing in this spec is planned. Keep the text for later.

## Goal
Tribute to the liege gives influence. Influence buys aid, villagers, weapons or tools.

## Player rules (from M00)
- The player is sworn to a local city power (the liege).
- Influence is the resource of the liege relation. It is a mod-owned value.
- Gain influence: send tribute to the liege.
- Spend influence: call for military aid, or request villagers, weapons or tools.
- One liege aid call costs about 1 to 2 years of normal tribute in influence.
- Path effect: oppression gives influence from military success. Prosperity gives influence from tribute and wealth (M12).

## Current state
Not started.

## Proven building blocks
- Mod state: M01 (`docs/harness/24-mod-save-state/README.md`).
- Silver, wealth and influence payouts by game calls: `docs/harness/10-invasion-testability/implementation-notes/spike-P5.md`.
- Mercenary hire: `spike-P5.md`. Spawn of an army with an owner: `docs/harness/10-invasion-testability/implementation-notes/spike-S7.md`.
- Review of the liege rules: `docs/mod/M00-invasion-mod/implementation-notes/feasibility-vassals.md`.
- Mod menu examples: `docs/harness/13-mod-inspection/implementation-notes/ml-mod-menu.md`.

## Tunables (M00)
- Influence per unit of tribute.
- Aid call cost: about 1 to 2 years of normal tribute.
- Price list for villagers, weapons and tools (M00 gives none).

## Dependencies
- M08 tribute, M01 mod-state. M12 for path effects.

## Open questions
1. Answered (decision 9): the liege is off-screen. Only a custom menu represents it. All other rules stay TBD.
6. The relief army of the great raid (decision 1) comes from the liege. Does M11 own the relief army, or does M02? Until M11 starts, M02 owns it.
2. How does the player send tribute to the liege and spend influence: a menu from a pak widget, or a named command?
3. What does a military aid call bring: a spawned army, and under whose control?
4. Which goods and how many villagers can be requested?
5. Does influence decay or have a cap?

## Iterations
| # | Name | Goal | Result |
| --- | --- | --- | --- |
| 01 | influence-balance | Tribute to the liege adds influence. | not started |
| 02 | spend-influence | Spend influence on villagers, weapons and tools. | not started |
| 03 | military-aid | A liege aid call. | not started |
