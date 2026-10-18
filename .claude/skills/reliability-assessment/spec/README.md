# Spec: reliability-assessment skill

Status: built (2026-10-18). Issue: #289. OpenSpec change: `add-reliability-metrics`.

This spec belongs to the skill. The skill (`SKILL.md`), this spec, the script `scripts/reliability.py` and the tests `tests/` live together in `.claude/skills/reliability-assessment/`. The script imports nothing from the codebase it measures. To use it in another codebase, copy the folder and write a new `reliability.json`.

This spec names no rule of a codebase. When to assess and what to do with the results are rules of the codebase that uses the skill (here: the living spec `process/reliability-assessment`).

## Goal

Reliability metrics per domain (a capability, a module, any area of the code), from git history and from test run result files.

## Non-goals

- Defect tracking in an issue tracker.
- Dashboards.
- Exact values. Reports show sample counts.

## Requirements

Every requirement has a test in `tests/`. Words in `code` are config keys.

1. **Config.** The script reads one JSON file (`--config`, default `reliability.json` next to the skill). It has no built-in defaults. A missing key or a wrong type stops it with a message that names the key. Required: `domains`, `ignore`, `commit_types.{pattern, feat, fix}`, `cfr.window_days`, `low_sample_n`, `thresholds.{cfr, flaky, min_samples, unmapped_churn}`, `report_dir`. Optional: `capabilities_dir`, `runs`.
2. **Domain map.**
   - A path that matches a glob in `ignore` has no domain and adds no churn.
   - Globs in `domains` are tried in order. The first match wins. `**/` matches zero or more folders, `*` stays inside one folder, and `{x}` captures one folder name into the `domain` template.
   - No match gives `unmapped`.
   - When `capabilities_dir` is set: a domain without placeholders must have a folder there, or the script stops and names the pattern. A captured domain without a folder is kept and listed as an unknown domain. With `"require_capability": true` on a rule, it falls through to the next rule instead.
3. **Commits.** `commit_types.pattern` must have a group `type`. Types in `commit_types.feat` and `commit_types.fix` count. Merge commits are skipped. A commit counts once in each domain it touches.
4. **Origins of a fix.** The lines a fix removes or changes are blamed on the fix's parent commit. Each (domain of the file, blamed commit) pair is an origin.
5. **Change failure rate.** A feat commit fails in a domain when it is an origin of a fix in that domain, and the fix comes at most `cfr.window_days` days later. The rate is failed feats divided by feats.
   - Example: window 14, a fix changes a line that a feat wrote 5 days before → the feat failed. 20 days → it did not.
6. **Bug lifetime.** Per fix and domain: from the newest origin to the fix. A fix with no origin in a domain (it only adds lines) counts in `no_origin`.
   - Example: a line written 3 days before the fix → between 2.9 and 3.1 days.
7. **Git report.** Per domain: feat, fix, fix-to-feat ratio, churn, change failure rate, median bug lifetime, `no_origin`, the list of fix commits (for a label review). Also the `unmapped` churn share and the unknown domains.
8. **Run report.** Only when `runs` is set.
   - Files from `runs.glob`, sorted by `runs.fields.time` (ISO 8601 or epoch seconds). Each file is one run of the test `runs.fields.test`.
   - Verdicts (`runs.fields.verdict`) in `runs.pass` pass, in `runs.fail` fail. Others are counted apart and do not change the timeline.
   - An unreadable file is listed and skipped.
   - The domain of a test: the files in `runs.test_files.globs` are read. `runs.test_files.name_pattern` (group 1) gives the test name, or the file name with `runs.test_files.stem_replace` applied. The file path goes through the domain map. A test with no file is `unmapped`.
9. **Flaky.** A failure is flaky when the next counted run of the same test passes on the same `runs.fields.commit`. A run without a commit is never flaky. Flaky failures do not count in MTTF or MTTR.
10. **MTTF and MTTR.** Flaky failures and other verdicts are removed. MTTF is the median time from the first pass of a pass streak to the next failure. MTTR is the median time from the first failure of a failure streak to the next pass. Both in hours.
    - Example: pass at hour 0, fail at hour 10, pass at hour 14 → MTTF 10 h, MTTR 4 h (±0.1 h).
11. **Sample sizes.** Every ratio, rate and median shows its sample count. Below `low_sample_n` it is marked `low sample`.
12. **Assess.** Runs both reports and writes `<report_dir>/<date>.md` and `<date>.json` (atomic writes). It lists:
    - each domain with a change failure rate over `thresholds.cfr` and at least `thresholds.min_samples` feats
    - each domain with a flaky rate (flaky failures / counted runs) over `thresholds.flaky` and at least `thresholds.min_samples` runs
    - an `unmapped` churn share over `thresholds.unmapped_churn`
13. **Portability.** The script works for another layout and commit style with only a different config.

## Commands

```
uv run python .claude/skills/reliability-assessment/scripts/reliability.py git|runs|assess [--config FILE] [--repo DIR] [--rev REV] [--json FILE] [--date YYYY-MM-DD]
uv run python -m unittest discover -s .claude/skills/reliability-assessment/tests
```

Exit code 2 means a config error.
