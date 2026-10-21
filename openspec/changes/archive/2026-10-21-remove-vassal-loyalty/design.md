# Design: Remove vassal loyalty

## Context
- Loyalty drives four things today: the tribute share (0.10 to 0.30), the policy change at each season (+3, 0, -5), the gift order, and the submission and return of a vassal. A raid result and the law Trade Pacts also change it.
- The owner decided that a vassal survives or dies and that tribute does not matter for AI regions (2026-10-20, item 10). Lua still simulates the tribute for the player.

## Decisions
- The tribute share is a fixed value (`tribute.share`, default 0.20). At loyalty 50 the old share was 0.20, so the tribute of a vassal with 5 families stays 20 goods (policy `fair`).
- The policies `light`, `fair` and `heavy` stay and only scale the tribute (0.5, 1.0, 1.5). They are gated by the tech tree as before.
- The submission feature is removed completely. A submitted vassal no longer exists as a state.
- Trade Pacts keeps its effect `tribute_share` +0.25, so no law is left empty. The effect kind `vassal_loyalty` is removed from the tree loader. A tree file with an unknown effect kind fails to load, as before.
- The owner chose to remove the loyalty text from `design/mod/invasion-mod.md` and `design/mod/decisions.md` in this change (chat, 2026-10-21). Only loyalty sentences are deleted or rewritten.

## Open questions
All answered by the owner in chat on 2026-10-21.

| # | Question | Answer |
|---|---|---|
| 1 | The gift order has loyalty as its only effect. Drop it, or replace it? | Drop it. |
| 2 | Trade Pacts now has one effect (+25 percent tribute). Enough? | Yes. Trade Pacts keeps only `tribute_share` +0.25. |
| 3 | `design/mod/invasion-mod.md` and `design/mod/decisions.md` mention loyalty. Update them? | Yes, remove the loyalty text, with minimal edits. |
| 4 | Old saves hold `loyalty` and `submitted` in the registry. Ignore without a crash? | Yes. ModState keeps entries with no registered key as unknown entries and does not read them. A fake-game test (`OldSaveTests`) proves it; no real game spike is needed. See `notes/old-save-registry.md`. |
