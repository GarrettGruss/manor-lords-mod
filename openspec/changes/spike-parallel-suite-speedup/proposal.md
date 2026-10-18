# Proposal: Spike parallel suite speedup

Issue: #151. Legacy source: `docs/harness/11-parallel-game-slots/README.md` (plan step 5 and the open acceptance boxes). Legacy issue: #151.

## Why
Steps 1 to 4 of spec 11 are built (slots, launcher slot support, parallel suite, `EXCLUSIVE` scenarios). The living spec `harness/game-slots` and `harness/regression-suite` describe them. Issue #151 still says that steps 3 and 4 are open. This is out of date.

Three things are not proven:
- The real A/B suite on 3 slots against the same suite on 1 slot. The `core` suite gained only about 15 percent, because the boot dominates short scenarios (`docs/harness/11-parallel-game-slots/implementation-notes/step4-parallel-suite.md`).
- An `EXCLUSIVE` scenario in a real parallel suite. Only pool tests cover it.
- With 3 games a bridge call can wait longer than the 15 s timeout. The run then ends with `harness_error`, which the suite does not retry.

## What Changes
- Run one long A/B suite (for example `raid-size-ab`) on 1 slot and on 3 slots. Compare wall time and result ranges.
- Run a parallel suite that holds one `EXCLUSIVE` scenario. Check that it runs alone.
- Decide how to handle a bridge timeout under load (see `design.md`).
- Check that no game file, key or slot folder is in git.
- Write the findings to `notes/`.

## Non-goals
- More than 3 slots.
- Changes to the slot design.
- Bug #158 (`test_install_scripts` fails while a game runs) and bug #160 (`suite.py` has no `--slot`): they are bug issues. See `design.md`.

## Legacy folders
`docs/harness/11-parallel-game-slots/` (read only).

## Capabilities
### New Capabilities
None.

### Modified Capabilities
None now. If the bridge timeout decision changes behavior, the implementation adds a requirement to `harness/regression-suite` or `harness/ue4ss-bridge`.

## Impact
Needs the real game and up to 3 slots. Runs take about 15 to 30 minutes. No code change is planned unless the timeout decision needs one.
