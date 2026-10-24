# Design: Spike Lua crash after spawn

## Questions
1. Do the crashes share a signature (address, frame)?
2. Which Lua sites touch UObjects off the game thread, share Lua state across threads, or keep stale UObject references?
3. Does an immediate unit scan after a great wave spawn change the crash rate?
4. Does wrapping risky `LoopAsync` sites in `ExecuteInGameThread` change the crash rate in a long fast-forward?
5. Is low free memory involved?

## Method
Crash table from the run folders, then a static code audit, then A/B runs with a small sample. Crashes are data. The simulation is not deterministic, so results are counts, not proofs.

## Decision rule
Implement a fix only if it is low risk and local. Otherwise list it for a follow-up change.
