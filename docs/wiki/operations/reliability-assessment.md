---
type: Guide
title: Reliability assessment
description: How the reliability-assessment skill measures regression risk per spec domain from git history and run results, and how the project uses the result.
tags: [process, reliability, metrics, git, runs, skills]
generated: { by: claude-code/claude-opus-5-5, at: 2026-10-18T22:00:00Z }
sources:
  - resource: repo://.claude/skills/reliability-assessment/
  - resource: repo://openspec/specs/process/reliability-assessment/spec.md
  - resource: repo://docs/reliability/
---
# Reliability assessment

The skill `reliability-assessment` gives numbers for the regression risk of each spec domain. The script is generic. Everything specific to this repo is in `.claude/skills/reliability-assessment/reliability.json`.

## Run it

```
uv run python .claude/skills/reliability-assessment/scripts/reliability.py assess
```

The report goes to `docs/reliability/<date>.md` and `.json`.

## Where the numbers come from

| Metric | Source | Meaning |
| --- | --- | --- |
| feat, fix, fix:feat, churn | `git log --numstat` | Work and repairs per domain |
| CFR (change failure rate) | `git blame` of each fix | Share of feats whose lines a fix changed within `cfr.window_days` |
| Bug lifetime | `git blame` of each fix | Days from the last edit of the fixed lines to the fix |
| MTTF, MTTR, flaky | `runs/*/summary.json` | Time between test scenario failures, time to repair, failures that pass on the same commit |

A file gets its domain from ordered glob rules in `reliability.json` (`domains`). A run gets its domain through the file of its test scenario (`runs.test_files`), because `summary.json` holds only the scenario name.

## Limits of the data

- Every test scenario in `harness/scenarios/` maps to `harness/run-launcher`.
- Most runs are on a dirty tree (`<sha>+dirty`), so the flaky count is a low estimate.
- Commit labels decide what a fix is. The JSON lists the fix commits of each domain for review.

## How the project uses it

The rules are in the living spec `process/reliability-assessment`: assess before a release, at the spec pull request of a feat change, and once a month. A domain over a limit gets a regression test scenario or a fix-only change next. A feat proposal has a `Reliability risk` section (`process/spec-workflow`).
