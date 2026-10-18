# Design: add reliability metrics

## Context

- `harness/runlib/summary.py` already writes `git` (10 characters, `+dirty`) from `environment.harness_git`. The full SHA is in `config.json`.
- Test scenario files carry `COVERS` (criteria IDs of spec 10), not domains. Criteria are not capabilities, so the domain comes from the path.
- Commit scopes do not match capabilities (`runlib`, `boot`, `invasion`, `raid_behavior`). The domain comes from changed file paths, not from the scope.
- Old runs have no `domain` and often no full SHA.

## Goals / Non-Goals

Goals: per-domain numbers from data we already have; cheap to run; pure Python with no new package.
Non-goals: see the proposal.

## Decisions

1. **Domain from paths, one map for both reports.** `harness/reliability/domains.json` is an ordered list of `{"glob": ..., "domain": ...}`. First match wins. Feature folders map by rule. Reason: scopes are inconsistent; paths are not.
2. **Library plus thin tool.** `harness/reliabilitylib/` (`domains.py`, `gitlog.py`, `blame.py`, `runs.py`, `report.py`); `harness/tools/reliability.py` with sub-commands `git` and `runs`. Reason: small functions that tests can call without a CLI.
3. **Git through `subprocess`** (`git log --numstat --format=...`, `git blame --porcelain -L`). No GitPython. Reason: no new package.
4. **Change failure rate by time window, not by blame.** Simple and robust. Blame is used only for bug lifetime.
5. **Bug lifetime uses only removed and changed lines** of the fix, blamed on the fix's parent. The newest origin commit gives the lifetime (the bug cannot be older than the last edit of those lines in a simple model).
6. **Old runs.** The run report reads the domain from `summary.json` if present. Otherwise it computes it from the test scenario name through the map. The commit for flaky detection is `git_sha`, else `git`. Runs with no commit cannot be flaky; they count as real failures and are flagged `no_commit`.
7. **Tests build a temporary git repository** with fixed author dates (`GIT_AUTHOR_DATE`, `GIT_COMMITTER_DATE`) and fake run folders. No real game.

## Risks / Trade-offs

- Wrong `fix` labels inflate or hide defects. Mitigation: the report lists the fix commits per domain so a review can spot errors. If noise is high, we propose solution 2 (issues).
- Blame finds refactor commits as origin. Lifetime is an estimate; the report says so.
- Runs on `main` are irregular. MTTF depends on run frequency. The report shows run counts next to it.
- `unmapped` churn hides domains. The report shows its share so we can extend the map.

## Open Questions

- Which name gives the test scenario of a run: `summary.scenario` is a short name (`noop`). Does the run folder or `config.json` hold the scenario path? Answer during task 1.1 by reading `harness/runlib/runner.py` and `config.json` of a recent run. This does not change what is built, only where the path is read.
