# First reliability report

Run 2026-10-18 (tasks 3.1, 3.2). Full report: `docs/reliability/2026-10-18.md` and `.json`.

## Over a limit

- `harness/game-boot`: CFR 0.57 (n=7)
- `harness/agent-tools`: CFR 0.40 (n=5)
- `mod/unit_balance`: CFR 0.40 (n=5)

Near the limit, with high fix-to-feat ratios: `mod/invasion` (CFR 0.25, fix:feat 0.58), `mod/raid_behavior` (fix:feat 0.64), `harness/pak-mods` (0.50, n=4).

## Other findings

- Bug lifetimes are short (median 0.0 to 0.2 days in most domains). Bugs are found and fixed within hours. The history is only 9 days long, so long-lived bugs cannot show yet.
- Run report: 422 summaries. `harness/run-launcher` (all harness test scenarios): 22 real failures in 308 runs, MTTF 0.8 h, MTTR 0.0 h (n=13). MTTR near 0 means a failing test scenario is often rerun right away after a quick edit.
- Flaky failures: 0. 368 of 422 runs are on a dirty tree (`<sha>+dirty`), so "same commit" is weak evidence. The flaky count is a low estimate. Running suites from a clean tree would make it useful.
- `timeout` (1 run) is now a failure verdict in the config; `harness_error` (26) stays apart.

## Label review (task 3.2)

58 `fix` commits reviewed by subject. About 55 repair a real defect (crashes, wrong reads, races, wrong paths). About 3 are tuning or follow-up work labeled `fix` (for example `fix(unit_balance): pike reach band from measured ranges`, `allow 30 days for larger raids`).

Decision: the labels are good enough. No change for defect issues now.
