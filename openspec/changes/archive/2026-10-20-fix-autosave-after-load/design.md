## Context

`HarnessAutosave.disable(period_s)` calls `SetAutosavePeriodOnPawn` on the game instance. The pawn owns the timer (`autosaveHandle`). A load makes a new pawn and a new timer of `Settings.autosavePeriod` (600 s).

## Decisions

- **Trigger:** react to the new player pawn after a load (`NotifyOnNewObject` on the pawn class, or the `ReceiveBeginPlay` hook that HarnessBoot already uses for the world). Spike task 1.1 picks the hook that fires once per load and after the timer exists. Reason: a push before the pawn starts its own timer is undone.
- **Retry:** if `is_disabled` is false after the push, retry a few times with a short delay, then log an error. Reason: the timer may start a moment after the pawn begins play.
- **Scope:** only after `READY` was reached once in the session. Before that, the boot state machine owns the timer.

## Risks

- A hook that fires for each pawn in the world (AI lords) would call the push many times. The push is cheap and idempotent, but the hook filters to the player pawn.
