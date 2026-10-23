## 1. Static search
- [x] 1.1 Search extracted data and jmap/usmap for unemployment and manor order factors. Written to `notes/factor-location.md` (question 1).

## 2. Pak test
- [x] 2.1 Closed without a pak factor build: a new factor row is not possible (enum and weights are native and config, `notes/factor-location.md`). The config weight pak was tested and had no effect (`notes/game-tests-2.md`). The tooltip picture was not taken (needs a mouse).

## 3. Run-time toggle test
- [x] 3.1 Run-time toggle tested: index 17 write blocked, memory append has no effect (`notes/game-tests.md`, `notes/game-tests-2.md`), per-tick `publicOrder` write holds (`notes/tick-write.md`). Tooltip picture not taken: needs a mouse device.
- [ ] 3.2 Save/load persistence with `save_game`: not done. Not needed after the owner decision: the mod keeps `mod_order` in its own state, and a save check belongs to the later change.

## 4. Close
- [x] 4.1 The recommendation is in `notes/tick-write.md` (verdict) and the owner decision (2026-10-23) in the proposal and design: route A.
- [x] 4.2 Lasting engine facts moved to `docs/wiki/concepts/engine-limits.md`; `CHANGELOG.md` line added.

## 5. Route A (owner decision 2026-10-23)
- [x] 5.1 Tick-write test of route A: flicker rate and effect against a control run. Written to `notes/tick-write.md` (verdict: A partly works). Evidence in `evidence/`.
- [x] 5.2 Route B (overlay on the top bar) is recorded in `notes/tick-write.md`. Not built: not needed now (owner decision).
