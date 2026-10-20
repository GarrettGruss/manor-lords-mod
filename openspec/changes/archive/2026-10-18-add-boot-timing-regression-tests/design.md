# Design: add boot timing regression tests

## Context

- Boot code: `mod/HarnessBoot/Scripts/main.lua`. Constants: `CLOCK_STOPPED_SECONDS = 8`, `CINEMATIC_WAIT_S = 25`, `PAUSE_RETRY_S = 2`, timeouts per state (`TIMEOUT_S`).
- Fake tests: `harness/tests/boot_state_machine.py` has 16 modes. `slotlate`, `cinematic`, `cinematicstuck` and `silentrestart` exist but are not named in the living spec.
- Real data, 426 summaries in `runs/` (2026-10-18): 413 `READY`, 5 `FAILED`, 8 without a boot entry. Boot seconds of READY runs: min 29, median 31, p95 52, max 105.5. `pause_calls`: 1 (368 runs) or 2 (45 runs).
- The test scenario `noop` checks the clock once for 3 s (`ctx.read_clock`). Nothing checks a longer still period or the boot history.
- A test scenario reads its run folder through `ctx.run` (`boot_path` is `boot.json`). `summary.json` holds `boot.seconds` and `boot.pause_calls`.

## Goals / Non-Goals

Goals: name the existing fake coverage in the spec; add one real-game test scenario and one suite that catch a boot timing regression.
Non-goals: see the proposal.

## Decisions

1. **One test scenario, `boot-timing`** (`harness/scenarios/boot_timing.py`, `LIMIT_S` about 90).
   - Read `boot.json` from `ctx.run.boot_path`. Check the history: the six save states, in order, each once, the last is `READY`.
   - Read boot seconds (`updated - started`) and the pause call count. The count comes from the same source as `summary.boot.pause_calls` (read in task 1.1).
   - Clock: `ctx.read_clock(wait_s=30)`. 30 s is well above the 8 s hold and the 2 to 4 s restart seen in the game.
   - Ranges: boot 20 to 120 s (data max 105.5); pause calls 1 to 3 (data 1 or 2; 3 allows one more restart); clock change 0 to 0.001.
2. **Suite `boot-timing`**: `{"scenario": "boot-timing", "repeat": 5}`, `flake_retries` 0, so a flaky boot shows as a failure. Pass: at least 4 of 5. Data shows about 1% boot failures, so 5 of 5 is likely, and 4 of 5 leaves room for one game hiccup.
3. **Domain map**: add `harness/scenarios/boot_timing.py` → `harness/game-boot` before the general `harness/scenarios/**` rule. Then the run report gives MTTF, MTTR and flaky rate for this domain.
4. **Spec scenarios only for the fake modes.** The tests exist and pass, so no fake code change is needed.

## Risks / Trade-offs

- The real ranges come from one PC. Another PC may boot slower. The upper bound (120 s) has room.
- A 30 s wait makes each run about 30 s longer.
- The test checks timing after the fact. It does not force the race conditions; the fake modes do that.

## Open Questions

- Where `pause_calls` is read from (`boot.json` or the launcher). Answer in task 1.1 by reading `harness/runlib/phases.py`. It only changes where the test scenario reads the number.
