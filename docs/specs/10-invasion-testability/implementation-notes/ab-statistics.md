# A/B variants and statistics (U4)

Status: built and unit tested with a seeded stand-in. NOT verified on the real game (no real A/B suite was run).

## Why
Combat is not deterministic. One run per variant says little. A feature is judged over N runs per variant,
with a clear rule for "different", "same" or "not enough data".

## Design
- `run.py --pak <name>` (repeatable): preflight installs the built pak `<work_dir>/out/<name>_P.pak` into `~mods` with the shared code in
  `harness/runlib/paks.py` (the same code as `pakmod.py install`). The phase `paks-remove` has `always_run` and runs AFTER teardown, so the game no longer holds the file.
  It removes only files that the manifest lists and whose hash still matches. A foreign file with the same name is never replaced (install fails with a clear message) and never deleted.
  The work folder comes from `harness/pakmod.local.json` (`--pak-config` changes the file).
- `run.py --env KEY=VALUE` (repeatable): extra variables for the game process only. Name `^[A-Z][A-Z0-9_]{0,63}$`; names that start with `HARNESS_RUN_DIR`, `LOCALAPPDATA`, `PATH` or `UE4SS_BRIDGE`
  are refused, as are `HARNESS_AUTOBOOT`, `HARNESS_TEST_SAVE`, `HARNESS_TELEMETRY_INTERVAL_S`. The value is printable, has no newline, at most 256 characters. The harness values are set after the extra values, so they always win.
- Recording: `config.json` has `paks`, `env` (a value is `***` if the name contains KEY, TOKEN, SECRET or PASSWORD) and `environment.paks` (`name:sha256-prefix`) and `environment.env_keys`.
  `summary.environment` has `paks` and `env_keys` only (no values).
- Suite entry: `variants: [{name, paks, env}]`, `repeat` runs per variant, interleaved A, B, A, B so slow drift hits all variants alike. The first variant is the reference.
  No `variants` means one implicit variant `default`, and `run_one` is called with three arguments as before. With variants the `Variant` is a fourth argument.
- Metrics of a run: `duration_s`, the numeric values of `scenario_result.asserts` (by name), and `metrics.json` in the run folder (flat `{name: number}`, written by `ctx.metric(name, value)`). A `metrics.json` value wins over an assert of the same name.
  Only passing runs give values (the last attempt of a repeat).

## Rules (`harness/suitelib/stats.py`)
- Summary: n, min, median, max, mean, sample standard deviation.
- Pass rate: Wilson interval (95%).
- Effect size: Cohen's d with the pooled standard deviation, (mean B - mean A) / pooled sd. Zero spread: 0 for equal means, else +-99 (JSON has no infinity).
- Relative difference: (median B - median A) / |median A|. Undefined (null) if the median of A is 0 and the medians differ.
- Range overlap: do [min, max] of A and B share a point.
- p-value: two-sided permutation test on the difference of means. Exact over all splits when there are at most 20000; else 10000 random shuffles with the fixed seed 20261010 (p = (hits + 1) / (shuffles + 1)).
- Verdict, alpha = 0.1: fewer than 3 runs in a variant -> `inconclusive`. `different` if p <= alpha and |d| >= 0.5. `same` if p > alpha and |d| < 0.5. Otherwise `inconclusive`.
- `expect` of a suite entry (`metric`, `direction` lower or higher, `min_rel_diff`): met only if the verdict of every later variant is `different`, the median moved in the wanted direction and |rel diff| >= `min_rel_diff`.
  `inconclusive` or a missing metric is NOT met. A missed expectation gives exit code 1.

## Limits of the permutation test with small n
- It is a heuristic, not a proof. With 3 against 3 runs there are only 20 splits: the smallest possible two-sided p is 0.1, so alpha 0.1 is the lowest bar that can ever give `different` at n = 3.
- With n between 3 and 30 the test has little power: a real but moderate effect often ends as `inconclusive`. More runs per variant is the fix, not a looser alpha.
- It compares means, so one outlier (a crash-like run that still passes) can move the result. The range overlap flag and the medians in the report help to see this.
- The test assumes runs are independent and exchangeable. Interleaving covers slow drift, not a change in the machine during the suite.
- Many metrics are compared at once. With alpha 0.1, about one in ten unrelated metrics may show `different` by chance. The report shows the 8 strongest per variant and the note counts all.
- Pass rate intervals from few runs are wide. 5 of 5 passes has a lower bound of about 0.57.

## Report size
`report.json` of a passing suite without variants stays under 4 KB. With an `ab` section it stays under 8 KB (at most 8 metrics per compared variant; tested with 12 metrics and 10 runs).

## Not verified
A real A/B on the game (the example suite `ab-example` uses `env` only and the `smoke` scenario ignores the variable, so it is an A/A check), a real pak in a run, the cleanup after a real crash or a suite timeout kill
(a killed `run.py` cannot remove its pak; `pakmod.py remove --all` or `uninstall.ps1 -Remove` does, and the next run overwrites a pak that is in the manifest).
