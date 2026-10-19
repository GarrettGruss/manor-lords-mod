# Proposal: add boot timing regression tests

Issue: #295. No legacy folder (the boot work came from legacy spec 02, read-only).

## Why

The reliability report of 2026-10-18 marks `harness/game-boot` over the limit: change failure rate 0.57 (n=7). Five of six boot fixes were timing problems that only the real game showed (the clock restarts after a pause, the cinematic undoes a pause, the slot appears late). The rule `process/reliability-assessment` asks for a regression test as the next change in this domain.

The fake game kit already tests these paths (`harness/tests/boot_state_machine.py`, modes `cinematic`, `cinematicstuck`, `slotlate`, `silentrestart`). But the living spec does not name them, and no real-game test scenario checks boot timing over several runs.

## What Changes

- The living spec `harness/game-boot` names the fake tests that already exist for the intro cinematic and for a late slot.
- A new real-game test scenario `boot-timing` checks, after READY:
  - the clock stays still for a longer time than the boot hold
  - `boot.json` walks the fixed states in order
  - boot time and pause calls are in ranges taken from 413 past runs
- A new suite `boot-timing` runs it 5 times. It gives a pass rate.
- No change to `HarnessBoot` behavior.

## Non-goals

- New boot features or changed timeouts.
- The fresh-start (new game) path in the real game. It has its own test scenarios.
- Making boot faster.

## Reliability risk

- `harness/game-boot`: change failure rate 0.57 (n=7), flaky rate not measured (no test scenario maps to this domain yet).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `harness/game-boot`: new spec scenarios for the cinematic and the late slot, and a requirement that boot timing is checked in the real game.

## Impact

- New: `harness/scenarios/boot_timing.py`, `harness/suites/boot-timing.json`.
- `.claude/skills/reliability-assessment/reliability.json`: map `boot_timing.py` to `harness/game-boot`, so its runs count for this domain.
- `harness/tests/test_fakegame_kit.py` or a scenario test, if the new scenario needs a fake test.
- `CHANGELOG.md`.
