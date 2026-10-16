---
name: harness-ab-testing
description: Compare two variants over several runs (a pak, an environment setting, a tier) with small-sample statistics. Use for stochastic behavior such as combat, raids and balance, where one run proves nothing.
---

# A/B testing with the suite runner

The game is not deterministic. Judge a change over N runs per variant (at least 3, better 5 or more). Spec 10 U4 and `docs/harness/10-invasion-testability/implementation-notes/ab-statistics.md`.

## In the scenario
Record numbers with `ctx.metric("casualties_spear", value)`. They go to `runs/<id>/metrics.json`. A scenario may also record many numbers per run (for example per tier). Keep names short and stable.

## In the suite
A suite is `harness/suites/<name>.json`: `name`, `scenarios` (a list), `time_budget_s`, `flake_retries`. Each entry in `scenarios` has `scenario`, `repeat` and `variants`; a variant has a `name` and optional `paks` and `env`:
```json
{"scenario": "raid-tiers", "repeat": 4,
 "variants": [{"name": "size-100", "env": {"RAID_STANDIN_SIZE_PERCENT": "100"}},
              {"name": "size-150", "env": {"RAID_STANDIN_SIZE_PERCENT": "150"}}]}
```
Examples: `ab-example.json`, `raid-size-ab.json`, `counters-ab.json`, `pak-ab.json` (hidden scenario `pak-item-value`, a real pak A/B), `lord-village-ab.json`. Runs are interleaved (A, B, A, B) to cancel drift. An optional `expect` rule turns an A/B result into pass or fail (exit code 1).
```
uv run python harness\suite.py --suite raid-size-ab
```
Outputs: `runs/suite-<stamp>/report.json` (an `ab` section: the 8 metrics with the largest effect) and `report.md` (a table).

## What a variant can change
- A Python scenario cannot read `--env` values from `os.environ`: they go to the game process. Read them with `ctx.variant_option(name, default)`. Scenario `battlefield-anchor` is an example. (Run `20261015-123949-2a0a` was invalid for this reason.)
- `--env KEY=VALUE`: extra game environment variables. Names match `^[A-Z][A-Z0-9_]{0,63}$`. Reserved names are refused (`HARNESS_RUN_DIR`, `LOCALAPPDATA`, `PATH`, `UE4SS_BRIDGE*`, `HARNESS_AUTOBOOT`, `HARNESS_TEST_SAVE`, `HARNESS_TELEMETRY_INTERVAL_S`). Values of secret-looking names are masked. A mod reads the variable when it loads.
- `--pak NAME`: install a built pak (it needs `harness/pakmod.local.json`; in a worktree copy it from the main checkout) for the run, remove it after teardown (skill `harness-pak-mod`).

## Reading the verdict (`harness/suitelib/stats.py`, stdlib only)
n, min, median, max, mean, stdev, a 95% Wilson interval for pass rates, Cohen's d, range overlap, and a two-sided permutation test on the difference of means. Verdict: `different` needs p <= 0.1 and |d| >= 0.5. `same` needs p > 0.1 and |d| < 0.5. Fewer than 3 runs per variant is `inconclusive`. It is a heuristic for small samples. Say so when you report it, and give the numbers, not only the word.

## Cautions
- Add a control: run A against A first (`ab-example.json` is an A/A check) to see the noise.
- Equal distributions must give `same`. Test that your metric can show a difference at all.
- Every run costs 40 to 70 s and one count of the run cap.
- A killed run cannot remove its pak. `pakmod.py remove --all` does.
