## 1. Static search
- [x] 1.1 Search extracted data and jmap/usmap for unemployment and manor order factors. Written to `notes/factor-location.md` (question 1).

## 2. Pak test
- [ ] 2.1 Build a pak that adds a negative factor row or effect. Run with `--pak`; read order values and the tooltip. Write `notes/pak-factor.md` (questions 2 and 4).

## 3. Run-time toggle test
- [ ] 3.1 Switch the factor on and off from the mod at run time. Write `notes/runtime-toggle.md` (question 3). (partly done: see `notes/game-tests.md`; index 17 write blocked, memory append works) More: `notes/game-tests-2.md` (control run: appended entries have no effect on publicOrder; config route works for weights but index 17 did not change order).
- [ ] 3.2 Check save/load persistence with `save_game`, after a fresh backup and with the owner informed. Write `notes/persistence.md` (question 5).

## 4. Close
- [ ] 4.1 Write `notes/recommendation.md` with a follow-up change, and ask the owner.
- [ ] 4.2 Move lasting engine facts to the wiki and add a `CHANGELOG.md` line if a tool changed.

## 5. Route A (owner decision 2026-10-23)
- [x] 5.1 Tick-write test of route A: flicker rate and effect against a control run. Written to `notes/tick-write.md` (verdict: A partly works). Evidence in `evidence/`.
- [ ] 5.2 Route B (overlay on the top bar) is the backup. Do not build it now; only record it (done in `notes/tick-write.md`).
