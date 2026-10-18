# Design: add reliability metrics

## Context

- Run results: `runs/<id>/summary.json` has `verdict`, `started`, `scenario` (short name) and `git` (10 characters, `+dirty`). The full SHA is in `config.json` (`harness_git`).
- Test scenario files carry `COVERS` (criteria IDs), not domains. The domain comes from the path.
- Commit scopes do not match capabilities (`runlib`, `boot`, `invasion`). The domain comes from changed file paths.
- Precedent: `.claude/skills/repo-wiki/` keeps its spec, script and tests in the skill folder.

## Goals / Non-Goals

Goals: a skill that works in any git repository with a config file; numbers from data we already have; no new package.
Non-goals: see the proposal.

## Decisions

1. **Two specs with different owners.** The skill spec (`.claude/skills/reliability-assessment/spec/README.md`) describes the script and the config. It names no repo rule, so the skill can be copied. The OpenSpec capability `process/reliability-assessment` holds this repo's rules for using the results.
2. **One config file, no built-in defaults.** Every constant comes from `reliability.json`. A missing key stops the script with a clear message. Reason: the specs name config keys, so values can change without a spec change.
3. **Domains from ordered globs.** First match wins. `{name}` captures a path part into the domain name.
4. **Git through `subprocess`** (`git log --numstat`, `git blame --porcelain`). No GitPython. No import from `harness/`.
5. **Change failure rate by time window; blame only for bug lifetime.**
6. **Run format from config.** `runs.fields` names the JSON keys. Here `commit` reads the short `git` value, which is enough to find flaky failures (same commit, next run).
7. **Tests use a temporary git repository** with fixed dates and fake run folders.

## Config for this repo (start values)

```json
{
  "domains": [
    {"glob": "mod/InvasionMod/Scripts/features/{name}/**", "domain": "mod/{name}"},
    {"glob": "mod/InvasionMod/scenarios/{name}/**", "domain": "mod/{name}"},
    {"glob": "harness/runlib/**", "domain": "harness/run-launcher"}
  ],
  "commit_types": {"pattern": "^(?P<type>\\w+)(\\([^)]*\\))?!?:", "feat": ["feat"], "fix": ["fix"]},
  "capabilities_dir": "openspec/specs",
  "runs": {
    "glob": "runs/*/summary.json",
    "fields": {"time": "started", "test": "scenario", "verdict": "verdict", "commit": "git"},
    "pass": ["pass"], "fail": ["fail", "crash"]
  },
  "cfr": {"window_days": 14},
  "low_sample_n": 3,
  "thresholds": {"cfr": 0.3, "flaky": 0.2, "min_samples": 5, "unmapped_churn": 0.15},
  "report_dir": "docs/reliability"
}
```

The full `domains` list is written in task 2.

## Skill spec (draft for `spec/README.md`)

Each requirement gets a test in `tests/`. Values in brackets are config keys.

1. **Config.** The script reads one JSON file (`--config`, default `reliability.json` next to the skill). A missing key or a wrong type stops it with a message that names the key.
2. **Domain map.** Globs in `domains` are tried in order. The first match wins. `{name}` fills the domain. No match gives `unmapped`. When `capabilities_dir` is set, each domain must have a folder there, or the script stops and names the pattern.
3. **Commit types.** `commit_types.pattern` finds the type. Types in `commit_types.feat` and `commit_types.fix` count. Merge commits are skipped. A commit counts once in each domain it touches.
4. **Git report.** Per domain: feat count, fix count, fix-to-feat ratio, churn, change failure rate, median bug lifetime, `no_origin` count, and the `unmapped` churn share.
5. **Change failure rate.** The share of feat commits followed by a fix in the same domain within `cfr.window_days`.
   - Example: window 14, fix 5 days after a feat → counts; fix 20 days after → does not.
6. **Bug lifetime.** Blame the lines a fix removes or changes on the parent commit. The newest origin commit gives the start. A fix that only adds lines counts in `no_origin`.
   - Example: a line written 3 days before the fix → lifetime between 2.9 and 3.1 days.
7. **Run report.** Only when `runs` is set. Files from `runs.glob`, sorted by `runs.fields.time`, grouped by `runs.fields.test` and domain. `runs.pass` and `runs.fail` sort verdicts. Other verdicts are counted apart. An unreadable file is listed and skipped.
8. **Flaky.** A failure is flaky when the next run of the same test on the same commit passes. Flaky failures do not count in MTTF or MTTR.
9. **MTTF and MTTR.** Medians: pass to next real failure; real failure to next pass.
   - Example: pass at hour 0, fail at hour 10, pass at hour 14 → MTTF 10 h, MTTR 4 h (ranges ±0.1 h).
10. **Sample sizes.** Each value shows its count. Below `low_sample_n` it is marked `low sample`.
11. **Assess.** Runs both reports, writes `<report_dir>/YYYY-MM-DD.md` and `.json`, and lists each domain over `thresholds.cfr` or `thresholds.flaky` with at least `thresholds.min_samples` samples, and an `unmapped` share over `thresholds.unmapped_churn`.

## Risks / Trade-offs

- Wrong `fix` labels distort counts. The report lists fix commits per domain for review. A process rule says when to switch to issues.
- Blame finds refactors as origins. Lifetime is an estimate.
- Irregular runs distort MTTF. Run counts appear next to it.
- Two specs can drift. The skill spec names no repo rule; the process spec names only config keys.

## Open Questions

- Where a run stores its test scenario path (`summary.scenario` is a short name). The domain lookup needs a path. Answer in task 1.1 by reading `harness/runlib/runner.py` and a recent `config.json`. If no path exists, `runs` gets a `test_domains` map from test name to domain in the config.
