## 1. Timers
- [ ] 1.1 Move `UEBridge`, `HarnessBoot`, `HarnessReload` loops to `HarnessLoop`.

## 2. Input thread
- [ ] 2.1 Hand key bind work to the game thread (menu, raid widget, tech tree widget, Esc).

## 3. Scans
- [ ] 3.1 Defer the wave spawn unit scan. Add `IsValid` checks in the other scan loops.

## 4. Fake game kit
- [ ] 4.1 Add `LoopInGameThreadWithDelay` and `CancelDelayedAction`, with tests.

## 5. Measure
- [ ] 5.1 Suites: 10 runs each of `invasion-first-raid` and `invasion-great-raid-waves`. Write `notes/suite-results.md`.

## 6. Close
- [ ] 6.1 Tests, validate, CHANGELOG, wiki, archive.
