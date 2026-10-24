## 1. Timers
- [x] 1.1 Move `UEBridge`, `HarnessBoot`, `HarnessReload` loops to `HarnessLoop`.

## 2. Input thread
- [x] 2.1 Hand key bind work to the game thread (menu, raid widget, tech tree widget, Esc).

## 3. Scans
- [x] 3.1 Defer the unit scan after a raid spawn (raid_behavior). Add `IsValid` checks in the other scan loops.

## 4. Fake game kit
- [x] 4.1 Add `LoopInGameThreadWithDelay` and `CancelDelayedAction`, with tests.

## 5. Measure
- [ ] 5.1 Suites: 10 runs each of `invasion-first-raid` and `invasion-great-raid-waves`. Write `notes/suite-results.md`.

## 6. Close
- [ ] 6.1 Tests, validate, CHANGELOG, wiki, archive.
